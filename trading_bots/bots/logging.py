import logging
import os
from logging import Logger

import pygogo
from pygogo.utils import get_structured_filter

from ..conf import settings

# Configure logger
console_format = '%(asctime)s UTC | %(tag)s | %(bot)s | %(config)s | %(levelname)-8s | %(message)s'
console_formatter = logging.Formatter(console_format)


def setup_pygogo(root_name='bots', logger_name='bot',
                 low_level_handler=None, high_level_handler=None,
                 monolog=True, verbose=None, file=None):

    if low_level_handler is None:
        if file:
            low_level_handler = pygogo.handlers.file_hdlr(os.path.join('logs', file))
        else:
            low_level_handler = pygogo.handlers.stdout_hdlr()

    log_level = settings.log_level

    pygogo.Gogo(
        name=root_name,
        low_formatter=console_formatter,
        high_formatter=console_formatter,
        low_level=log_level['low'],
        high_level=log_level['high'],
        low_hdlr=low_level_handler,
        high_hdlr=high_level_handler or pygogo.handlers.stderr_hdlr(),
        verbose=verbose,
        monolog=monolog,
    ).get_logger(logger_name)


def setup_logger(logger: Logger, logger_name: str, **logger_kwargs):
    if not logger.handlers:
        setup_pygogo(logger_name=logger_name)
    structured_filter = get_structured_filter(**logger_kwargs)
    for handler in logger.handlers:
        handler.addFilter(structured_filter)
        handler.setFormatter(console_formatter)
