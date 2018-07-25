import asyncio
import time
from logging import Logger

import trading_bots
from .registry import bots
from ..conf import settings


class BotTask:
    """Class representing a Bot Task."""

    def __init__(self, bot_label: str, config_name: str, logger: Logger=None):
        settings.configure()
        trading_bots.setup()
        self.config_name = config_name
        self.bot_cls = bots.get_bot(bot_label).cls
        self.bot_config = bots.get_config(bot_label, config_name)
        self.bot_instance = self.bot_cls(self.bot_config, self.config_name, logger)

    def run_once(self):
        self.bot_instance.execute()

    def loop(self, interval: int):
        while True:
            self.run_once()
            time.sleep(interval)

    async def loop_async(self, interval: int):
        while True:
            self.run_once()
            await asyncio.sleep(interval)

    def run_loop(self, interval: int):
        self.loop(interval)

    def run_loop_async(self, interval: int):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.loop_async(interval))
        loop.close()
