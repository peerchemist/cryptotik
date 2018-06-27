# cryptotik
Standardized common API for several cryptocurrency exchanges.
Cryptotik is python3 compatible collection of cryptocurrency exchange wrappers.
Main goal of cryptotik is to deliver unified common interface to some of the most popular cryptocurrency exchanges, cryptotik accomplishes that by standardizing names of the methods and expected inputs and outputs.

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![PyPI](https://img.shields.io/pypi/l/cryptotik.svg?style=flat-square)]()
[![PyPI](https://img.shields.io/pypi/v/cryptotik.svg?style=flat-square)](https://pypi.python.org/pypi/cryptotik/)

## Install

`pip install cryptotik`

or latest development version:

`pip install git+git://github.com/indiciumfund/cryptotik.git`

# Supported Exchanges
| Exchange            | API  | Public Methods    | Private Methods    | Normalized Private | Normalized Public | Tests |
|---------------------|------|-------------------|--------------------|--------------------|-------------------|-------|
| www.binance.com     | Done | Done              | Done               | TODO               | Done              | Done  |
| [bitkonan.com](https://bitkonan.com/)        | Done | Done              | TODO                 | TODO             | TODO              | TODO  |
| www.bitstamp.net    | Done | Done              | Done               | TODO               | Done              | Done  |
| [bittrex.com](https://bittrex.com/)         | Done | Done              | Done               | TODO             | Done              | Done  |
| www.cryptopia.co.nz | Done | Done              | Done               | TODO               | Done              | Done  |
| [hitbtc.com](https://hitbtc.com/)          | Done | Done              | Done                 | TODO             | Done              | Done  |
| www.kraken.com      | Done | Done              | Done               | TODO               | Done              | Done  |
| [poloniex.com](https://poloniex.com/)        | Done | Done              | Done               | TODO               | Done              | Done  |
| [therocktrading.com](https://therocktrading.com/)  | Done | Done              | Done               | TODO               | Done              | Done  |
| [wex.nz](https://wex.nz/)              | Done | Done              | Done               | TODO               | Done              | Done  |


## Examples

Right now library supports: Wex.nz, Poloniex.com, Bitstamp.com, Kraken.com Bittrex.com, Binance, TheRockTrading, HitBtc, Bitkonan with elementary support for Livecoin.
Library supports other useful features like wrapper around Coinmarketcap.com's public API.

`from cryptotik import Wex, Bittrex, Poloniex`

You only need to learn commands once, for example `get_markets` will work anywhere:

`Bittrex().get_markets()`

`Poloniex().get_markets()`

`Wex().get_markets()`

`Binance().get_markets()`

and will yield similar results. However parsing and interpreting them is left to user.

## More examples

`Wex().get_market_ticker("ppc-btc")`

`Poloniex().get_market_order_book("btc-nxt")`

`Bittrex().get_market_depth("btc-maid")`

`Binance().get_market_ticker('etc-eth')`

## Private API methods (the ones that require authentication)

Library also supports private API methods for Poloniex, Binance, Bitstamp, Kraken, TheRockExchange, Bittrex, Wex and some others.
To use them you need to make class instance though with your API credentials.

`polo = Poloniex(yourkey, yoursecret)`

`polo.get_balances()`

`polo.withdraw(<coin>, <amount>, <address>)`

Same goes for Bittrex:

`btrx = Bittrex(yourkey, yoursecret)`

`btrx.get_balances()`

`btrx.withdraw(<coin>, <amount>, <address>)`

And Wex:

`wex = Wex(yourkey, yoursecret)`

`Wex.get_balances()`

`Wex.withdraw(<coin>, <amount>, <address>)`

----------------------------------------------------------

# Running tests

`cd test`

## Bittrex
`pytest bittrex_test.py --apikey=<APIKEY> --secret=<APISECRET>`

## Poloniex
`pytest poloniex_test.py --apikey=<APIKEY> --secret=<APISECRET>`

## Wex

`pytest wex_test.py --apikey=<APIKEY> --secret=<APISECRET>`

____________________________________________________________

## Contributing

1. Fork it (https://github.com/indiciumfund/cryptotik/fork)
2. Study how it's implemented
3. Create your feature branch (`git checkout -b my-new-feature`)
4. Commit your changes (`git commit -am 'Add some feature'`)
5. Push to the branch (`git push origin my-new-feature`)
6. Create a new Pull Request
