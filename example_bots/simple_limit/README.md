# Buda Bots - Simple Limit example

Example use case of Buda.com Bots framework for creating and running cryptocurrency trading bots.

## Overview

Buying and selling at market price on illiquid markets can be hard on the execution price. Our first reaction would be to use limit orders, nevertheless illiquid markets can take time to fill this orders while price changes constantly and competing traders outbids our orders.

Simple Limit is an easy way to use of buy and sell limit orders. It allows us to auto renew our orders using a reference market and a simple price multiplier to set an offset for our orders.
The reference market should be active enough to take its price as a good reference and place our limit orders at a higher or lower price.


## Installation

Clone or download this repository to your working environment
```bash
git clone https://github.com/budacom/buda-bots.git
```

Then, open a console and install requirements:
```bash
pip install -r requirements.txt
```
We are ready!

## Authentication

### API Key

Copy the file `secrets.yml.example` and rename it to `secrets.yml`. Then fill with an API key and secret to access your Buda.com account.

### Warnings

- This library will create live orders at Buda.com cryptocurrency exchange. Please review the code and check all the parameters of your strategy before entering your keys and running the bot.
- Some bots make use of a storage file. Default storage saves data as JSON objects inside store.json file found at the root of this project. This file could contain data essential for the correct execution of this strategy.

## Usage

For more references, go to the [official documentation](https://docuseba.com/).

### Setup Config File

Found at the root of this project. Its a yaml file that allows us to easily set our stategy's parameters.

**Example:**
```yml
simple_limit:
  loop_time: 1                # Minutes to wait between orders update
  market: BTCCLP              # Buda.com market where orders will be placed
  reference:
    name: Bitstamp            # Reference exchange to use for price
    market: BTCUSD            # Reference market to use for price
  prices:
    buy_multiplier: 0.95      # Price multiplier for buy order, ie: 1.05 is 5% above reference
    sell_multiplier: 1.05     # Price multiplier for sell order, ie: 0.95 is 5% under reference
  amounts:
   max_base: 1                #  Max amount on sell order, ie: base is BTC on BTCCLP
   max_quote: 25000000        #  Max amount on buy order, ie: quote is CLP on BTCCLP
```

## Bot Strategy



### Init

```
def __init__(self, market: (str, Market), config: dict=None):
    super().__init__(market, config)
    # Set configs
    self.sl_config = self.config['simple_limit']
    self.bid_price, self.ask_price = None, None
    self.base_amount, self.quote_amount = None, None
    # Set buda trading client
    buda_dry_run = config['dry_run']['buda']
    buda_env = config['buda_env']
    self.buda = buda.BudaTrading(
        self.market, dry_run=buda_dry_run, timeout=self.timeout, logger=self.log,
        store=self.store, env=buda_env)
    # Set reference market client
    reference_config = self.sl_config['reference']
    self.reference = self._get_market_client(reference_config['name'], reference_config['market'])
    assert self.reference.market.base == self.market.base
```

- At the beginning of our bot Class we initialize placeholders for our `prices` and `amounts`.
- Also setup our clients and variables according to the reference `market` on our configs.

### Strategy

This functions runs at every `loop_time` minutes. We describe our instructions following our desired strategy logic:

```python
def _strategy(self):
    # Setup
    self.log.info(f'Preparing prices using {self.reference.name} {self.reference.market.code}')
    self.prepare_prices()
    # Cancel open orders
    self.log.info('Closing open orders')
    self.cancel_orders()
    # Get available balances
    self.prepare_amounts()
    # Start strategy
    self.log.info('Starting order deployment')
    # Deploy orders
    deploy_list = self.get_deploy_list()
    self.deploy_orders(deploy_list)
```


**Prepare prices**

- First, we go fetch our reference price from the selected exchange and market quoting its orderbook.
- Our reference price gets converted our market's quote currency and is saved as ref_bid and ref_ask.
- We offset our reference prices using our multipliers from configs and save them as bid_price and ask_price

**Cancel orders**

- Cancel all pending orders at the selected market on Buda.com. This frees balance to use on our orders

**Prepare Amounts**
- Get amounts from configs to dictate maximum allowed to spend on each order
- Validates against available balance
- Sets the amount to be used on orders as quote_amount and base_amount

**Get Deploy List**
- Builds a list of orders to be deployed

**Deploy Orders**
- Places our orders at the exchange (You can test with `dry_run=True` flag on configs to be sure)

### Abort

As important as our strategy is providing abort instructions which is the piece of code that executes in case anything goes wrong:

```
def _abort(self):
    self.log.error('Aborting strategy, cancelling all orders')
    try:
        self.cancel_orders()
    except Exception:
        self.log.exception(f'Failed!, some orders might not be cancelled')
        raise
    else:
        self.log.info(f'All open orders were cancelled')
```
- Very simple abort function, we want to cancel all pending orders and exit

## Runing bots

Simply run the desired bot file from console.
```bash
$ python simple-limit.py
```

Flag `--config` can be specified to change the default config file

```bash
$ python simple-limit.py --config /path/to/simple-limit_other.yml
```
Runing multiple bots for different markets is possible using multiple shells and config files:

Shell 1:
```bash
$ python simple-limit.py --config simple-limit_btcclp.yml
```
Shell 2:
```bash
$ python simple-limit.py --config simple-limit_ethclp.yml
```



## Contributing

Blablala
