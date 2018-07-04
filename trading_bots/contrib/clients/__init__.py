from collections import namedtuple
from enum import Enum
from logging import Logger

from cached_property import cached_property

from trading_bots.conf import settings
from trading_bots.core.logging import get_logger
from trading_bots.core.storage import get_store

__all__ = [
    'Market',
    'Side',
    'OrderBook',
    'OrderType',
    'BaseClient',
    'BaseCurrencyClient',
    'BaseMarketClient',
    'MarketClient',
    'WalletClient',
    'TradingClient',
]


class Market(object):

    def __init__(self, code: (str, list, tuple)):
        assert isinstance(code, (str, list, tuple))
        if isinstance(code, (list, tuple)):
            assert len(code) == 2, 'A market code must have 2 items (base and quote currency).'
            base, quote = code
            self.base, self.quote = str(base), str(quote)
        if isinstance(code, str):
            assert len(code) == 6, 'A market code must have 6 characters (base and quote currency).'
            self.base, self.quote = code[:3], code[3:]
        self.code = self.base + self.quote

    def __str__(self):
        return self.code

    def __eq__(self, other):
        if isinstance(other, Market):
            other = other.code
        return self.code == other


OrderBook = namedtuple('order_book', 'bids asks')


class OrderBookEmptyError(Exception):
    pass


class Side(Enum):
    BUY = 'buy'
    SELL = 'sell'


class OrderType(Enum):
    MARKET = 'market'
    LIMIT = 'limit'


class BaseClient(object):
    name = ''

    def __init__(self, client=None, dry_run: bool=False, timeout: int=None,
                 logger: Logger=None, store=None, **kwargs):
        assert self.name, 'A name must be defined for the client!'
        self.credentials = settings.credentials.get(self.name)
        self.dry_run = dry_run
        self.timeout = timeout
        self.log = logger or get_logger(__name__)
        self.store = store or get_store(self.log)
        self.client = client or self._client()

    def _client(self):
        raise NotImplementedError


class BaseCurrencyClient(BaseClient):

    def __init__(self, currency: str, client=None, dry_run: bool=False, timeout: int=None,
                 logger: Logger=None, store=None, **kwargs):
        super().__init__(client, dry_run, timeout, logger, store, **kwargs)
        self.currency = currency


class BaseMarketClient(BaseClient):

    def __init__(self, market: (str, Market), client=None, dry_run: bool=False, timeout: int=None,
                 logger: Logger=None, store=None, **kwargs):
        super().__init__(client, dry_run, timeout, logger, store, **kwargs)
        if not isinstance(market, Market):
            market = Market(market)
        self.market = market
        self.market_id = self._market_id()

    def _market_id(self):
        return str(self.market)


