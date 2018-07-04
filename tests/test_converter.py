from collections import namedtuple
from operator import attrgetter

import pytest
from simple_settings import settings

from trading_bots.contrib.converters import Converter
from trading_bots.contrib.converters.bitcoin_average import BitcoinAverage
from trading_bots.contrib.converters.coinmarketcap import CoinMarketCap
from trading_bots.contrib.converters.currencylayer import CurrencyLayer
from trading_bots.contrib.converters.open_exchange_rates import OpenExchangeRates

CREDENTIALS = settings.credentials

CRYPTO_CONVERTERS = [
    BitcoinAverage(),
    CoinMarketCap(),
]

FIAT_CONVERTERS = [
    CurrencyLayer(CREDENTIALS.get('CurrencyLayer')),
    OpenExchangeRates(CREDENTIALS.get('OpenExchangeRates')),
]

Market = namedtuple('market', 'base quote id')

CRYPTO_MARKETS = [
    Market('BTC', 'CLP', 'upper'),
    Market('btc', 'CLP', 'lower_base'),
    Market('BTC', 'clp', 'lower_quote'),
    Market('BTC', 'BTC', 'same'),
]

FIAT_MARKETS = [
    Market('USD', 'CLP', 'upper'),
    Market('usd', 'CLP', 'lower_base'),
    Market('USD', 'clp', 'lower_quote'),
    Market('USD', 'BTC', 'same'),
]


@pytest.fixture(params=CRYPTO_CONVERTERS, ids=attrgetter('slug'))
def crypto_converter(request):
    return request.param


@pytest.fixture(params=FIAT_CONVERTERS, ids=attrgetter('slug'))
def fiat_converter(request):
    return request.param


@pytest.fixture(params=CRYPTO_MARKETS, ids=attrgetter('id'))
def crypto_market(request):
    return request.param


@pytest.fixture(params=FIAT_MARKETS, ids=attrgetter('id'))
def fiat_market(request):
    return request.param


def test_crypto_converter_instance(crypto_converter):
    assert isinstance(crypto_converter, Converter)


def test_fiat_converter_instance(fiat_converter):
    assert isinstance(fiat_converter, Converter)


def test_get_crypto_rate(crypto_converter, crypto_market):
    rate = crypto_converter.get_rate_for(crypto_market.base, to=crypto_market.quote)
    assert isinstance(rate, float)
    assert rate > 0


def test_get_fiat_rate(fiat_converter, fiat_market):
    rate = fiat_converter.get_rate_for(fiat_market.base, to=fiat_market.quote)
    assert isinstance(rate, float)
    assert rate > 0


def test_convert_crypto(crypto_converter, crypto_market):
    amount = crypto_converter.convert(0.5, currency=crypto_market.base, to=crypto_market.quote)
    assert isinstance(amount, float)
    assert amount > 0


def test_convert_fiat(fiat_converter, fiat_market):
    amount = fiat_converter.convert(0.5, currency=fiat_market.base, to=fiat_market.quote)
    assert isinstance(amount, float)
    assert amount > 0
