# -*- coding: utf-8 -*-

''' Hitbct exchange '''

import time
import requests
from decimal import Decimal
from cryptotik.common import APIError, headers, ExchangeWrapper


class Hitbtc(ExchangeWrapper):
    ''' Hitbct exchange '''

    url = 'https://api.hitbtc.com/api/2/'
    delimiter = ""
    headers = headers

    api_session = requests.Session()

    def __init__(self, apikey=None, secret=None, timeout=None):
        '''initialize object from Hitbtc class'''

        if apikey and secret:
            self.apikey = apikey.encode("utf-8")
            self.secret = secret.encode("utf-8")
    try:
        assert timeout is not None
    except:
        timeout = (8, 15)

    def get_nonce(self):
        '''return nonce integer'''

        nonce = getattr(self, '_nonce', 0)
        if nonce:
            nonce += 1
        # If the unix time is greater though, use that instead (helps low
        # concurrency multi-threaded apps always call with the largest nonce).
        self._nonce = max(int(time.time()), nonce)
        return self._nonce

    @classmethod
    def format_pair(cls, pair):
        '''Format the pair argument to format understood by remote API.'''

        pair = pair.replace("-", cls.delimiter).upper()
        return pair

    @classmethod
    def api(cls, url, params={}):
        '''call api'''

        try:
            result = requests.get(url, params=params, headers=cls.headers, timeout=3)
            assert result.status_code == 200, {'error: ' + str(result.json()['error'])}
            return result.json()
        except requests.exceptions.RequestException as e:
            raise APIError(e)

    @classmethod
    def get_market_ticker(cls, pair):
        '''returns simple current market status report'''

        return cls.api(cls.url + "public/"+ "ticker/" + cls.format_pair(pair))

    @classmethod
    def get_market_trade_history(cls, pair, limit=1000):
        '''get market trade history'''

        return cls.api(cls.url + "public/trades/" + cls.format_pair(pair), 
                        params={'limit': limit})

    @classmethod
    def get_market_orders(cls, pair):
        '''return order book for the market'''

        return cls.api(cls.url + "public/orderbook/" + cls.format_pair(pair))

    @classmethod
    def get_market_spread(cls, pair):
        '''return first buy order and first sell order'''

        order_book = cls.get_market_orders(cls.format_pair(pair))

        ask = order_book['ask'][0]['price']
        bid = order_book['bid'][0]['price']

        return Decimal(ask) - Decimal(bid)


    @classmethod
    def get_markets(cls):
        '''Find supported markets on this exchange'''

        r = cls.api(cls.url + "public/" + "symbol")

        pairs = [i["id"].lower() for i in r]
        return pairs

    @classmethod
    def get_market_volume(cls, pair):
        ''' return volume of last 24h'''

        return cls.get_market_ticker(cls.format_pair(pair))["volume"]

    @classmethod
    def get_market_depth(cls, pair):
        '''return sum of all bids and asks'''

        order_book = cls.get_market_orders(cls.format_pair(pair))
        asks = sum([Decimal(i['size']) for i in order_book['ask']])
        bid = sum([Decimal(i['size']) for i in order_book['bid']])

        return {"bids": bid, "asks": asks}

    def private_api(self, url, params={}, http_method='GET'):
        '''handles private api methods'''

        if not self.apikey or not self.secret:
            raise ValueError("A Key and Secret needed!")

        if http_method == 'GET':
            result = requests.get(url, auth=(self.apikey, self.secret))
        elif http_method == 'POST':
            if not bool(params):
                raise AttributeError("Data parameters required for POST request")
            result = requests.post(url, data=params , auth=(self.apikey, self.secret))
        elif http_method == 'PUT':
            result = requests.put(url, auth=(self.apikey, self.secret))
        elif http_method == 'DELETE':
            result = requests.delete(url, auth=(self.apikey, self.secret))
        assert result.status_code == 200, {'error: ' + str(result.json()['error'])}
        return result.json()

    def get_balances(self):
        """get all balances from your account"""

        balances = self.private_api(self.url + "trading/balance")

        return [i for i in balances if i["available"] != '0']

    def get_withdraw_history(self, currency):
        '''Retrieves withdrawal history.'''

        transactions = self.private_api(self.url + "account/transactions", 
                                        params={"currency": currency.upper()})
        return [i for i in transactions if i["type"] == 'payout']
    
    def withdraw(self, coin, amount, address):
        '''withdraw <coin> <amount> to <address>'''

        return self.private_api(self.url + "account/crypto/withdraw",
                                params={"currency": coin.upper(),
                                        "amount": amount,
                                        "address": address},
                                http_method='POST')

    def get_order(self, order_id):
        ''' Retreive a single order by it's ID '''

        return self.private_api(self.url + "history/order/" + order_id + "/trades")

    def sell(self, pair, price, quantity):
        '''creates sell order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "order",
                                params={'symbol': self.format_pair(pair),
                                        'side': 'sell', 'quantity': quantity,
                                        'price': price},
                                http_method='POST')

    def cancel_all_orders(self):
        '''cancel all active orders'''

        return self.private_api(self.url + "order", http_method='DELETE')

    def cancel_order(self, clientOrderId):
        '''cancels order with id <clientOrderId>'''

        return self.private_api(self.url + "order/" + clientOrderId,
                                http_method='DELETE')

    def get_deposit_history(self, currency):
        '''Retreive deposit history.'''

        transactions = self.private_api(self.url + "account/transactions", 
                                            params={"currency": currency.upper()})
        return [i for i in transactions if i["type"] == 'payin']

    def get_open_orders(self, pair=None):
        '''get open orders for <pair>
           or all open orders if called without an argument.'''

        if pair:
            return self.private_api(self.url + "order", 
                                    params={'symbol': pair.upper()})
        return self.private_api(self.url + "order")

    def get_deposit_address(self, currency):
        ''' get deposit address for <currency> '''

        return self.private_api(self.url + "account/crypto/address/" + currency.upper())

    def buy(self, pair, price, quantity):
        '''creates buy order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "order",
                                params={'symbol': self.format_pair(pair),
                                    'side': 'buy', 'quantity': quantity,
                                    'price': price},
                                http_method='POST')
