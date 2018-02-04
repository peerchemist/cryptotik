import pytest
from cryptotik import Hitbtc
from decimal import Decimal

private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)


def test_format_pair():
    '''test string formating to match API expectations'''

    assert Hitbtc.format_pair("ppc-usd") == "PPCUSD"

def test_get_markets():
    '''test get_markets'''

    assert isinstance(Hitbtc.get_markets(), list)
    assert "ppcusd" in Hitbtc.get_markets()

def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = Hitbtc.get_market_ticker("PPC-USD")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == ['ask', 'bid', 'high', 'last', 'low', 'open', 'symbol', 'timestamp', 'volume', 'volumeQuote']

def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = Hitbtc.get_market_orders("ppc-usd")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["ask"], list)
    assert isinstance(market_orders["bid"], list)

def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = Hitbtc.get_market_trade_history("ppc-usd", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert sorted(trade_history[0].keys()) == sorted(['id', 'price', 'quantity', 'side', 'timestamp'])

def test_get_market_depth():
    '''test get_market_depth'''

    market_depth = Hitbtc.get_market_depth("ppc-usd")

    assert isinstance(market_depth, dict)
    assert isinstance(market_depth["asks"], Decimal)

def test_get_market_spread():
    '''test get_market spread'''

    assert isinstance(Hitbtc.get_market_spread("ppc-usd"), Decimal)

@private
def test_get_balances(apikey, secret):

    hit = Hitbtc(apikey, secret)
    balances = hit.get_balances()

    assert isinstance(balances, list)

@private
def test_get_deposit_address(apikey, secret):

    hit = Hitbtc(apikey, secret)

    assert isinstance(hit.get_deposit_address("ppc"), dict)

@private
def test_get_withdraw_history(apikey, secret):

    hit = Hitbtc(apikey, secret)

    assert isinstance(hit.get_withdraw_history("ppc"), list)

@pytest.mark.xfail
@private
def test_withdraw(apikey, secret):

    print('This is made to fail with <Insufficient funds>' + 
            ', so make sure your testing API key does not allow that.')
    hit = Hitbtc(apikey, secret)

    with pytest.raises(AssertionError):
        hit.withdraw("ppc", 1, 'PpcEaT3Rd0NTsendftMKDAKr331DXgHe3L')

@private
def test_buy_limit(apikey, secret):

    hit = Hitbtc(apikey, secret)

    with pytest.raises(AssertionError):
        hit.buy("ppc_btc", 0.05, 1)


@private
def test_sell_limit(apikey, secret):

    hit = Hitbtc(apikey, secret)

    with pytest.raises(AssertionError):
        hit.sell("ltc_btc", 1, 0.25)

@private
def test_cancel_order(apikey, secret):

    hit = Hitbtc(apikey, secret)

    with pytest.raises(AssertionError):
        hit.cancel_order('invalid')