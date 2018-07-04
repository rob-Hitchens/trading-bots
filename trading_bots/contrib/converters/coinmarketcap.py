import trading_api_wrappers as wrappers

from . import Converter


class CoinMarketCap(Converter):
    name = 'CoinMarketCap'
    slug = 'coinmarketcap'

    def __init__(self, return_decimal: bool=False, timeout: int=None, retry: bool=None):
        super().__init__(return_decimal)
        self.client = wrappers.CoinMarketCap(timeout, retry)

    def _get_rate(self, currency: str, to: str):
        rate = self.client.price(currency, convert=to)
        return rate
