from .common import APIError, headers
import datetime, time
import requests

class Poloniex:

    url = 'https://poloniex.com/'
    public_commands = ["returnTicker", "returnOrderBook", "returnTradeHistory", "returnChartData", "return24hVolume", "returnLoanOrders"]
    time_limit = datetime.timedelta(days=365) # Poloniex will provide just 1 year of data
    delimiter = "_"
    case = "upper"

    headers = headers

    @classmethod
    def format_pair(cls, pair):
        '''formats pair string in format understood by remote API'''
        
        if not cls.delimiter in pair and len(pair) > 5:
            pair = pair.replace("-", cls.delimiter)

        if not pair.isupper():
            return pair.upper()
        else:
            return pair

    @classmethod
    def api(cls, params):
        '''so far only public methods'''
        
        if params["command"] in cls.public_commands:
            prefix = "public?"
            
            try:
                r = requests.get(cls.url + prefix, params=params, headers=cls.headers, timeout=3)
                return r.json()
            except requests.exceptions.RequestException as e:
                print("Error!", e)
    
    @classmethod
    def get_pairs(cls):

        markets = [i for i in cls.get_market_ticker()]
        base_pairs = set([i.split(cls.delimiter)[0] for i in markets])
        market_pairs = set([i.split(cls.delimiter)[1] for i in markets])

        return {"base": base_pairs, "market_pairs": market_pairs,
                "markets": markets}
    
    @classmethod
    def get_market_ticker(cls, pair=None):
        '''Returns the ticker for all markets'''
        if pair:
            return cls.api({"command": 'returnTicker'})[cls.format_pair(pair)]

        return cls.api({"command": 'returnTicker'})
    
    @classmethod
    def get_market_trade_history(cls, pair, since=None, until=int(time.time())):
        """Requests trade history for >pair< from >since< to >until< selected timeframe expressed in seconds (unix time)\n
            Each request is limited to 50000 trades or 1 year.\n
            If called without arguments, it will requets last 200 trades for the pair."""
              
        query = {"command": "returnTradeHistory", "currencyPair": cls.format_pair(pair)}
        
        if since == None: # default, return 200 last trades
            return cls.api(query)
            
        if since > time.time():
            raise APIError("AYYY LMAO start time is in the future, take it easy.")

        if (datetime.datetime.now() - cls.time_limit).timestamp() <= since:
            query.update({"start": str(since),
                            "end": str(until)}
                            )
            return cls.api(query)
                
        else:
            raise APIError('''Poloniex API does no support queries for data older than a year.\n
                                Earilest data we can get is since {0} UTC'''.format((datetime.datetime.now() - cls.time_limit).isoformat())
                                    )
    
    @classmethod    
    def get_full_market_trade_history(cls, pair):
        """get full (maximium) trade history for this pair from one year ago until now, or last 50k trades - whichever comes first."""
        
        start = (datetime.datetime.now() - cls.time_limit).timestamp() + 1
        return cls.get_market_trade_history(cls.format_pair(pair), int(start))  
    
    @classmethod
    def get_loans(cls, coin):
        '''return loan offers for coin'''

        loans = cls.api({"command": 'returnLoanOrders',
                         "currency": cls.format_pair(coin)
                        })
        return {"demands": loans["demands"], "offers": loans["offers"]}
    
    @classmethod
    def get_loan_depth(cls, coin):
        """return loans depth"""

        from decimal import Decimal
        
        loans = cls.get_loans(coin)
        return {"offers": sum([Decimal(i["amount"]) for i in loans["offers"]]),
                "demands": sum([Decimal(i["amount"]) for i in loans["demands"]])
                }

    @classmethod
    def get_market_order_book(cls, pair, depth=999999):
        '''return order book for the market'''

        return cls.api({"command": "returnOrderBook",
                        "currencyPair": cls.format_pair(pair),
                        "depth": depth
                        })
    
    @classmethod
    def get_market_depth(cls, pair):
        '''return sum of all bids and asks'''

        from decimal import Decimal
        
        order_book = cls.get_market_order_book(cls.format_pair(pair))
        asks = sum([Decimal(i[1]) for i in order_book["asks"]])
        bid = sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]])

        return {"bids": bid, "asks": asks} ## bids are expressed in base pair

    @classmethod
    def get_market_spread(cls, pair):
        '''returns market spread'''

        from decimal import Decimal

        order_book = cls.get_market_order_book(cls.format_pair(pair), 1)
        ask = order_book["asks"][0][0]
        bid = order_book["bids"][0][0]

        return Decimal(ask) - Decimal(bid)
    
    @classmethod
    def get_market_volume(cls, pair=None):
        '''Returns the volume for past 24h'''

        q = cls.api({"command": 'return24hVolume'})
        
        if pair != None:
            return q[cls.format_pair(pair)]
        else:    
            return q
    
    @classmethod
    def get_markets_status(cls):
        ''' Returns additional market info for all markets '''

        return cls.api({'command': 'returnCurrencies'})

