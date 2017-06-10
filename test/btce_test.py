from cryptotik.btce import Btce
from decimal import Decimal


def test_format_pair():
    '''test string formating to match API expectations'''

    assert Btce.format_pair("ppc-usd") == "ppc_usd"


def test_get_markets():
    '''test get_markets'''

    assert isinstance(Btce.get_markets(), list)
    assert "btc_usd" in Btce.get_markets()


def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = Btce.get_market_ticker("ppc_usd")

    assert isinstance(ticker, dict)
    assert list(ticker["ppc_usd"].keys()) == ['high', 'low', 'avg',
                                              'vol', 'vol_cur', 'last',
                                              'buy', 'sell', 'updated']


def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = Btce.get_market_orders("ppc_usd")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["asks"], list)
    assert isinstance(market_orders["bids"], list)


def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = Btce.get_market_trade_history("ppc_usd", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert list(trade_history[0].keys()) == ['type', 'price', 'amount', 'tid',
                                             'timestamp']


def test_get_market_depth():
    '''test get_market_depth'''

    market_depth = Btce.get_market_depth("ppc_usd")

    assert isinstance(market_depth, dict)
    assert isinstance(market_depth["asks"], Decimal)


def test_get_market_spread():
    '''test get_market spread'''

    assert isinstance(Btce.get_market_spread("ppc_usd"), Decimal)

