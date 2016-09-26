# cryptotik
Standardized common API for several cryptocurrency exchanges

## Install

`pip install git+git://github.com/peerchemist/cryptotik.git`

## Examples

`from cryptotik import Btce, Bittrex, Poloniex`

`Btce.get_market_ticker("ppc-btc")`

`Bittrex.get_markets()`

`Poloniex.get_markets()`

`Poloniex.get_market_order_book("btc-nxt")`

You should get quite similar results from methods that are named the same.

----------------------------------------------------------

This is initial code dump, there is more left to do.