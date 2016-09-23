import requests
from .common import APIError, headers

class Bittrex:

    url = 'https://bittrex.com/api/v1.1/'
    delimiter = "-"
    
    headers = headers
    
    @classmethod
    def api(cls, url, params):
        """call api"""
        
        return requests.get(url, params, headers=cls.headers, timeout=3).json()
    
    @classmethod
    def get_pairs(cls):
        '''find out supported markets on this exhange.'''
        
        return cls.api(cls.url + "public" + "/getmarkets", params={})["result"]
    
    @classmethod
    def get_market_ticker(cls, pair):
        '''returns simple current market status report'''
        
        return cls.api(cls.url + "public" + "/getticker", params={"market": pair})
    
    @classmethod
    def get_market_trade_history(cls, pair, depth=200):
        '''returns last 200 trades for the pair'''

        return cls.api(cls.url + "public" + "/getmarkethistory", params={"market": pair,
                                                            "count": depth})["result"]
    
    @classmethod
    def get_market_depth(cls, pair, depth=999999):
        '''returns market depth'''
        
        from decimal import Decimal
        
        order_book = cls.api(cls.url + "public" + "/getorderbook", params={'market': pair, 
                                                        'type': 'both', 
                                                        'depth': depth})["result"]
        
        return {"bids": sum([Decimal(i["Quantity"]) * Decimal(i["Rate"]) for i in order_book["buy"]]), 
                    "asks": sum([Decimal(i["Quantity"]) for i in order_book["sell"]])
                    }
    @classmethod
    def get_market_summary(cls, pair):
        '''return basic market information'''
    
        return cls.api(cls.url + "public" + "/getmarketsummary", params={"market": pair})["result"][0]
    
    @classmethod
    def get_market_spread(cls, pair):
        '''return first buy order and first sell order'''
        
        from decimal import Decimal
        
        d = cls.get_market_summary(pair)
        return Decimal(d["Ask"]) - Decimal(d["Bid"])
        
    