# cryptotik
Standardized common API for several cryptocurrency exchanges.

## Install

`pip install git+git://github.com/peerchemist/cryptotik.git`

## Examples

Right now library supports: Wex.nz, Poloniex.com and Bittrex.com; with elementary support for: TheRockTrading, HitBtc and Livecoin.

`from cryptotik import Wex, Bittrex, Poloniex`

You only need to learn commands once, for example `get_markets` will work anywhere:

`Bittrex.get_markets()`

`Poloniex.get_markets()`

`Wex.get_markets()`

and will yield similar results. However parsing and interpreting them is left to user.

## More examples

`Wex.get_market_ticker("ppc-btc")`

`Poloniex.get_market_order_book("btc-nxt")`

`Bittrex.get_market_depth("btc-maid")`

## Private API methods (the ones that require authentication)

Library also supports private API methods for Poloniex and Bittrex, 
to use them you need to make class instance though with your API credentials.

`polo = Poloniex(yourkey, yoursecret)`

`polo.get_balances()`

`polo.withdraw(<coin>, <amount>, <address>)`

Same goes for Bittrex:

`btrx = Bittrex(yourkey, yoursecret)`

`btrx.get_balances()`

`btrx.withdraw(<coin>, <amount>, <address>)`

----------------------------------------------------------

# Running tests

`cd test`

## Bittrex
`pytest bittrex_test.py --apikey=<APIKEY> --secret=<APISECRET>`

## Poloniex
`pytest poloniex_test.py --apikey=<APIKEY> --secret=<APISECRET>`

