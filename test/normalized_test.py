import pytest
from decimal import Decimal
import time
import importlib
import re
from cryptotik.exceptions import APIError

Exchange = pytest.config.getoption("--exchange")
ExchangeClass = getattr(importlib.import_module("cryptotik." + Exchange.lower()), Exchange + "Normalized")

exchange = ExchangeClass(pytest.config.getoption("--apikey"), 
            pytest.config.getoption("--secret"))

def test_get_markets():
    '''test get_markets'''
    '''
    :params:
        -
    :return: 
        list -> str
        example: ['ltc-eur', 'ppc-btc', 'ltc-usd']
    '''

    assert isinstance(exchange.get_markets(), list)
    assert re.match("[\$a-z]{2,5}-[a-z]{2,5}", exchange.get_markets()[1])
    
def test_get_market_ticker():
    '''test get_market_ticker'''
    '''
    :params:
        pair: str
    :return: 
        dict['ask': float, 'bid': float, 'last': float]
    '''

    ticker = exchange.get_market_ticker("ltc-btc")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == ['ask', 'bid', 'last']

def test_get_market_orders():
    '''test get_market_orderbook'''
    '''
    :params:
        pair: str, limit: int
    :return:
        dict['bids': list[price, quantity],
                'asks': list[price, quantity]
            ]
    bids[0] should be first next to the spread
    asks[0] should be first next to the spread
    '''

    market_orders = exchange.get_market_orders("ltc-btc")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["asks"], list)
    assert isinstance(market_orders["asks"][0], list)
    assert len(market_orders["asks"][0]) == 2
    

def test_get_market_trade_history():
    '''test get_market_trade_history'''
    '''
    :params:
        pair: str, limit: int
    :return:
        list -> dict['timestamp': datetime.datetime,
                    'is_sale': bool,
                    'rate': float,
                    'amount': float,
                    'trade_id': any]
    '''

    trade_history = exchange.get_market_trade_history("ltc-btc", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert isinstance(trade_history[0], dict)
    assert sorted(trade_history[0].keys()) == ['amount', 'is_sale', 'rate', 'timestamp', 'trade_id']

def test_get_market_depth():
    '''test get_market_depth'''
    '''
        :params:
            pair: str
        :return:
            dict['bids': Decimal, 'asks': Decimal]
        bids are to be expressed in the base_currency
        asks are to be expressed in the quote currency
        '''

    market_depth = exchange.get_market_depth("ltc-btc")

    assert isinstance(market_depth, dict)
    assert isinstance(market_depth["asks"], Decimal)

def test_get_market_spread():
    '''test get_market spread'''
    '''
        :params:
            pair: str
        :return:
            Decimal
        '''

    assert isinstance(exchange.get_market_spread("ltc-btc"), Decimal)

def test_get_market_sell_orders():
    '''
    :return:
        list[price, quantity]
    '''

    assert isinstance(exchange.get_market_sell_orders("ltc-btc"), list)

def test_get_market_buy_orders():
    '''
    :return:
        list[price, quantity]
    '''

    assert isinstance(exchange.get_market_buy_orders("ltc-btc"), list)
