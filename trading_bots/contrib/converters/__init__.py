from decimal import Decimal

from trading_bots.conf import settings
from trading_bots.core.logging import get_logger

logger = get_logger(__name__)
Number = (float, Decimal)


class ConverterRateError(Exception):
    def __init__(self, converter):
        logger.exception(f'{converter} failed to get rate!')
        super().__init__()


class ConverterValidationError(Exception):
    def __init__(self, converter, rate):
        logger.exception(f'{converter} rate is invalid!: {rate}')
        super().__init__()


class Converter(object):
    name = ''
    slug = ''

    def __init__(self, return_decimal: bool=False, **kwargs):
        assert self.name, 'A converter must have a name!'
        self.credentials = settings.credentials.get(self.name)
        self.return_decimal = return_decimal

    def _format_number(self, value: (str, Number)) -> Number:
        if self.return_decimal:
            if not isinstance(value, Decimal):
                return Decimal(value)
        return float(value)

    def _get_rate(self, currency: str, to: str) -> (str, Number):
        raise NotImplementedError

    def get_rate_for(self, currency: str, to: str, reverse: bool=False) -> Number:
        """Get current market rate for currency"""

        # Return 1 when currencies match
        if currency.upper() == to.upper():
            return self._format_number('1.0')

        # Set base and quote currencies
        base, quote = currency, to
        if reverse:
            base, quote = to, currency

        try:  # Get rate from source
            rate = self._get_rate(base, quote)
        except Exception as e:
            raise ConverterRateError(self.name) from e

        # Convert rate to number
        rate = self._format_number(rate)

        try:  # Validate rate value
            assert isinstance(rate, Number)
            assert rate > 0
        except AssertionError as e:
            raise ConverterValidationError(self.name, rate) from e

        # Return market rate
        if reverse:
            return self._format_number('1.0') / rate
        return rate

    def convert(self, amount: Number, currency: str, to: str, reverse: bool=False) -> Number:
        """Convert amount to another currency"""
        rate = self.get_rate_for(currency, to, reverse)
        if self.return_decimal:
            amount = Decimal(amount)
        return amount * rate
