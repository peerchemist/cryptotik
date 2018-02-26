import pytest
from decimal import Decimal
import time
import importlib
from cryptotik.common import APIError

Exchange = pytest.config.getoption("--exchange")
ExchangeClass = getattr(importlib.import_module("cryptotik." + Exchange.lower()), Exchange)

exchange = ExchangeClass(pytest.config.getoption("--apikey"), 
            pytest.config.getoption("--secret"))

def test_get_markets():
    '''test get_markets'''

    assert isinstance(exchange.get_markets(), list)
    assert "ltcbtc" in exchange.get_markets()
    
def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = exchange.get_market_ticker("ltc-btc")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == ['ask', 'bid', 'last']

def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = exchange.get_market_orders("ltc-btc")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["asks"], list)
    assert isinstance(market_orders["bids"], list)

def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = exchange.get_market_trade_history("ltc-btc", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert isinstance(trade_history[0], dict)

def test_get_market_depth():
    '''test get_market_depth'''

    market_depth = exchange.get_market_depth("ltc-btc")

    assert isinstance(market_depth, dict)
    assert isinstance(market_depth["asks"], Decimal)

def test_get_market_spread():
    '''test get_market spread'''

    assert isinstance(exchange.get_market_spread("ltc-btc"), Decimal)