class WalletClient(BaseCurrencyClient):
    withdrawal_fees = {}

    # Balance
    def _balance(self, currency: str, available_only: bool=False):
        raise NotImplementedError

    def _get_balance(self, currency: str, available_only: bool=False):
        b_type = 'balance' if available_only else 'available amount'
        self.log.debug(f'Obtaining {currency} {b_type} from {self.name}')
        try:
            amount = self._balance(currency, available_only)
            self.log.debug(f'{self.name} {b_type}: {amount} {currency}')
        except Exception:
            self.log.error(f'Failed obtaining {b_type} from {self.name} {currency}')
            raise
        return amount

    def get_balance(self):
        return self._get_balance(self.currency)

    def get_available(self):
        return self._get_balance(self.currency, available_only=True)

    # Deposits
    def _deposits(self, currency: str):
        raise NotImplementedError

    def _get_deposits(self, currency: str):
        self.log.debug(f'Obtaining deposits from {self.name}')
        try:
            deposits = self._deposits(currency)
            self.log.debug(f'Total number of deposits: {len(deposits)}')
        except Exception:
            self.log.error(f'Failed obtaining deposits from {self.name}!')
            raise
        return deposits

    def get_deposits(self):
        return self._get_deposits(self.currency)

    # Withdrawals
    def _withdrawals(self, currency: str):
        raise NotImplementedError

    def _get_withdrawals(self, currency: str):
        self.log.debug(f'Obtaining withdrawals from {self.name}')
        try:
            withdrawals = self._withdrawals(currency)
            self.log.debug(f'Total number of withdrawals: {len(withdrawals)}')
        except Exception:
            self.log.error(f'Failed obtaining withdrawals from {self.name}!')
            raise
        return withdrawals

    def get_withdrawals(self):
        return self._get_withdrawals(self.currency)

    # Request withdrawal
    @cached_property
    def withdrawal_fee(self):
        try:
            return self.withdrawal_fees[self.currency]
        except KeyError:
            return 0

    def _withdraw(self, currency: str, amount: float, address: str, subtract_fee: bool=False):
        raise NotImplementedError

    def _request_withdrawal(self, currency: str, amount: float, address: str, subtract_fee: bool=False):
        withdrawal_msg = self._request_withdrawal_msg(currency)
        self.log.debug(f'Requesting {withdrawal_msg} to {address}')
        # Check dry run, request withdrawal
        if not self.dry_run:
            try:
                withdrawal = self._withdraw(currency, amount, address, subtract_fee)
            except Exception:
                self.log.error(f'Failed requesting {withdrawal_msg}! | Amount: {amount} | Address: {address}')
                raise
            msg = self._withdrawal_details_msg(f'{withdrawal_msg} requested | ', withdrawal)
            self.log.info(msg)
            return withdrawal
        else:
            msg = f'DRY RUN: {withdrawal_msg} requested'
            self.log.warning(msg)
            return False

    def _request_withdrawal_msg(self, currency: str):
        return f'{currency} withdrawal from {self.name}'

    def _withdrawal_details_msg(self, msg: str, withdrawal):
        return f'{msg} {withdrawal}'

    def request_withdrawal(self, amount: float, address: str, subtract_fee: bool=False):
        return self._request_withdrawal(self.currency, amount, address, subtract_fee)


class MarketClient(BaseMarketClient):

    def _ticker(self):
        raise NotImplementedError

    def get_ticker(self):
        self.log.debug(f'Obtaining ticker from {self.name}')
        try:
            ticker = self._ticker()
        except Exception:
            self.log.error(f'Failed obtaining ticker from {self.name}!')
            raise
        return ticker

    def _order_book(self, side: Side=None):
        raise NotImplementedError

    def get_order_book(self, side: Side=None):
        self.log.debug(f'Obtaining order book from {self.name}')
        try:
            order_book = self._order_book(side)
            order_book_len = len(order_book) if side else len(order_book.bids) + len(order_book.asks)
            self.log.debug(f'Order book has {order_book_len} orders')
        except Exception:
            self.log.error(f'Failed obtaining order book from {self.name}!')
            raise
        return order_book

    def _order_book_entry_amount(self, order):
        return order.amount

    def _order_book_entry_price(self, order):
        return order.price

    def _quote_book_price(self, order_book: list, amount: float=0):
        quote = 0
        if not order_book:
            raise OrderBookEmptyError
        for order in order_book:
            quote = self._order_book_entry_price(order)
            amount -= self._order_book_entry_amount(order)
            if amount < 0:
                break
        if amount > 0:
            self.log.warning('Total amount on order book is not enough to cover quote')
        return quote

    def quote_price(self, side: Side, amount: float=0, order_book_side=None):
        # TODO: get price from convert if it fails with  OrderBookEmptyError
        order_book = order_book_side or self.get_order_book(side)
        return self._quote_book_price(order_book, amount)

    def quote_buy_price(self, amount: float=0, order_book_bid=None):
        return self.quote_price(Side.BUY, amount, order_book_bid)

    def quote_sell_price(self, amount: float=0, order_book_ask=None):
        return self.quote_price(Side.SELL, amount, order_book_ask)

    @property
    def min_ask(self):
        return self.quote_buy_price()

    @property
    def max_bid(self):
        return self.quote_sell_price()

    def get_spread_details(self, slippage_amount: float=0, order_book=None):
        order_book = order_book or self.get_order_book()
        max_bid = self.quote_sell_price(slippage_amount, order_book.bids)
        min_ask = self.quote_buy_price(slippage_amount, order_book.asks)
        self.log.debug(f'Market Spread | Bid: {max_bid:10,f} | Ask: {min_ask:10,f}')
        return max_bid, min_ask

    def get_volume_details(self, order_book=None):
        order_book = order_book or self.get_order_book()
        volume_bid = sum([self._order_book_entry_amount(o) for o in order_book.bids])
        volume_ask = sum([self._order_book_entry_amount(o) for o in order_book.asks])
        volume_total = volume_bid + volume_ask
        # Log market volume details
        self.log.debug(f'Bid volume: {volume_bid:10,f}')
        self.log.debug(f'Ask volume: {volume_ask:10,f}')
        self.log.debug(f'Market vol: {volume_total:10,f}')
        if volume_total:
            bid_vol_p = volume_bid / volume_total
            ask_vol_p = volume_ask / volume_total
            self.log.info(f'Market Volume | Bid: {bid_vol_p:6.1%} | Ask: {ask_vol_p:6.1%}')
        else:
            self.log.warning(f'Market has no volume!')
        return volume_bid, volume_ask

    def get_vw_price(self, order_book=None):
        order_book = order_book or self.get_order_book()
        volume_bid, volume_ask = self.get_volume_details(order_book)
        max_bid, min_ask = self.get_spread_details(order_book=order_book)
        volume_total = volume_bid + volume_ask
        if volume_total:
            vw_price = round((volume_bid * max_bid + volume_ask * min_ask) / (volume_bid + volume_ask), 2)
            vw_price_str = f'{vw_price:10,f}'
        else:
            vw_price = None
            vw_price_str = 'N/A'
        self.log.info(f'Volume-Weighted Price: {vw_price_str}')
        return vw_price


