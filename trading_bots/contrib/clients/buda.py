from trading_api_wrappers import Buda

from .base import *

__all__ = [
    'BudaBase',
    'BudaPublic',
    'BudaAuth',
    'BudaMarket',
    'BudaWallet',
    'BudaTrading',
]

PER_PAGE = 300


def paginated(data_attr: str):
    def func_wrapper(func):
        def wrapper():
            data = []
            page = 1
            while True:
                paginated_data = func(page)
                new_data = getattr(paginated_data, data_attr)
                data.extend(new_data)
                page = paginated_data.meta.current_page + 1
                if page > paginated_data.meta.total_pages:
                    return data
        return wrapper
    return func_wrapper


class BudaBase(BaseClient):
    name = 'Buda'

    def __init__(self, client=None, dry_run: bool=False, timeout: int=None, logger=None, store=None, host: str=None):
        self.host = host
        super().__init__(client, dry_run, timeout, logger, store)


class BudaPublic(BudaBase):

    class Client(APIClient, Buda.Public):
        pass

    def _client(self):
        return self.Client(self.timeout, host=self.host)


class BudaAuth(BudaBase):

    class Client(APIClient, Buda.Auth):
        pass

    def _client(self):
        key = self.credentials['key']
        secret = self.credentials['secret']
        return self.Client(key, secret, timeout=self.timeout, host=self.host)


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
        @paginated('deposits')
        def deposits(page):
            return self.client.deposit_pages(currency, page=page, per_page=PER_PAGE)
        return deposits()

    def _withdrawals(self, currency: str):
        @paginated('withdrawals')
        def withdrawals(page):
            return self.client.withdrawal_pages(currency, page=page, per_page=PER_PAGE)
        return withdrawals()

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
        @paginated('orders')
        def open_orders(page):
            state = Buda.OrderState.PENDING
            return self.client.order_pages(self.market_id, page=page, per_page=PER_PAGE, state=state)
        return open_orders()

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
