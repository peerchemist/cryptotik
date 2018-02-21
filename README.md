# cryptotik
Standardized common API for several cryptocurrency exchanges.

[![PyPI](https://img.shields.io/pypi/l/cryptotik.svg?style=flat-square)]()
[![PyPI](https://img.shields.io/pypi/v/cryptotik.svg?style=flat-square)](https://pypi.python.org/pypi/cryptotik/)

## Install

`pip install git+git://github.com/peerchemist/cryptotik.git`

# Supported Exchanges
| Exchange            | API  | Public Methods    | Private Methods    | Normalization| Tests |
|---------------------|------|-------------------|--------------------|--------------|-------|
| www.binance.com     | Done | Done              | Done               | TODO         | Done  |
| [bitkonan.com](https://bitkonan.com/)        | Done | Done              | Done                 | TODO       | Done  |
| www.bitstamp.net    | Done | Done              | Done               | TODO         | Done  |
| [bittrex.com](https://bittrex.com/)         | Done | Done              | Done               | TODO       | Done  |
| www.cryptopia.co.nz | Done | Done              | Done               | TODO         | Done  |
| [hitbtc.com](https://hitbtc.com/)          | Done | Done              | Done                 | TODO       | Done  |
| www.kraken.com      | Done | Done              | Done               | TODO         | Done  |
| [poloniex.com](https://poloniex.com/)        | Done | Done              | Done               | TODO         | Done  |
| [therocktrading.com](https://therocktrading.com/)  | Done | Done              | Done               | TODO         | Done  |
| [wex.nz](https://wex.nz/)              | Done | Done              | Done               | TODO         | Done  |


## Examples

Right now library supports: Wex.nz, Poloniex.com, Bitstamp.com, Kraken.com Bittrex.com, Binance, TheRockTrading, HitBtc with elementary support for Bitkonan and Livecoin.
Library supports other useful features like wrapper around Coinmarketcap.com public API.

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

1. Fork it (https://github.com/peerchemist/cryptotik/fork)
2. Study how it's implemented
3. Create your feature branch (`git checkout -b my-new-feature`)
4. Commit your changes (`git commit -am 'Add some feature'`)
5. Push to the branch (`git push origin my-new-feature`)
6. Create a new Pull Request
