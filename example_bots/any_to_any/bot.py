from datetime import datetime
from time import sleep

from trading_bots.bots import Bot
from trading_bots.contrib.clients import Market, Side
from trading_bots.contrib.clients import buda
from trading_bots.utils import truncate_to


class AnyToAny(Bot):
    name = 'AnyToAny'

    def _setup(self, config):
        # Get configs
        self.from_currency = config['from_currency']
        self.from_address = config['from']['address']
        self.to_currency = config['to_currency']
        self.to_withdraw = config['to']['withdraw']
        self.to_address = config['to']['address']
        # Set market
        self.market = self._get_market(self.from_currency, self.to_currency)
        # Set side
        self.side = Side.SELL if self.market.base == self.from_currency else Side.BUY
        # Set buda trading client
        self.buda = buda.BudaTrading(
            self.market, dry_run=self.dry_run, timeout=self.timeout, logger=self.log, store=self.store)
        # Get deposits
        self.deposits = self.store.get(self.from_currency + '_deposits') or {}
        # Set start date
        self.start_date = datetime.utcnow()

    def _strategy(self):
        # Get new deposits
        self.log.info(f'Checking for new {self.from_currency} deposits')
        self.update_deposits()
        # Convert pending amounts
        self.log.info('Converting pending amounts')
        self.process_conversions()
        # Get available balances
        self.log.info('Processing pending withdrawals')
        self.process_withdrawals()

    def _abort(self):
        pass

    def update_deposits(self):
        # Get deposits
        deposits = self.deposits
        # Set wallet from relevant currency according to side
        from_wallet = self.buda.wallets.quote if self.side == Side.BUY else self.buda.wallets.base
        # Get and filter deposits
        new_deposits = from_wallet.get_deposits()
        if self.from_address != 'Any':
            new_deposits = [deposit for deposit in new_deposits if deposit.data.address == self.from_address]
        new_deposits = [deposit for deposit in new_deposits if deposit.created_at >= self.start_date]
        # Update states on existing keys and add new keys with base structure
        for deposit in new_deposits:
            idx = str(deposit.id)
            if idx in deposits.keys():
                if deposit.state != deposits[idx]['state']:
                    deposits[idx]['state'] = deposit.state
            else:
                deposits[idx] = {
                    'state': deposit.state,
                    'amounts': {'original_amount': deposit.amount.amount,
                                'converted_amount': 0,
                                'converted_value': 0},
                    'orders': [],
                    'pending_withdrawal': self.to_withdraw
                    }
            self.store.store(self.from_currency + '_deposits', deposits)
            self.deposits = deposits

    def process_conversions(self):
        # Get deposits
        deposits = self.deposits
        for deposit_id in deposits:
            # Calculate remaining amount to convert
            original_amount = deposits[deposit_id]['amounts']['original_amount']
            converted_amount = deposits[deposit_id]['amounts']['converted_amount']
            converted_value = deposits[deposit_id]['amounts']['converted_value']
            remaining = original_amount - converted_amount
            if deposits[deposit_id]['state'] == 'confirmed' and remaining > 0:
                if self.side == Side.BUY:  # Change amount to base currency for order creation purposes
                    remaining = self.buda.client.quotation_market(self.market.base + '-' + self.market.quote,
                                                                  'bid_given_spent_quote',
                                                                  remaining).order_amount.amount
                remaining = truncate_to(remaining, self.market.base)
                # Convert remaining amount using market order
                order = self.buda.place_market_order(self.side, remaining)
                # Wait for traded state to set updated values
                if order:
                    self.log.info(f'{self.side} market order placed, waiting for traded state')
                    while order.state != 'traded':
                        order = self.buda.client.order_details(order.id)
                        sleep(1)
                    self.log.info(f'{self.side} order traded, updating store values')
                    converted_amount += order.total_exchanged.amount if self.side == Side.BUY\
                                                                and order.state == 'traded'\
                                                                else order.traded_amount.amount
                    converted_value += order.traded_amount.amount if self.side == Side.BUY\
                                                                and order.state == 'traded'\
                                                                else order.total_exchanged.amount
                    converted_value -= order.paid_fee.amount  # Fee deducted so it wont interfere with withdrawal
                    deposits[deposit_id]['orders'].append(order.id)  # Save related orders for debugging
                # Save new values
                deposits[deposit_id]['amounts']['converted_amount'] = converted_amount
                deposits[deposit_id]['amounts']['converted_value'] = converted_value
                self.store.store(self.from_currency + '_deposits', deposits)
                self.deposits = deposits

    def process_withdrawals(self):
        # Get deposits
        deposits = self.deposits
        # Set wallet from relevant currency according to side
        to_wallet = self.buda.wallets.base if self.side == Side.BUY else self.buda.wallets.quote
        for deposit_id in deposits:
            # Filter deposits already converted and pending withdrawal
            if deposits[deposit_id]['state'] == 'confirmed' \
                    and deposits[deposit_id]['pending_withdrawal'] \
                    and deposits[deposit_id]['amounts']['original_amount'] == deposits[deposit_id]['amounts']['converted_amount']:
                withdrawal_amount = deposits[deposit_id]['amounts']['converted_value']
                withdrawal_amount = truncate_to(withdrawal_amount, self.to_currency)
                available = to_wallet.get_available()
                if withdrawal_amount <= available:  # We cannot withdraw more than available balance
                    w = to_wallet.request_withdrawal(withdrawal_amount, self.to_address, subtract_fee=True)
                    if w.state == 'pending_preparation':  # Check state to set and store updated values
                        self.log.info(f'{self.to_currency} withdrawal request received, updating store values')
                        deposits[deposit_id]['pending_withdrawal'] = False
                        self.store.store(self.from_currency + '_deposits', deposits)
                        self.deposits = deposits
                    else:
                        self.log.warning('Withdrawal failed')
                else:
                    self.log.warning(f'Available balance not enough for withdrawal amount {amount} {self.to_currency}')

    def _get_market(self, from_currency, to_currency):
        public_client = buda.BudaPublic()
        buda_markets = public_client.client.markets()
        bases = [market.base_currency for market in buda_markets]
        quotes = [market.quote_currency for market in buda_markets]

        if from_currency in bases and to_currency in quotes:
            market = Market((from_currency, to_currency))
        elif from_currency in quotes and to_currency in bases:
            market = Market((to_currency, from_currency))
        else:
            raise NotImplementedError(f'No compatible market found!')
        return market
