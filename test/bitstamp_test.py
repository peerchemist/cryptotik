import pytest
from cryptotik import Bitstamp
from decimal import Decimal

private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)

stamp = Bitstamp()


def test_format_pair():
    '''test string formating to match API expectations'''

    assert stamp.format_pair("btc-eur") == "btceur"


def test_get_markets():
    '''test get_markets'''

    assert isinstance(stamp.get_markets(), list)
    assert "ltcbtc" in stamp.get_markets()


def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = stamp.get_market_ticker("xrpbtc")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == sorted(['last', 'high', 'low', 'vwap', 'volume', 'bid', 'ask', 'timestamp', 'open'])


def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = stamp.get_market_orders("btceur")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["bids"], list)
    assert isinstance(market_orders["asks"], list)


def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = stamp.get_market_trade_history("ethusd")

    assert isinstance(trade_history, list)
    assert sorted(trade_history[0].keys()) == sorted(['tid', 'date',
                                               'price', 'amount',
                                               'type'])


def test_get_market_depth():
    '''test get_market_depth'''

    market_depth = stamp.get_market_depth("ethbtc")

    assert isinstance(market_depth, dict)
    assert isinstance(market_depth["asks"], Decimal)


def test_get_market_spread():
    '''test get_market spread'''

    assert isinstance(stamp.get_market_spread("btcusd"), Decimal)


@private
def test_get_balances(apikey, secret):
    '''test get_balances'''

    stamp = Bitstamp(apikey, secret)
    balances = stamp.get_balances()

    raise NotImplementedError


@private
def test_get_open_orders(apikey, secret):
    '''test get_balances'''

    stamp = Bitstamp(apikey, secret)
    orders = stamp.get_open_orders()

    raise NotImplementedError


@private
def test_get_deposit_address(apikey, secret):
    '''test get_deposit_address'''

    stamp = Bitstamp(apikey, secret)

    assert isinstance(stamp.get_deposit_address("btc"), str)


@private
def test_buy(apikey, secret):
    '''test buy'''

    stamp = Bitstamp(apikey, secret)

    raise NotImplementedError


@private
def test_sell(apikey, secret):
    '''test buy'''

    stamp = Bitstamp(apikey, secret)

    raise NotImplementedError


@private
def test_get_order_history(apikey, secret):
    '''test get_order_history'''

    stamp = Bitstamp(apikey, secret)
    order_history = stamp.get_order_history()

    raise NotImplementedError


@private
def test_get_withdrawal_history(apikey, secret):
    '''test get_withdrawal_history'''

    stamp = Bitstamp(apikey, secret)
    raise NotImplementedError


@private
def test_get_deposit_history(apikey, secret):
    '''test get_withdrawal_history'''

    stamp = Bitstamp(apikey, secret)
    raise NotImplementedError
