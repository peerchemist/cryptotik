import pytest
from cryptotik import Wex
from decimal import Decimal

private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)

wex = Wex()


def test_format_pair():
    '''test string formating to match API expectations'''

    assert wex.format_pair("ppc-usd") == "ppc_usd"


def test_get_base_currencies():

    wex.get_base_currencies()


def test_get_markets():
    '''test get_markets'''

    assert isinstance(wex.get_markets(), list)
    assert "btc_usd" in wex.get_markets()


def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = wex.get_market_ticker("ppc_usd")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == ['avg', 'buy', 'high', 'last', 'low', 'sell', 'updated', 'vol', 'vol_cur']


def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = wex.get_market_orders("ppc_usd")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["asks"], list)
    assert isinstance(market_orders["bids"], list)


def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = wex.get_market_trade_history("ppc_usd", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert sorted(trade_history[0].keys()) == sorted(['type', 'price', 'amount', 'tid',
                                                      'timestamp'])


def test_get_market_depth():
    '''test get_market_depth'''

    market_depth = wex.get_market_depth("ppc_usd")

    assert isinstance(market_depth, dict)
    assert isinstance(market_depth["asks"], Decimal)


def test_get_market_spread():
    '''test get_market spread'''

    assert isinstance(wex.get_market_spread("ppc_usd"), Decimal)


@private
def test_get_balances(apikey, secret):

    wex = Wex(apikey, secret)
    balances = wex.get_balances()

    assert isinstance(balances, dict)
    assert 'btc' in balances.keys()


@private
def test_get_deposit_address(apikey, secret):

    wex = Wex(apikey, secret)

    try:
        with pytest.raises(ValueError):
            wex.get_deposit_address("ltc")
    except:
        assert isinstance(wex.get_deposit_address("ppc"), dict)


@private
def test_cancel_order(apikey, secret):

    wex = Wex(apikey, secret)

    with pytest.raises(ValueError):
        wex.get_open_orders("ppc_btc")


@private
def test_buy_limit(apikey, secret):

    wex = Wex(apikey, secret)

    with pytest.raises(ValueError):
        wex.buy_limit("ppc_btc", 0.05, 1)


@private
def test_sell_limit(apikey, secret):

    wex = Wex(apikey, secret)

    with pytest.raises(ValueError):
        wex.sell_limit("ltc_btc", 1, 0.25)


@private
def test_get_transaction_history(apikey, secret):

    wex = Wex(apikey, secret)

    assert isinstance(wex.get_transaction_history(), dict)


@pytest.mark.xfail
@private
def test_withdraw(apikey, secret):

    print('This is made to fail with <<api key dont have withdraw permission>>, so make sure your testing API key does not allow that.')
    wex = Wex(apikey, secret)

    with pytest.raises(ValueError):
        wex.withdraw("ppc", 1, 'PpcEaT3Rd0NTsendftMKDAKr331DXgHe3L')
