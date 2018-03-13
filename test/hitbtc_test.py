import pytest
from cryptotik import Hitbtc
from decimal import Decimal
from cryptotik.exceptions import APIError

private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)

hit = Hitbtc(pytest.config.getoption("--apikey"), 
            pytest.config.getoption("--secret"))

def test_format_pair():
    '''test string formating to match API expectations'''

    assert hit.format_pair("ppc-usd") == "PPCUSD"

def test_get_markets():
    '''test get_markets'''

    assert isinstance(hit.get_markets(), list)
    assert "ppcusd" in hit.get_markets()

def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = hit.get_market_ticker("PPC-USD")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == ['ask', 'bid', 'high', 'last', 'low', 'open', 'symbol', 'timestamp', 'volume', 'volumeQuote']

def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = hit.get_market_orders("ppc-usd")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["ask"], list)
    assert isinstance(market_orders["bid"], list)


def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = hit.get_market_trade_history("ppc-usd", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert sorted(trade_history[0].keys()) == sorted(['id', 'price', 'quantity', 'side', 'timestamp'])


@private
def test_get_balances(apikey, secret):

    balances = hit.get_balances()

    assert isinstance(balances, list)


@private
def test_get_deposit_address(apikey, secret):


    assert isinstance(hit.get_deposit_address("ppc"), dict)

@private
def test_get_withdraw_history(apikey, secret):

    assert isinstance(hit.get_withdraw_history("ppc"), list)

@private
def test_withdraw(apikey, secret):

    with pytest.raises(APIError):
        hit.withdraw("ppc", 1, 'PpcEaT3Rd0NTsendftMKDAKr331DXgHe3L')


@private
def test_buy_limit(apikey, secret):

    with pytest.raises(APIError):
        hit.buy_limit("ppc-btc", 0.05, 1)


@private
def test_sell_limit(apikey, secret):


    with pytest.raises(APIError):
        hit.sell_limit("ltc_btc", 1, 0.25)


@private
def test_cancel_order(apikey, secret):


    with pytest.raises(APIError):
        hit.cancel_order('invalid')