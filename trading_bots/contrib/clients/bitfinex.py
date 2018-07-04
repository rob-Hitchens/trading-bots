from trading_api_wrappers import Bitfinex

from . import *

DEFAULT_WALLET_TYPE = 'exchange'


class BitfinexPublic(BaseClient):
    name = 'Bitfinex'

    def _client(self):
        return Bitfinex.Public(timeout=self.timeout, logger=self.log, store=self.store)


class BitfinexAuth(BaseClient):
    name = 'Bitfinex'

    def _client(self):
        key = self.credentials['key']
        secret = self.credentials['secret']
        return Bitfinex.Auth(key, secret, timeout=self.timeout, logger=self.log, store=self.store)


class BitfinexMarket(MarketClient, BitfinexPublic):

    def _ticker(self):
        return self.client.ticker(symbol=self.market_id)

    def _order_book(self, side: Side=None):
        order_book = self.client.order_book(symbol=self.market_id)
        bids, asks = order_book['bids'], order_book['asks']
        if side:
            return bids if side == Side.BUY else asks
        return OrderBook(bids=bids, asks=asks)

    def _order_book_entry_amount(self, order):
        return float(order['amount'])

    def _order_book_entry_price(self, order):
        return float(order['price'])


class BitfinexWallet(WalletClient, BitfinexAuth):
    withdrawal_fees = {
        'BCH': 0.0005,
        'BTC': 0.0005,
        'ETH': 0.01,
        'LTC': 0.01,
    }
    method_mapping = {
        'BCH': 'bcash',
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'LTC': 'litecoin',
    }

    def __init__(self, currency: str, client=None, dry_run: bool=False, timeout: int=None, logger=None,
                 wallet_type: str=DEFAULT_WALLET_TYPE):
        super().__init__(currency, client, dry_run, timeout, logger)
        self.wallet_type = wallet_type

    def _balance(self, currency, available_only=False):
        balances = self.client.balances()
        currency = currency.lower()
        balance = next(b for b in balances if b['currency'] == currency
                       and b['type'] == self.wallet_type)
        if available_only:
            return float(balance['available'])
        return float(balance['amount'])

    @staticmethod
    def _filter_state(items, state: str=None):
        if state:
            items = [i for i in items if i['status'] == state]
        return items

    def _deposits(self, currency: str):
        deposits = self.client.movements(currency)
        return [d for d in deposits if d['type'] == 'DEPOSIT']

    def _withdrawals(self, currency: str):
        withdrawals = self.client.movements(currency)
        return [w for w in withdrawals if w['type'] == 'WITHDRAWAL']

    def _withdraw(self, currency: str, amount: float, address: str, subtract_fee: bool=False):
        method = self.method_mapping[currency]
        if subtract_fee:
            fee = self.withdrawal_fees[currency]
            amount -= fee
        return self.client.withdraw(method, 'exchange', amount, address)


class BitfinexTrading(TradingClient, BitfinexAuth, BitfinexMarket):
    wallet_client = BitfinexWallet
    has_margin_trading = True
    min_order_amount_mapping = {
        'BCH': 0.02,
        'BTC': 0.002,
        'ETH': 0.04,
        'LTC': 0.02,
    }
    order_type_mapping = {
        OrderType.MARKET: 'exchange market',
        OrderType.LIMIT: 'exchange limit',
    }

    def _open_orders(self):
        orders = self.client.active_orders()
        return [o for o in orders if o['is_live'] is True]

    def _order_amount(self, order):
        return order['remaining_amount']

    def _cancel_order(self, order):
        return self.client.delete_order(order['id'])

    def _order_details(self, order_id: int):
        return self.client.status_order(order_id)

    def _open_positions(self):
        positions = self.client.active_positions()
        return [p for p in positions if p['symbol'] == self.market_id and p['status'] in ['ACTIVE']]

    @staticmethod
    def _order_price(order_type: OrderType, price: float):
        return price if order_type == OrderType.LIMIT else 1  # Bitfinex API doc: 'Use random number for market orders'

    def _place_order(self, side: Side, o_type: OrderType, amount: float, price: float=None):
        price = self._order_price(o_type, price)
        order_type = self.order_type_mapping[o_type]
        return self.client.place_order(amount, price, side.value, order_type, self.market_id)

    def _open_position(self, side: Side, p_type: OrderType, amount: float, price: float=None, leverage: float=None):
        price = self._order_price(p_type, price)
        return self.client.place_order(amount, price, side.value, p_type.value, self.market_id)
