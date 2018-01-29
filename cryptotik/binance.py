# -*- coding: utf-8 -*-

''' Binance exchange '''

import hmac
import hashlib
import time
import requests
from decimal import Decimal
from cryptotik.common import APIError, headers, ExchangeWrapper


class Binance(ExchangeWrapper):
    ''' Binance exchange class'''

    name = "binance"
    url = 'https://api.binance.com/'
    delimiter = ""
    headers = headers
    taker_fee, maker_fee = 0.001, 0.001

    def __init__(self, apikey=None, secret=None, timeout=None):
        '''initialize object from Hitbtc class'''

        if apikey and secret:
            self.apikey = apikey
            self.secret = bytes(secret.encode("utf-8"))
    try:
        assert timeout is not None
    except:
        timeout = (8, 15)

    @classmethod
    def api(cls, url, params):
        '''call api'''

        try:
            result = requests.get(url, params=params, headers=cls.headers, timeout=3)
            assert result.status_code == 200, {'error: ' + str(result.json())}
            return result.json()
        except requests.exceptions.RequestException as e:
            raise APIError(e)

    @classmethod
    def format_pair(cls, pair):
        '''Format the pair argument to format understood by remote API.'''

        pair = pair.replace("-", cls.delimiter).upper()
        return pair

    @classmethod
    def get_market_ticker(cls, pair):
        '''returns simple current market status report'''
        params=(('symbol', cls.format_pair(pair)),)
        return cls.api(cls.url + "api/v1/ticker/24hr", params)

    @classmethod
    def get_market_trade_history(cls, pair, limit=100):
        '''get market trade history'''

        return cls.api(cls.url + "api/v1/aggTrades", 
                        params=(('symbol', cls.format_pair(pair)), ('limit', limit),))

    @classmethod
    def get_summaries(cls):
        '''get summary of all active markets'''

        return cls.api(cls.url + 'api/v1/ticker/24hr',
                       params=())

    @classmethod
    def get_market_orders(cls, pair, limit=100):
        '''return sum of all bids and asks'''
        params=(('symbol', cls.format_pair(pair)), ('limit', limit),)

        return cls.api(cls.url + 'api/v1/depth', params)

    @classmethod
    def get_market_spread(cls, pair):
        '''return first buy order and first sell order'''

        order_book = cls.get_market_orders(cls.format_pair(pair))

        ask = order_book['asks'][0][0]
        bid = order_book['bids'][0][0]
        
        return Decimal(ask) - Decimal(bid)

    @classmethod
    def get_market_depth(cls, pair):
        '''return sum of all bids and asks'''

        order_book = cls.get_market_orders(cls.format_pair(pair))
        asks = sum([Decimal(i[1]) for i in order_book['asks']])
        bid = sum([Decimal(i[1]) for i in order_book['bids']])

        return {"bids": bid, "asks": asks}

    @classmethod
    def get_markets(cls, filter=None):
        '''Find supported markets on this exchange,
            use <filter> if needed'''

        r = cls.api(cls.url + "api/v1/ticker/allPrices", params=())
        pairs = [i["symbol"].lower() for i in r]
        if filter:
            pairs = [p for p in pairs if filter in p]
        return pairs

    @classmethod
    def get_market_volume(cls, pair):
        ''' return volume of last 24h'''

        return cls.get_market_ticker(cls.format_pair(pair))["volume"]

    def private_api(self, url, params={}, http_method='GET'):
        '''handles private api methods'''

        if not self.apikey or not self.secret:
            raise ValueError("A Key and Secret needed!")

        query = requests.compat.urlencode(sorted(params.items()))
        query += "&timestamp={}".format(int(time.time() * 1000))
        signature = hmac.new(self.secret, query.encode("utf-8"),
                            hashlib.sha256).hexdigest()
        query += "&signature={}".format(signature)
        result = requests.request(http_method,
                                url + "?" + query,
                                headers={"X-MBX-APIKEY": self.apikey})
        assert result.status_code == 200, {'error: ' + str(result.json())}
        return result.json()

    def get_balances(self):
        """get all balances from your account"""

        balances = self.private_api(self.url + "api/v3/account")["balances"]

        return [i for i in balances if i["free"] != '0.00000000']

    def buy(self, pair, price, quantity):
        '''creates buy order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "api/v3/order",
                                params={'symbol': self.format_pair(pair),
                                    'side': 'BUY', 'type': 'limit',
                                    'timeInForce': 'GTC', 'quantity': quantity,
                                    'price': price},
                                http_method='POST')

    def get_deposit_address(self, currency):
        ''' get deposit address for <currency> '''
        
        return self.private_api(self.url + "/wapi/v3/depositAddress.html",
                                params={'asset': currency.upper()},
                                http_method='GET') 

    def get_open_orders(self, pair=None):
        '''get open orders for <pair>
           or all open orders if called without an argument.'''

        if pair:
            return self.private_api(self.url + "/api/v3/openOrders", 
                                    params={'symbol': pair.upper()})
        return self.private_api(self.url + "/api/v3/openOrders")

    def sell(self, pair, price, quantity):
        '''creates sell order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "api/v3/order",
                                params={'symbol': self.format_pair(pair),
                                    'side': 'SELL', 'type': 'limit',
                                    'timeInForce': 'GTC', 'quantity': quantity,
                                    'price': price},
                                http_method='POST')

    def withdraw(self, coin, amount, address, address_tag=None):
        '''withdraw <coin> <amount> to <address> with <address_tag> if needed'''

        if address_tag:
            return self.private_api(self.url + "/wapi/v3/withdraw.html",
                                    params={'asset': coin.upper(),
                                            'address': address,
                                            'addressTag': address_tag,
                                            'name': coin.upper(),
                                            'amount': amount},
                                    http_method='POST')
        return self.private_api(self.url + "/wapi/v3/withdraw.html",
                                params={'asset': coin.upper(),
                                        'address': address, 
                                        'amount': amount},
                                http_method='POST')

    def get_withdraw_history(self, currency=None):
        '''Retrieves withdrawal history.'''

        if currency:
            transactions = self.private_api(self.url + "/wapi/v3/withdrawHistory.html", 
                                        params={"asset": currency.upper()})
        else:
            transactions = self.private_api(self.url + 
                                "/wapi/v3/withdrawHistory.html")

        return [i for i in transactions["withdrawList"]]

    def get_deposit_history(self, currency=None):
        '''Retreive deposit history.'''

        if currency:
            transactions = self.private_api(self.url + "/wapi/v3/depositHistory.html", 
                                            params={"asset": currency.upper()})
        else:
            transactions = self.private_api(self.url + "/wapi/v3/depositHistory.html")
        
        return [i for i in transactions["depositList"]]

    def get_order(self, symbol, order_id):
        """retrieve a single order by orderId."""

        return self.private_api(self.url + "/api/v3/order",
                                params={"symbol": symbol,
                                "orderId": order_id},
                                http_method='GET')

    def cancel_order(self, order_id, symbol):
        """cancel order with <order_id> for <symbol>"""

        return self.private_api(self.url + "/api/v3/order",
                                params={"symbol": symbol,
                                "orderId": order_id},
                                http_method='DELETE')

    def cancel_all_orders(self):
    
        for order in self.get_open_orders():
            self.cancel_order(order['orderId'], order['symbol'])

    def get_nonce(self):
        pass
