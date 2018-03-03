import pytest
from cryptotik.cryptopia import Cryptopia
from decimal import Decimal
import time
from cryptotik.exceptions import APIError


private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)

cryptopia = Cryptopia(pytest.config.getoption("--apikey"), 
            pytest.config.getoption("--secret"))

def test_format_pair():
    '''test string formating to match API expectations'''

    assert cryptopia.format_pair("ltc-btc") == "LTC_BTC"

def test_get_markets():
    '''test get_markets'''

    assert isinstance(cryptopia.get_markets(), list)
    assert "LTC/BTC" in cryptopia.get_markets()

def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = cryptopia.get_market_ticker("ltc-btc")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == ['ask', 'bid', 'last']

def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = cryptopia.get_market_orders("ltc-btc")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["asks"], list)
    assert isinstance(market_orders["bids"], list)

def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = cryptopia.get_market_trade_history("ltc-btc", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert isinstance(trade_history[0], dict)


@private
def test_get_balances(apikey, secret):
    
    balances = cryptopia.get_balances()

    assert isinstance(balances, list)


@private
def test_get_deposit_address(apikey, secret):
    
    assert isinstance(cryptopia.get_deposit_address("ltc"), str)

@private
def test_get_withdraw_history(apikey, secret):
    
    assert isinstance(cryptopia.get_withdraw_history(), list)

@pytest.mark.xfail
@private
def test_withdraw(apikey, secret):
    
    print('This is made to fail because withdraw amount is below the minimum')
    
    with pytest.raises(APIError):
        cryptopia.withdraw("btc", 0.00, 'fake_address')

@pytest.mark.xfail
@private
def test_buy_limit(apikey, secret):

    with pytest.raises(APIError):
        cryptopia.buy_limit("ltc-btc", 0.0005, 0.0005)

@pytest.mark.xfail
@private
def test_sell_limit(apikey, secret):
    
    with pytest.raises(APIError):
        cryptopia.sell_limit("ltc-btc", 0.0005, 0.0005)

@pytest.mark.xfail
@private
def test_cancel_order(apikey, secret): 

    with pytest.raises(APIError):
        cryptopia.cancel_order('invalid')
