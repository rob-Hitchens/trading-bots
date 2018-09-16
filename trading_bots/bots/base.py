import time
from logging import Logger

from .logging import get_logger
from .logging import setup_logger
from ..conf import defaults
from ..conf import settings
from ..core.storage import get_store
from ..utils import get_iso_time_str


class Bot:
    """Class representing a base Trading Bot and its logic."""

    label = ''
    verbose_name = ''
    config_file = ''

    def __init__(self, config: dict=None, config_name: str=None, logger: Logger=None):
        assert self.label, 'A Bot object must have a label attribute!'
        # Set configuration
        self.config = config
        self.config_name = config_name or defaults.BOT_CONFIG
        # Configs
        self.dry_run = settings.dry_run
        self.timeout = settings.timeout
        self.env = self.get_env()
        # Set logger
        self.log = logger or self.get_logger()
        self.setup_logger(self.log)
        # Set store
        self.store = get_store(self.log)
        # Time
        self.timestamp = None
        self.run_time = None
        # User setup
        self._setup(self.config)

    def _setup(self, config: dict):
        pass

    def _algorithm(self):
        raise NotImplementedError

    def _abort(self):
        pass

    def _post_exec(self):
        pass

    def execute(self):
        self.timestamp = int(time.time())
        msg = f'Starting {self.label} {self.timestamp}: {get_iso_time_str()} '
        self.log.info(f'{msg:-<80}')

        try:
            self.check_dry_run()
            self._algorithm()

        except Exception:
            self.log.exception(f'Bot entered an invalid state!')
            self._abort()
            raise

        except KeyboardInterrupt:
            self.log.warning(f'Bot execution cancelled!')
            self._abort()
            raise

        finally:
            if self.timestamp:
                self.run_time = time.time() - self.timestamp
                self.log.info(f'Run time: {self.run_time:,.4f} seconds')
                msg = f'Ending {self.label} {self.timestamp}: {get_iso_time_str()} '
            else:
                msg = f'Ending {self.label}: {get_iso_time_str()} '
            self.log.info(f'{msg:-<80}')
            self._post_exec()

    def abort(self):
        try:
            self.log.warning(f'Aborting {self.label} bot...')
            self._abort()
        except Exception:
            self.log.critical('Failed to abort!', exc_info=True)
            raise

    def setup_logger(self, logger: Logger):
        logger_kwargs = self._logger_kwargs()
        self.log = setup_logger(logger, **logger_kwargs)

    def _get_logger_name(self):
        return f'{self.label}.{self.config_name}'

    def get_logger(self):
        logger_name = self._get_logger_name()
        return get_logger(logger_name)

    def _logger_kwargs(self):
        return {'tag': settings.tag, 'env': self.env, 'bot': self.label, 'config': self.config_name}

    def check_dry_run(self):
        if self.dry_run:
            self.log.warning('DRY RUN!')
        return self.dry_run

    def get_env(self):
        return 'TEST' if self.dry_run else 'LIVE'
