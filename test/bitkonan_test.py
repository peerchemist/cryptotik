import pytest
from cryptotik.bitkonan import Bitkonan
from decimal import Decimal
from cryptotik.exceptions import APIError

private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)

konan = Bitkonan(pytest.config.getoption("--apikey"), 
            pytest.config.getoption("--secret"))


def test_format_pair():
    '''test string formating to match API expectations'''

    assert konan.format_pair("btc-usd") == "BTC/USD"


def test_get_markets():
    '''test get_markets'''

    assert isinstance(konan.get_markets(), list)
    assert "btc-usd" in konan.get_markets()


def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = konan.get_market_ticker("ETH-BTC")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == ['ask', 'bid', 'high', 'last', 'low', 'open', 'volume']


def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = konan.get_market_orders("btc-usd")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["ask"], list)
    assert isinstance(market_orders["bid"], list)


def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = konan.get_market_trade_history("btc-usd", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert sorted(trade_history[0].keys()) == sorted(['btc', 'maker', 'taker', 'tid', 'time', 'total', 'tradetype', 'usd'])


@private
def test_get_balances(apikey, secret):

    balances = konan.get_balances()
    assert isinstance(balances, list)

@private
def test_cancel_order(apikey, secret):

    with pytest.raises(APIError):
        konan.cancel_order(0)