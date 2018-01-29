# -*- coding: utf-8 -*-

import hmac
import hashlib
import time
import requests
from cryptotik.common import APIError, headers, ExchangeWrapper
from re import findall
from decimal import Decimal


class TheRock(ExchangeWrapper):

    url = 'https://api.therocktrading.com/v1/'
    delimiter = ""
    headers = headers

    def __init__(self, apikey=None, secret=None, timeout=None):
        '''initialize bittrex class'''

        if apikey and secret:
            self.apikey = apikey.encode("utf-8")
            self.secret = secret.encode("utf-8")

    try:
        assert timeout is not None
    except:
        timeout = (8, 15)

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        return "".join(findall(r"[^\W\d_]+|\d+", pair)).upper()

    @classmethod
    def api(cls, url):
        '''call api'''

        try:
            result = requests.get(url, headers=cls.headers, timeout=3)
            assert result.status_code == 200
            return result.json()
        except requests.exceptions.RequestException as e:
            print("Error!", e)

    @classmethod
    def get_market_ticker(cls, pair):
        '''returns simple current market status report'''

        return cls.api(cls.url + "funds/" + cls.format_pair(pair) + "/ticker")

    @classmethod
    def get_market_trade_history(cls, pair, limit=10):
        '''get market trade history'''

        return cls.api(cls.url + "funds/" + cls.format_pair(pair) + "/trades" + 
                                "?per_page={}".format(limit))['trades']

    @classmethod
    def get_market_orders(cls, pair):
        '''return order book for the market'''

        return cls.api(cls.url + "funds/" + cls.format_pair(pair) + "/orderbook")

    @classmethod
    def get_market_spread(cls, pair):
        '''return first buy order and first sell order'''

        order_book = cls.get_market_orders(pair)

        ask = order_book["asks"][0]['price']
        bid = order_book["bids"][0]['price']

        return Decimal(ask) - Decimal(bid)

    @classmethod
    def get_market_depth(cls, pair):
        '''return sum of all bids and asks'''

        ob = cls.get_market_orders(pair)
        return {"bids": Decimal(ob['bids'][-1]['depth']),
                "asks": Decimal(ob['asks'][-1]['depth'])}

    @classmethod
    def get_markets(cls, filter=None):
        '''Find supported markets on this exchange,
            use <filter> if needed'''

        r = cls.api(cls.url + "funds")['funds']
        pairs = [i["id"].lower() for i in r]
        if filter:
            pairs = [p for p in pairs if filter in p]
        return pairs

    @classmethod
    def get_market_volume(cls, pair):
        ''' return volume of last 24h'''

        return cls.get_market_ticker(cls.format_pair(pair))["volume"]

    def private_api(self, url, http_method='GET', params={}):
        '''handles private api methods'''

        if not self.apikey or not self.secret:
            raise ValueError("A Key and Secret needed!")

        nonce = str(self.get_nonce())
        if params:
            url += "?" + requests.compat.urlencode(sorted(params.items()))
        nonce_plus_url = str(nonce) + url
        signature = hmac.new(self.secret,
                            nonce_plus_url.encode("utf-8"),
                            hashlib.sha512).hexdigest()
        head = {"Content-Type": "application/json",
                "X-TRT-KEY": self.apikey,
                "X-TRT-SIGN": signature,
                "X-TRT-NONCE": nonce}

        result = requests.request(http_method, url, headers=head)
        #assert result.status_code == 200, {'error: ' + str(result.json())}
        return result.json()

    def get_nonce(self):
        '''return nonce integer'''

        nonce = getattr(self, '_nonce', 0)
        if nonce:
            nonce += 1
        # If the unix time is greater though, use that instead (helps low
        # concurrency multi-threaded apps always call with the largest nonce).
        self._nonce = max(int(time.time()), nonce)
        return self._nonce

    def get_balances(self):
        """get all balances from your account"""

        balances = self.private_api(self.url + "balances")
        return [i for i in balances['balances'] if i["trading_balance"] != 0.0]

    def get_deposit_address(self, currency):
        ''' get deposit address for <currency> '''

        return self.private_api(self.url + "currencies/" + currency.upper() +
                                "/addresses",
                                http_method='GET', 
                                params={'unused': 'true'})

    def buy(self, pair, price, quantity):
        '''creates buy order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "funds/" 
                                + self.format_pair(pair) + "/orders",
                                params={'fund_id': self.format_pair(pair),
                                    'side': 'buy', 'amount': quantity,
                                    'price': price},
                                http_method='POST')

    def sell(self, pair, price, quantity):
        '''creates sell order for <pair> at <price> for <quantity>'''
        
        return self.private_api(self.url + "funds/" 
                                + self.format_pair(pair) + "/orders",
                                params={'fund_id': self.format_pair(pair),
                                    'side': 'sell', 'amount': quantity,
                                    'price': price},
                                http_method='POST')

    def withdraw(self, coin, amount, address):
        '''withdraw <coin> <amount> to <address> with <address_tag> if needed'''
          
        return self.private_api(self.url + "atms/withdraw",
                                params={'currency': coin.upper(),
                                        'destination_address': address, 
                                        'amount': amount},
                                http_method='POST')

    def get_withdraw_history(self, currency=None):
        '''Retrieves withdrawal history.'''
        
        if currency:
            transactions = self.private_api(self.url + "transactions",
                                        params={'currency': currency.upper()})["transactions"] 
        else:
            transactions = self.private_api(self.url + "transactions")["transactions"]

        return [i for i in transactions if i["type"] == "withdraw"]

    def get_deposit_history(self, currency=None):
        '''Retreive deposit history.'''
        
        if currency:
            transactions = self.private_api(self.url + "transactions",
                                        params={'currency': currency})["transactions"] 
        else:
            transactions = self.private_api(self.url + "transactions")["transactions"]

        return [i for i in transactions if i["type"] == "atm_payment"]

    def get_open_orders(self, pair=None):
        '''get open orders for <pair>
           or all open orders if called without an argument.'''
        
        if not pair:
            all_pairs=[]
            for market in self.get_markets():
                all_pairs += self.private_api(self.url + "funds/" + 
                                            self.format_pair(market) + "/orders")
                return all_pairs
        else:
            return self.private_api(self.url + "funds/" + self.format_pair(pair) 
                                    + "/orders")["orders"]

    def get_order(self, symbol, order_id):
        """retrieve a single order by orderId."""
        
        return self.private_api(self.url + "funds/" + symbol + "/orders/" + order_id,
                                http_method='GET')

    def cancel_order(self, order_id, symbol):
        """cancel order with <order_id> for <symbol>"""
        
        return self.private_api(self.url + "funds/" + symbol + 
                                "/orders/" + order_id,
                                http_method='DELETE')

    def cancel_all_orders(self, symbol):
        """cancel all orders for <symbol> """
            
        return self.private_api(self.url + "funds/" + symbol + 
                                "/orders/remove_all",
                                http_method='DELETE')