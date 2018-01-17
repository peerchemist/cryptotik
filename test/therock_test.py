import pytest
from cryptotik.therock import TheRock
from decimal import Decimal
import time


private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)

def test_format_pair():
    '''test string formating to match API expectations'''

    assert TheRock.format_pair("eth-btc") == "ETHBTC"

def test_get_markets():
    '''test get_markets'''

    assert isinstance(TheRock.get_markets(), list)
    assert "ethbtc" in TheRock.get_markets()

def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = TheRock.get_market_ticker("ETH-BTC")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == ['ask', 'bid', 'close', 'date', 
                                      'fund_id', 'high', 'last', 'low', 
                                      'open', 'volume', 'volume_traded']

def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = TheRock.get_market_orders("eth-btc")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["asks"], list)
    assert isinstance(market_orders["bids"], list)

def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = TheRock.get_market_trade_history("eth-btc", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert sorted(trade_history[0].keys()) == ['amount', 'dark', 
                                            'date', 'fund_id', 'id', 'price', 'side']

def test_get_market_depth():
    '''test get_market_depth'''

    market_depth = TheRock.get_market_depth("eth-btc")

    assert isinstance(market_depth, dict)
    assert isinstance(market_depth["asks"], Decimal)

def test_get_market_spread():
    '''test get_market spread'''

    assert isinstance(TheRock.get_market_spread("eth-btc"), Decimal)

@private
def test_get_balances(apikey, secret):

    rock = TheRock(apikey, secret)
    balances = rock.get_balances()

    assert isinstance(balances, list)

@private
def test_get_deposit_address(apikey, secret):
    time.sleep(1)
    rock = TheRock(apikey, secret)

    assert isinstance(rock.get_deposit_address("btc"), dict)

@private
def test_get_withdraw_history(apikey, secret):
    time.sleep(1)
    rock = TheRock(apikey, secret)

    assert isinstance(rock.get_withdraw_history("btc"), list)

@pytest.mark.xfail
@private
def test_withdraw(apikey, secret):
    time.sleep(1)
    print('This is made to fail because of fake address')
    rock = TheRock(apikey, secret)

    with pytest.raises(AssertionError):
        rock.withdraw("eth", 0.01, 'fake_address')


@private
def test_buy(apikey, secret):
    time.sleep(1)
    rock = TheRock(apikey, secret)
    print('This is made to fail because of small amount')
    with pytest.raises(AssertionError):
        rock.buy("eth-btc", 0.0005, 0.0005)


@private
def test_sell(apikey, secret):
    time.sleep(1)
    rock = TheRock(apikey, secret)

    with pytest.raises(AssertionError):
        rock.sell("eth-btc", 0.0005, 0.0005)

@private
def test_cancel_order(apikey, secret):
    time.sleep(1)
    rock = TheRock(apikey, secret)

    with pytest.raises(AssertionError):
        rock.cancel_order('invalid', 'btc')