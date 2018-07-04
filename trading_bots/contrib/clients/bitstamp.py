from trading_api_wrappers import Bitstamp

from trading_bots.utils import truncate
from . import *


class BitstampPublic(BaseClient):
    name = 'Bitstamp'

    def _client(self):
        return Bitstamp.Public(timeout=self.timeout, logger=self.log, store=self.store)


class BitstampAuth(BaseClient):
    name = 'Bitstamp'

    def _client(self):
        key = self.credentials['key']
        secret = self.credentials['secret']
        customer_id = self.credentials['customer_id']
        return Bitstamp.Auth(key, secret, customer_id, timeout=self.timeout, logger=self.log, store=self.store)


class BitstampMarket(MarketClient, BitstampPublic):

    def _market_id(self):
        return str(self.market).lower()

    def _ticker(self):
        return self.client.ticker(self.market_id)

    def _order_book(self, side: Side=None):
        order_book = self.client.order_book(self.market_id)
        bids, asks = order_book['bids'], order_book['asks']
        if side:
            return bids if side == Side.BUY else asks
        return OrderBook(bids=bids, asks=asks)

    def _order_book_entry_amount(self, order):
        return float(order[1])

    def _order_book_entry_price(self, order):
        return float(order[0])


class BitstampWallet(WalletClient, BitstampAuth):

    def _balance(self, currency, available_only=False):
        balances = self.client.account_balance()
        key = 'available' if available_only else 'balance'
        balance = balances[f'{currency.lower()}_{key}']
        return float(balance)

    def _deposits(self, currency: str):
        tx_type = '0'  # '0': deposit; '1': withdrawal; '2': market trade; '14': sub account transfer.
        limit = 1000  # max limit: 1000
        deposits = [d for d in self.client.user_transactions(limit=limit) if d['type'] == tx_type]
        return deposits

    def _withdrawals(self, currency: str):
        time_delta = 50000000  # max delta: 50000000 (seconds)
        withdrawals = self.client.withdrawal_requests(time_delta)
        return [w for w in withdrawals if w['currency'] == currency.upper()]

    def _withdraw(self, currency: str, amount: float, address: str, subtract_fee: bool=False):
        withdrawal_method = {
            'BCH': self.client.bch_withdrawal,
            'BTC': self.client.bitcoin_withdrawal,
            'ETH': self.client.eth_withdrawal,
            'LTC': self.client.litecoin_withdrawal,
            # 'XRP': self.client.xrp_withdrawal,
        }
        # TODO: subtract_fee
        if subtract_fee:
            self.log.warning('subtract_fee option is not implemented!')
        method = withdrawal_method[currency.upper()]
        return method(address, amount)


class BitstampTrading(TradingClient, BitstampAuth, BitstampMarket):
    wallet_client = BitstampWallet
    min_order_amount_mapping = {
        'BCH': 0.005,
        'BTC': 0.001,
        'ETH': 0.01,
        'LTC': 0.05,
    }

    def _open_orders(self):
        return self.client.open_orders(self.market_id)

    def _order_amount(self, order):
        return float(order['amount'])

    def _cancel_order(self, order):
        return self.client.cancel_order(order['id'])

    def _order_details(self, order_id: int):
        return self.client.orders_status(order_id)

    def _place_order(self, side: Side, o_type: OrderType, amount: float, price: float=None):
        methods = {
            OrderType.MARKET: {
                Side.BUY: self.client.buy_market_order,
                Side.SELL: self.client.sell_market_order,
            },
            OrderType.LIMIT: {
                Side.BUY: self.client.buy_limit_order,
                Side.SELL: self.client.sell_limit_order,
            }
        }
        place_order = methods[o_type][side]
        amount = truncate(amount, 8)
        args = (amount, price) if o_type == OrderType.LIMIT else (amount,)
        return place_order(self.market_id, *args)

    def _open_positions(self):
        return []

    def _open_position(self, side: Side, p_type: OrderType, amount: float, price: float=None, leverage: float=None):
        raise NotImplementedError