class TradingClient(MarketClient):
    wallet_client = None
    has_margin_trading = False
    min_order_amount_mapping = {}

    def __init__(self, market, client=None, dry_run: bool=False, timeout: int=None,
                 logger: Logger=None, store=None, **kwargs):
        super().__init__(market, client, dry_run, timeout, logger, store, **kwargs)
        assert self.wallet_client, 'A wallet client must be defined for the client!'
        Wallets = namedtuple('Wallets', 'base quote')
        base = self._wallet_client_init(self.market.base)
        quote = self._wallet_client_init(self.market.quote)
        self.wallets = Wallets(base, quote)

    def _wallet_client_init(self, currency):
        return self.wallet_client(currency, self.client, self.dry_run, self.timeout, self.log)

    # Trading ----------------------------------------------------------------
    def _open_orders(self):
        raise NotImplementedError

    def get_open_orders(self):
        # Log fetch orders message
        self.log.debug(f'Obtaining open orders from {self.name}')
        # Fetch orders
        try:
            orders = self._open_orders()
            self.log.debug(f'Total number of orders: {len(orders)}')
            for order in orders:
                msg = self._order_details_msg(f'Order: ', order)
                self.log.debug(msg)
        except Exception:
            self.log.error(f'Failed obtaining orders from {self.name}!')
            raise
        return orders

    def _order_amount(self, order):
        return order.amount

    def get_open_orders_amount(self):
        orders = self.get_open_orders()
        amount = sum(self._order_amount(o) for o in orders)
        self.log.debug(f'Total amount on orders: {amount}')
        return amount

    def _cancel_order(self, order):
        raise NotImplementedError

    def cancel_order(self, order):
        # Log cancel order message
        self.log.debug('Canceling order')
        # Don't cancel if dry run
        if self.dry_run:
            self.log.warning(f'DRY RUN: Order cancelled')
            return
        # Iterate and cancel orders
        try:
            cancelled_order = self._cancel_order(order)
        except Exception:
            msg = self._order_details_msg('Failed to cancel order: ', order)
            self.log.error(msg)
            raise
        msg = self._order_details_msg('Order cancelled: ', cancelled_order)
        self.log.info(msg)
        return cancelled_order

    def cancel_orders(self, orders: list=None):
        # Log cancel orders message
        self.log.debug('Canceling orders')
        cancelled_orders = []
        # Don't cancel if dry run
        if self.dry_run:
            self.log.warning(f'DRY RUN: Orders cancelled')
            return cancelled_orders
        # Iterate and cancel orders
        orders = orders or self.get_open_orders()
        for order in orders:
            cancelled_order = self.cancel_order(order)
            cancelled_orders.append(cancelled_order)
        self.log.info(f'Cancelled orders: {len(cancelled_orders)}')
        return cancelled_orders

    def _order_details(self, order_id: int):
        raise NotImplementedError

    def order_details(self, order_id: int):
        self.log.debug(f'Obtaining order details from {self.name} for order {order_id}')
        try:
            order = self._order_details(order_id)
        except Exception:
            self.log.error(f'Failed obtaining order details from {self.name}!')
            raise
        msg = self._order_details_msg('Order: ', order)
        self.log.debug(msg)
        return order

    @cached_property
    def min_order_amount(self):
        try:
            return self.min_order_amount_mapping[self.market.base]
        except KeyError:
            return 0

    def _place_order(self, side: Side, o_type: OrderType, amount: float, price: float=None):
        raise NotImplementedError

    def place_order(self, side: Side, o_type: OrderType, amount: float, price: float=None):
        order_msg = self._place_order_msg(side, o_type)
        self.log.debug(f'Placing {order_msg} order')
        # Don´t place order if the amount is lower than the min allowed
        if self.min_order_amount and amount < self.min_order_amount:
            msg = f'{order_msg} order was not placed! {amount:,f} < Min Amount ({self.min_order_amount})'
            self.log.warning(msg)
            return False
        # Check dry run, place order
        if not self.dry_run:
            try:
                new_order = self._place_order(side, o_type, amount, price)
            except Exception:
                self.log.error(f'Failed placing {order_msg} order! | Amount: {amount} | Price: {price}')
                raise
            msg = self._order_details_msg(f'{order_msg} order placed: ', new_order)
            self.log.info(msg)
            return new_order
        else:
            msg = f'DRY RUN: {order_msg} order placed'
            self.log.warning(msg)
            return False

    def place_market_order(self, side: Side, amount: float):
        return self.place_order(side, OrderType.MARKET, amount)

    def place_limit_order(self, side: Side, amount: float, price: float):
        return self.place_order(side, OrderType.LIMIT, amount, price)

    def _place_order_msg(self, side: Side, order_type: OrderType=None):
        msg = side.value
        if order_type:
            msg = f'{msg} {order_type.value}'
        return f'{msg} order'

    def _order_details_msg(self, msg: str, order):
        return f'{msg} {order}'

    # Margin Trading ---------------------------------------------------------
    def _open_positions(self):
        raise NotImplementedError

    def get_open_positions(self):
        # Log fetch positions message
        self.log.debug(f'Obtaining open positions from {self.name}')
        # Fetch positions
        try:
            positions = self._open_positions()
            self.log.debug(f'Total number of positions: {len(positions)}')
        except Exception:
            self.log.error(f'Failed obtaining positions from {self.name}!')
            raise
        return positions

    def _position_amount(self, position):
        return float(position['amount'])

    def get_open_positions_amount(self):
        positions = self.get_open_positions()
        amount = sum(self._position_amount(p) for p in positions)
        self.log.debug(f'Total amount on positions: {amount}')
        return amount

    def _open_position(self, side: Side, o_type: OrderType, amount: float, price: float=None, leverage: float=None):
        raise NotImplementedError

    def open_position(self, side: Side, p_type: OrderType, amount: float, price: float=None, leverage: float=None):
        position_msg = self._open_position_msg(side, p_type)
        self.log.debug(f'Placing {position_msg} order')
        # Don´t place order if the amount is lower than the min allowed
        if self.min_order_amount and amount < self.min_order_amount:
            msg = f'{position_msg} position was not open! {amount:,f} < Min Amount ({self.min_order_amount})'
            self.log.warning(msg)
            return False
        # Check dry run, place position
        if not self.dry_run:
            try:
                new_position = self._open_position(side, p_type, amount, price, leverage)
            except Exception:
                self.log.error(f'Failed to open {position_msg} position!')
                raise
            msg = self._position_details_msg(f'{position_msg} position opened | ', new_position)
            self.log.info(msg)
            return new_position
        else:
            msg = f'DRY RUN: {position_msg} order placed'
            self.log.warning(msg)
            return False

    def open_market_position(self, side: Side, amount: float, leverage: float=None):
        return self.open_position(side, OrderType.MARKET, amount, leverage)

    def open_limit_position(self, side: Side, amount: float, price: float, leverage: float=None):
        return self.open_position(side, OrderType.LIMIT, amount, price, leverage)

    def _open_position_msg(self, side: Side, position_type: OrderType=None):
        msg = side.value
        if position_type:
            msg = f'{msg} {position_type.value}'
        return f'{msg} position'

    def _position_details_msg(self, msg: str, position):
        return f'{msg} {position}'
