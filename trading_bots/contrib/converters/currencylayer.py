import trading_api_wrappers as wrappers

from . import Converter


class CurrencyLayer(Converter):
    name = 'Currencylayer'
    slug = 'currencylayer'

    def __init__(self, return_decimal: bool=False, timeout: int=None, retry: bool=None):
        super().__init__(return_decimal)
        access_key = self.credentials['access_key']
        self.client = wrappers.CurrencyLayer(access_key, timeout, retry)

    def _get_rate(self, currency: str, to: str):
        market = (currency + to).upper()
        response = self.client.live_rates(base=currency.lower(), currencies=[to.lower()])
        rate = response['quotes'][market]
        return rate
