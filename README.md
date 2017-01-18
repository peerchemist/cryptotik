# cryptotik
Standardized common API for several cryptocurrency exchanges.

## Install

`pip install git+git://github.com/peerchemist/cryptotik.git`

## Examples

Right now library supports: Btce, Poloniex, Bittrex, TheRockTrading, HitBtc, Livecoin and OKcoin.

`from cryptotik import Btce, Bittrex, Poloniex, TheRock`

You only need to learn commands once, for example `get_markets` will work anywhere

`Bittrex.get_markets()`

`Poloniex.get_markets()`

`Btce.get_markets()`

`TheRock.get_markets()`

and will yield similar results. However parsing and interpreting them is left to user.

## More examples

`Btce.get_market_ticker("ppc-btc")`

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
