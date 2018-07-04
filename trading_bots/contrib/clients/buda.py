from trading_api_wrappers import Buda

from . import *


class BudaBase(BaseClient):
    name = 'Buda'

    def __init__(self, client=None, dry_run: bool=False, timeout: int=None, logger=None, store=None, host: str=None):
        self.host = host
        super().__init__(client, dry_run, timeout, logger, store)


class BudaPublic(BudaBase):

    def _client(self):
        return Buda.Public(self.timeout, host=self.host, logger=self.log, store=self.store)


class BudaAuth(BudaBase):

    def _client(self):
        key = self.credentials['key']
        secret = self.credentials['secret']
        return Buda.Auth(key, secret, timeout=self.timeout, host=self.host, logger=self.log, store=self.store)


class BudaMarket(MarketClient, BudaPublic):

    def _market_id(self):
        return f'{self.market.base}-{self.market.quote}'.lower()

    def _ticker(self):
        return self.client.ticker(self.market_id)

    def _order_book(self, side: Side=None):
        order_book = self.client.order_book(self.market_id)
        if side:
            return order_book.bids if side == Side.BUY else order_book.asks
        return order_book


class BudaWallet(WalletClient, BudaAuth):

    def _balance(self, currency, available_only=False):
        balance = self.client.balance(currency)
        if available_only:
            return balance.available_amount.amount
        return balance.amount.amount - balance.pending_withdraw_amount.amount

    @staticmethod
    def _filter_state(items, state: str=None):
        if state:
            items = [i for i in items if i.state == state]
        return items

    def _deposits(self, currency: str):
        return self.client.deposits(currency)

    def _withdrawals(self, currency: str):
        return self.client.withdrawals(currency)

    def _withdraw(self, currency: str, amount: float, address: str, subtract_fee: bool=False):
        if self.dry_run:
            return self.client.simulate_withdrawal(currency, amount, amount_includes_fee=subtract_fee)
        return self.client.withdrawal(currency, amount, address, amount_includes_fee=subtract_fee)

    def _withdrawal_details_msg(self, msg: str, withdrawal):
        # Limit is null on a market order
        msg += ('ID: {w.id} | '
                'Amount: {w.amount.amount:,f} | '
                'Fee: {w.fee.amount:,f} | '
                'Address: {w.data.address} | '
                'State: {w.state}')
        return msg.format(w=withdrawal)


class BudaTrading(TradingClient, BudaAuth, BudaMarket):
    wallet_client = BudaWallet
    side_mapping = {
        Side.BUY: Buda.OrderType.BID,
        Side.SELL: Buda.OrderType.ASK,
    }
    min_order_amount_mapping = {
        'BCH': 0.0001,
        'BTC': 0.0001,
        'ETH': 0.001,
        'LTC': 0.00001,
    }

    def _open_orders(self):
        return self.client.order_pages(self.market_id, state=Buda.OrderState.PENDING).orders

    def _order_amount(self, order):
        return order.amount.amount

    def _cancel_order(self, order):
        return self.client.cancel_order(order.id)

    def _order_details(self, order_id: int):
        return self.client.order_details(order_id=order_id)

    def _place_order(self, side: Side, o_type: OrderType, amount: float, price: float=None):
        side = self.side_mapping[side].value
        return self.client.new_order(self.market_id, side, o_type.value, amount, price)

    def _place_order_msg(self, side: Side, order_type: OrderType=None):
        return f'{side.value.title()} {order_type.value.title()}'

    def _order_details_msg(self, msg: str, order):
        # Limit is null on a market order
        price_type = Buda.OrderPriceType.LIMIT.value
        limit = order.limit.amount if order.price_type == price_type else 0
        msg += ('ID: {o.id} | '
                'Type: {o.type} | '
                'Limit: {limit:,f} | '
                'Amount: {o.amount.amount:,f} | '
                'State: {o.state}')
        return msg.format(o=order, limit=limit)

    def _open_positions(self):
        raise NotImplementedError

    def _open_position(self, side: Side, p_type: OrderType, amount: float, price: float=None, leverage: float=None):
        raise NotImplementedError
