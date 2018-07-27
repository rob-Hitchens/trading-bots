import logging
from logging import Logger

import pygogo
from pygogo.utils import get_structured_filter

from ..conf import settings

config = settings.logging
bots_root = config['bots_root']
log_level = config['level']
file = settings.logging.get('file')

# Configure logger
console_format = '%(asctime)s UTC | %(tag)s | %(env)-4s | %(bot)s | %(config)s | %(levelname)-8s | %(message)s'
console_formatter = logging.Formatter(console_format)

if file:
    low_level_handler = pygogo.handlers.file_hdlr(file)
else:
    low_level_handler = pygogo.handlers.stdout_hdlr()

gogo = pygogo.Gogo(
    name=config['bots_root'],
    low_formatter=console_formatter,
    high_formatter=console_formatter,
    low_level=log_level['low'],
    high_level=log_level['high'],
    low_hdlr=low_level_handler,
    high_hdlr=pygogo.handlers.stderr_hdlr(),
    monolog=True,
)


def setup_logger(logger: Logger, **logger_kwargs):
    if not logger.handlers:
        logger_name = logger.name.partition('.')[2]
        logger = gogo.get_logger(logger_name)
    structured_filter = get_structured_filter(**logger_kwargs)
    for handler in logger.handlers:
        handler.addFilter(structured_filter)
        handler.setFormatter(console_formatter)
    return logger


def get_logger(logger_name: str):
    logger = logging.getLogger(f'{bots_root}.{logger_name}')
    return logger
