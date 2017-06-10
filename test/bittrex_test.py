from cryptotik import Bittrex
from decimal import Decimal


def test_format_pair():
    '''test string formating to match API expectations'''

    assert Bittrex.format_pair("btc_ppc") == "btc-ppc"


def test_get_markets():
    '''test get_markets'''

    assert isinstance(Bittrex.get_markets(), list)
    assert "btc-ltc" in Bittrex.get_markets()


def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = Bittrex.get_market_ticker("btc-ltc")

    assert isinstance(ticker, dict)
    assert list(ticker.keys()) == ['Bid', 'Ask', 'Last']


def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = Bittrex.get_market_orders("btc-ppc", 20)

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["buy"], list)
    assert isinstance(market_orders["sell"], list)


def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = Bittrex.get_market_trade_history("btc-ppc", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert list(trade_history[0].keys()) == ['Id', 'TimeStamp', 'Quantity',
                                             'Price', 'Total', 'FillType',
                                             'OrderType']


def test_get_market_depth():
    '''test get_market_depth'''

    market_depth = Bittrex.get_market_depth("btc-ppc")

    assert isinstance(market_depth, dict)
    assert isinstance(market_depth["asks"], Decimal)


def test_get_market_spread():
    '''test get_market spread'''

    assert isinstance(Bittrex.get_market_spread("btc-vtc"), Decimal)

