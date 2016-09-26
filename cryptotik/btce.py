import requests
from .common import APIError, headers

class Btce:

    url = 'https://btc-e.com/api/3/'
    delimiter = "_"
    case = "lower"
    headers = headers

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        if isinstance(pair, list):
            return pair
            
        pair = pair.replace("-", cls.delimiter)

        if not pair.islower():
            return pair.lower()
        else:
            return pair

    @classmethod
    def api(cls, command):
        r = requests.get(cls.url + command, headers=cls.headers)
        return r.json()
        
    @classmethod
    def get_markets(cls):
        q = cls.api("info")
        return list(q['pairs'].keys())
    
    @classmethod
    def get_market_ticker(cls, pair):
        """return ticker for market"""
        
        pair = cls.format_pair(pair)
        return cls.api("ticker" + "/" + pair)
    
    @classmethod
    def get_markets_ticker(cls):
        """return ticker for all pairs"""

        pair = "-".join(cls.get_markets())
        return cls.api("ticker" + "/" + pair)

    @classmethod
    def get_market_orders(cls, pair, depth=None):
        """returns market depth on selected pair"""
        
        pair = cls.format_pair(pair)

        if depth == None:
            return cls.api("depth" + "/" + pair)[pair]
        
        if depth > 2000:
            raise ValueError("Btce API allows maximum depth of 2000 orders")
        
        return cls.api("depth" + "/" + pair + "/?limit={0}".format(depth))[pair]
    
    @classmethod
    def get_market_trade_history(cls, pair, limit=1000):
        """get market trade history"""
        
        pair = cls.format_pair(pair)

        if limit > 2000:
            raise APIError("Btc-e API can return only 2000 last trades.")

        if type(pair) != list:
            return cls.api("trades" + "/" + pair + "/?limit={0}".format(limit))[pair]

        if pair == "all": ## returns market history for all pairs with default history size.
            return cls.api("trades" + "/" + "-".join(cls.get_markets() + "/?limit={0}".format(limit)))

        else: ## simply concat pairs in the list
            return cls.api("trades" + "/" + "-".join(pair) + "/?limit={0}".format(limit))
    
    @classmethod    
    def get_market_depth(cls, pair):
        """get market order book depth"""

        from decimal import Decimal

        pair = cls.format_pair(pair)
        order_book = cls.get_market_orders(pair, 2000)
        return {"bids": sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]]), 
                "asks": sum([Decimal(i[1]) for i in order_book["asks"]])}
    
    @classmethod
    def get_market_spread(cls, pair):
        """get market spread"""

        from decimal import Decimal
        pair = cls.format_pair(pair)

        order_book = cls.get_market_orders(pair, 1)
        return Decimal(order_book["asks"][0][0]) - Decimal(order_book["bids"][0][0])

        