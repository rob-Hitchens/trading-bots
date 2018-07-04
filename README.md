![Buda](https://raw.githubusercontent.com/budacom/trading-bots/master/static/buda-logo.svg?sanitize=true)

# Trading Bots 🤖

> A simple framework for bootstrapping your **Crypto Trading Bots** on Python 3.6+. (Alpha stage)

> Supported by [Buda.com](https://www.buda.com)

> **Disclaimer:** Still at an early stage of development. Rapidly evolving APIs.

![status](https://img.shields.io/badge/status-alpha-red.svg)
![python](https://img.shields.io/badge/python-3.6,&nbsp;3.7-blue.svg)
![license](https://img.shields.io/badge/license-MIT-blue.svg)


**Trading-Bots** is a general purpose *mini-framework* for developing an [algorithmic trading bot](https://en.wikipedia.org/wiki/Algorithmic_trading) on **crypto currencies**, thus it makes no assumption of your trading goals.


## Installation

### Requirements
* macOS, Windows or Linux
* Python 3.6 or 3.7

To install Trading-Bots, simply use `pipenv` (or `pip`, of course):

    $ pipenv install trading-bots

## Getting started

### Create simple bot

Let's create a simple bot that fetches your **Bitcoin** balance on [Buda.com](https://www.buda.com)...

Start a Trading-Bots project with the `bots` CLI `startproyect` command, name it `MyProject`:

    $ bots startproyect

    TRADING BOTS 🤖
    ===============

    Name [MyAwesomeProject]: MyProject
    Directory [.]: .

Bootstrap a new Bot with `createbot`, name it `MyBot` and put it in the `my_project` directory (created previously by `startproject`)

    $ bots createbot

    TRADING BOTS 🤖
    ===============

    Name [MyAwesomeBot]: MyBot
    Directory (your projects dir): my_project

Add `MyBot` to `installed_bots` on `settings.yml`:

```yaml
# settings.yml

installed_bots:
  - my_project.my_bot.bot.MyBot  
```

Configure you Buda.com account's `API_KEY` and `API_SECRET` onto `secrets.yml` credentials:

You can mail support to request your API credentials on [soporte@buda.com](mailto:soporte@buda.com)

```yaml
# secrets.yml

credentials:
  Buda:
    key: MY_API_KEY
    secret: MY_API_SECRET
```

Now let's fetch the Bitcoin balance on Buda.com implementing the Bot's algorithm. The Bot's logic resides in the `my_project/my_bot/bot.py` module created by the `createbot` command:

```py
# my_project/my_bot/bot.py

# Base class that all Bots must inherit from
from trading_bots.bots import Bot

# The settings module contains all values from settings.yml and secrets.yml
from trading_bots.conf import settings

# API Wrapper for Buda.com
from trading_api_wrappers import Buda


class Mybot(Bot):
    label = 'MyBot'

    def _setup(self, config):
        # Get API_KEY and API_SECRET from credentials
        credentials = settings.credentials['Buda']
        key = credentials['key']
        secret = credentials['secret']

        # Initialize a Buda Auth client
        self.buda = Buda.Auth(key, secret)

    def _algorithm(self):
        # Fetch the Bitcoin balance from Buda.com
        balance = self.buda.balance('BTC')

        # Log the Bitcoin balance
        self.log.info(f'I have {balance.amount.amount} BTC')

    def _abort(self):
        # Abort logic, runs on exception
        self.log.error(f'Something went wrong with MyBot!')
```

We can make our Bot a little more modular, let's now fetch our Ethereum balance adding a `currency` key on `MyBot` default config file on `my_project/my_bot/configs/default.yml`:

```yaml
# my_project/my_bot/configs/default.yml

currency: ETH
```

Now use the new `currency` config on `MyBot` modifing the Bot's logic:

```py
# my_project/my_bot/bot.py

from trading_bots.bots import Bot
from trading_bots.conf import settings

from trading_api_wrappers import Buda


class Mybot(Bot):
    label = 'MyBot'

    def _setup(self, config):
        # Get currency from config 
        self.currency = config['currency']

        # Get API_KEY and API_SECRET from credentials
        credentials = settings.credentials['Buda']
        key = credentials['key']        
        secret = credentials['secret']

        # Initialize a Buda Auth client
        self.buda = Buda.Auth(key, secret)

    def _algorithm(self):
        # Fetch the currency balance from Buda.com
        balance = self.buda.balance(self.currency)

        # Log the currency balance
        self.log.info(f'I have {balance.amount.amount} {self.currency}')

    def _abort(self):
        # Abort logic, runs on exception
        self.log.error(f'Something went wrong with MyBot!')
```

Run the bot!

    $ bots run MyBot

    TRADING BOTS 🤖
    ===============

    Global settings
    - Settings files: None
    - Logs file: log.txt

    Bot: MyBot
    - Config file: default

    Starting MyBot 1530691595: 2018-07-04 08:06:35
    This is an example bot
    Doing work for 5 seconds...
    Finished!
    Run time: 5.9972 seconds
    Ending MyBot 1530691595: 2018-07-04 08:06:40

Or put it to work in a loop!

    $ bots loop MyBot --interval 10

    TRADING BOTS 🤖
    ===============

    Global settings
    - Settings files: None
    - Logs file: log.txt

    Bot: MyBot
    - Config file: default
    - Interval: 5s

    Starting MyBot 1530692725: 2018-07-04 08:25:25
    This is an example bot
    Doing work for 5 seconds...
    Finished!
    Run time: 5.3611 seconds
    Ending MyBot 1530692725: 2018-07-04 08:25:30

    Starting MyBot 1530692735: 2018-07-04 08:25:35
    This is an example bot
    Doing work for 5 seconds...
    Finished!
    Run time: 5.3632 seconds
    Ending MyBot 1530692735: 2018-07-04 08:25:40



## Bots CLI

Trading-Bots comes with a handy `CLI` named... `bots`!

### Commands

#### Start a project

    $ bots startproject

```bash
TRADING BOTS 🤖
===============

Name [MyAwesomeProject]: MyProject
Directory [.]: .

Success: 'MyProject' project was successfully created on '.'
```

`startproject` creates a Trading-Bots project directory structure for the given project `NAME` in the current directory `.` or optionally in the given `DIRECTORY`.

    project_dir/
    - project_name/
    - bots.py
    - secrets.yml
    - settings.yml


#### Create a bot

    $ bots createbot

```bash
TRADING BOTS 🤖
===============

Name [MyAwesomeBot]: MyBot
Directory (your projects dir): my_project

Success: 'MyBot' bot was successfully created on 'my_project'
```

`createbot` creates a Bot's directory structure for the given bot `NAME` in the current directory `.` or optionally in the given `DIRECTORY`.

    project_dir/
    - project_name/
    - bots.py
    - secrets.yml
    - settings.yml


After creating or a new Bot, you must add it to `installed_bots` on `settings.yml`:

```yaml
# settings.yml

installed_bots:
  - trading_bots.mybot.bot.MyBot  
```


#### Run bot once

    $ bots run BOT [OPTIONS]

Run a specified `BOT` by label. Options:

|                |     |
| ---            | --- |
| `-c, --config` | Bot configuration filename (YAML format) |
| `-l, --log`    | Log to this file |
| `--settings`   | Global settings files (YAML format) |


```bash
$ bots run Example

TRADING BOTS 🤖
===============

Global settings
- Settings files: None
- Logs file: log.txt

Bot: Example
- Config file: default

Starting Example 1530691595: 2018-07-04 08:06:35
This is an example bot
Doing work for 5 seconds...
Finished!
Run time: 5.9972 seconds
Ending Example 1530691595: 2018-07-04 08:06:40
```

#### Run bot in a loop

    $ bots loop BOT [OPTIONS]

Schedule a `BOT` (by label) to run on an interval. Options:

|                |     |
| ---            | --- |
| `-i, --interval` | Loop interval (in seconds). |
| `-c, --config`   | Bot configuration filename (YAML format) |
| `-l, --log`      | Log to this file |
| `--settings`     | Global settings files (YAML format) |

```bash
$ bots loop Example -i 5

TRADING BOTS 🤖
===============

Global settings
- Settings files: None
- Logs file: log.txt

Bot: Example
- Config file: default
- Interval: 5s

Starting Example 1530692725: 2018-07-04 08:25:25
This is an example bot
Doing work for 5 seconds...
Finished!
Run time: 5.3611 seconds
Ending Example 1530692725: 2018-07-04 08:25:30

Starting Example 1530692735: 2018-07-04 08:25:35
This is an example bot
Doing work for 5 seconds...
Finished!
Run time: 5.3632 seconds
Ending Example 1530692735: 2018-07-04 08:25:40

...
```

### Disclaimer

__USE THE SOFTWARE AT YOUR OWN RISK. YOU ARE RESPONSIBLE FOR YOUR OWN MONEY. PAST PERFORMANCE IS NOT NECESSARILY INDICATIVE OF FUTURE RESULTS.__

__THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.__
