from trading_api_wrappers import Kraken

from . import *


class KrakenPublic(BaseClient):
    name = 'Kraken'

    def _client(self):
        return Kraken.Public(timeout=self.timeout, logger=self.log, store=self.store)


class KrakenAuth(BaseClient):
    name = 'Kraken'

    def _client(self):
        key = self.credentials['key']
        secret = self.credentials['secret']
        return Kraken.Auth(key, secret, timeout=self.timeout, logger=self.log, store=self.store)


class KrakenMarket(MarketClient, KrakenPublic):

    def _market_id(self):
        return str(self.market).replace('BTC', 'XBT')

    def _ticker(self):
        result = self.client.ticker(symbol=self.market_id)['result']
        # Get result first key
        return result[next(iter(result))]

    def _order_book(self, side: Side=None):
        result = self.client.order_book(symbol=self.market_id)['result']
        # Get result first key
        order_book = result[next(iter(result))]
        bids, asks = order_book['bids'], order_book['asks']
        if side:
            return bids if side == Side.BUY else asks
        return OrderBook(bids=bids, asks=asks)

    def _order_book_entry_amount(self, order):
        return float(order[1])

    def _order_book_entry_price(self, order):
        return float(order[0])


class KrakenWallet(WalletClient, KrakenAuth):
    withdrawal_fees = {
        'BCH': 0.0005,
        'BTC': 0.0005,
        'ETH': 0.01,
        'LTC': 0.01,
    }

    def _balance(self, currency, available_only=False):
        # TODO: How to get available_only?
        if available_only:
            self.log.warning('available_only option is not implemented!')
        asset = currency.replace('BTC', 'XXBT').replace('ETH', 'XETH').replace('XLM', 'XXLM').replace('USD', 'ZUSD')
        balance = self.client.balance()
        return float(balance['result'][asset])

    @staticmethod
    def _filter_state(items, state: str=None):
        if state:
            items = [i for i in items if i['status'] == state]
        return items

    def _deposits(self, currency: str):
        mapping = {
            'BCH': ('BCH', 'Bitcoin Cash'),
            'BTC': ('XBT', 'Bitcoin'),
            'ETH': ('XETH', 'Ether (Hex)'),
            'LTC': ('LTC', 'Litecoin'),
        }
        asset, method = mapping[currency]
        return self.client.deposit_status(asset, method)['result']

    def _withdrawals(self, currency: str):
        mapping = {
            'BCH': ('BCH', 'Bitcoin Cash'),
            'BTC': ('XBT', 'Bitcoin'),
            'ETH': ('XETH', 'Ether'),
            'LTC': ('LTC', 'Litecoin'),
        }
        asset, method = mapping[currency]
        return self.client.withdraw_status(asset, method)['result']

    def _withdraw(self, currency: str, amount: float, address: str, subtract_fee: bool=False):
        asset = currency.replace('BTC', 'XBT').replace('ETH', 'XETH')
        return self.client.withdraw(asset, amount, address)


class KrakenTrading(TradingClient, KrakenAuth, KrakenMarket):
    wallet_client = KrakenWallet
    has_margin_trading = True
    min_order_amount_mapping = {
        'BCH': 0.002,
        'BTC': 0.002,
        'ETH': 0.02,
        'LTC': 0.002,
    }

    def _open_orders(self):
        return self.client.open_orders()['result']['open'].values()

    def _order_amount(self, order):
        return order['remaining_amount']

    def _cancel_order(self, order):
        return self.client.cancel_order(order['id'])

    def _order_details(self, order_id: int):
        return self.client.query_orders([order_id])['result'][order_id]

    def _place_order(self, side: Side, o_type: OrderType, amount: float, price: float=None):
        return self.client.add_order(self.market_id, side.value, o_type.value, amount, price)

    def _position_amount(self, position):
        return float(position['vol'])

    def _open_positions(self):
        positions = self.client.open_positions()['result'].values()
        return [p for p in positions if p['pair'] == self.market_id and p['posstatus'] == 'open']

    def _open_position(self, side: Side, p_type: OrderType, amount: float, price: float=None, leverage: float=None):
        return self.client.add_order(self.market_id, side.value, p_type.value, amount, price, leverage=leverage)
