import trading_api_wrappers as wrappers

from . import Converter


class OpenExchangeRates(Converter):
    name = 'Open Exchange Rates'
    slug = 'open-exchange-rates'

    def __init__(self, return_decimal: bool=False, timeout: int=None, retry: bool=None):
        super().__init__(return_decimal)
        app_id = self.credentials['app_id']
        self.client = wrappers.OXR(app_id, timeout, retry)

    def _get_rate(self, currency: str, to: str):
        response = self.client.latest(base=currency.lower(), symbols=[to.lower()])
        rate = response['rates'][to.upper()]
        return rate
