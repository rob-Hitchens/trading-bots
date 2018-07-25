import trading_api_wrappers as wrappers

from .base import Converter

__all__ = [
    'OpenExchangeRates'
]


class OpenExchangeRates(Converter):
    name = 'OpenExchangeRates'
    slug = 'open-exchange-rates'

    def __init__(self, return_decimal: bool=False, timeout: int=None, retry: bool=None):
        super().__init__(return_decimal)
        app_id = self.credentials['app_id']
        self.client = wrappers.OXR(app_id, timeout, retry)

    def _get_rate(self, currency: str, to: str):
        response = self.client.latest(base=currency.lower(), symbols=[to.lower()])
        rate = response['rates'][to.upper()]
        return rate
