from .clients import *
from ..base.exchange import Exchange

__all__ = [
    'Kraken',
]


class Kraken(Exchange, KrakenPublic):
    market_client = KrakenMarket
    wallet_client = KrakenWallet
    trading_client = KrakenTrading
