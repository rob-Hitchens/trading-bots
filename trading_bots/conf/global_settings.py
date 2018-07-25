from . import defaults

tag = 'TradingBots'

dry_run = True

installed_bots = ()

logging = {
    'bots_root': defaults.BOTS_LOG_ROOT,
    'filename': defaults.LOG_FILE,
    'levels': {
        'low': 'debug',
        'high': 'info',
    },
}

storage = {
    'name': 'json',
    'settings': {
        'filename': 'store.json',
    },
}

timeout = 120

urls = {}
