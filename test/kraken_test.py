import pytest
from cryptotik.kraken import Kraken
from decimal import Decimal
import time


private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)

kraken = Kraken(pytest.config.getoption("--apikey"), 
            pytest.config.getoption("--secret"))

def test_format_pair():
    '''test string formating to match API expectations'''

    assert kraken.format_pair("bch-eur") == "BCHEUR"

def test_get_markets():
    '''test get_markets'''

    assert isinstance(kraken.get_markets(), list)
    assert "BCHEUR" in kraken.get_markets()

def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = kraken.get_market_ticker("BCH-EUR")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == ['a', 'b', 'c', 'h', 'l', 'o', 'p', 't', 'v']

def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = kraken.get_market_orders("bch-eur")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["asks"], list)
    assert isinstance(market_orders["bids"], list)

def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = kraken.get_market_trade_history("bch-eur", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert isinstance(trade_history[0], list)

def test_get_market_depth():
    '''test get_market_depth'''

    market_depth = kraken.get_market_depth("bch-eur")

    assert isinstance(market_depth, dict)
    assert isinstance(market_depth["asks"], Decimal)

def test_get_market_spread():
    '''test get_market spread'''

    assert isinstance(kraken.get_market_spread("bch-eur"), Decimal)

@private
def test_get_balances(apikey, secret):

    
    balances = kraken.get_balances()

    assert isinstance(balances, dict)

@private
def test_get_deposit_address(apikey, secret):
    

    assert isinstance(kraken.get_deposit_address("bch"), str)

@private
def test_get_withdraw_history(apikey, secret):
    
    

    assert isinstance(kraken.get_withdraw_history("bch"), list)

@private
def test_withdraw(apikey, secret):
    
    print('This is made to fail because of fake address')
    

    response = kraken.withdraw("eur", 0.01, 'fake_address')
    assert response['error'][0] == 'EFunding:Unknown withdraw key'

@private
def test_buy(apikey, secret):
    
    

    response = kraken.buy_limit("bch-eur", 0.0005, 0.0005)
    assert response['error'][0] == 'EOrder:Invalid price:BCHEUR price can only be specified up to 1 decimals.'

@private
def test_sell_limit(apikey, secret):
    
    

    response = kraken.sell_limit("bch-eur", 0.0005, 0.0005)
    assert response['error'][0] == 'EOrder:Invalid price:BCHEUR price can only be specified up to 1 decimals.'


@private
def test_cancel_order(apikey, secret):
    
    

    response = kraken.cancel_order('invalid')
    assert response['error'][0] == 'EOrder:Invalid order'