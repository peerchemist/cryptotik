# -*- coding: utf-8 -*-

''' Hitbct exchange '''

import time
import requests
from decimal import Decimal
from cryptotik.common import APIError, headers, ExchangeWrapper


class Hitbtc(ExchangeWrapper):
    ''' Hitbct exchange '''

    url = 'https://api.hitbtc.com/api/2/'
    name = "hitbtc"
    delimiter = ""
    headers = headers

    api_session = requests.Session()

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        '''initialize object from Hitbtc class'''

        if apikey and secret:
            self.apikey = apikey.encode("utf-8")
            self.secret = secret.encode("utf-8")

        if proxy:
            assert proxy.startswith('https'), {'Error': 'Only https proxies supported.'}
        self.proxy = {'https': proxy}

        if not timeout:
            self.timeout = (8, 15)
        else:
            self.timeout = timeout

        self.api_session = requests.Session()

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

    def _verify_response(self, response):

        if response.json()['error']:
            raise APIError(response.json()['error'])

    def api(self, url, params={}):
        '''call api'''

        try:
            result = requests.get(url, params=params, headers=self.headers,
                                  timeout=self.timeout, proxies=self.proxy)
            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        return result.json()

    def private_api(self, url, params={}, http_method='GET'):
        '''handles private api methods'''

        if http_method == 'GET':
            try:
                result = self.api_session.get(url, auth=(self.apikey, self.secret), proxies=self.proxy)
                result.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(e)

        elif http_method == 'POST':
            if not bool(params):
                raise AttributeError("Data parameters required for POST request")
            try:
                result = self.api_session.post(url, data=params, auth=(self.apikey, self.secret))
                result.raise_for_status()

            except requests.exceptions.HTTPError as e:
                print(e)

        elif http_method == 'PUT':
            try:
                result = self.api_session.put(url, auth=(self.apikey, self.secret), proxies=self.proxy)
                result.raise_for_status()

            except requests.exceptions.HTTPError as e:
                print(e)

        elif http_method == 'DELETE':
            try:
                result = self.api_session.delete(url, auth=(self.apikey, self.secret), proxies=self.proxy)
                result.raise_for_status()

            except requests.exceptions.HTTPError as e:
                print(e)

        self._verify_response(result)
        return result.json()['result']

    def get_market_ticker(cls, pair):
        '''returns simple current market status report'''

        return cls.api(cls.url + "public/"+ "ticker/" + cls.format_pair(pair))

    def get_market_trade_history(cls, pair, limit=1000):
        '''get market trade history'''

        return cls.api(cls.url + "public/trades/" + cls.format_pair(pair), 
                        params={'limit': limit})

    def get_market_orders(cls, pair):
        '''return order book for the market'''

        return cls.api(cls.url + "public/orderbook/" + cls.format_pair(pair))

    def get_market_spread(cls, pair):
        '''return first buy order and first sell order'''

        order_book = cls.get_market_orders(cls.format_pair(pair))

        ask = order_book['ask'][0]['price']
        bid = order_book['bid'][0]['price']

        return Decimal(ask) - Decimal(bid)

    def get_markets(cls):
        '''Find supported markets on this exchange'''

        r = cls.api(cls.url + "public/" + "symbol")

        pairs = [i["id"].lower() for i in r]
        return pairs

    def get_market_volume(cls, pair):
        ''' return volume of last 24h'''

        return cls.get_market_ticker(cls.format_pair(pair))["volume"]

    def get_market_depth(cls, pair):
        '''return sum of all bids and asks'''

        order_book = cls.get_market_orders(cls.format_pair(pair))
        asks = sum([Decimal(i['size']) for i in order_book['ask']])
        bid = sum([Decimal(i['size']) for i in order_book['bid']])

        return {"bids": bid, "asks": asks}

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

    def sell_limit(self, pair, price, quantity):
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

    def buy_limit(self, pair, price, quantity):
        '''creates buy order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "order",
                                params={'symbol': self.format_pair(pair),
                                    'side': 'buy', 'quantity': quantity,
                                    'price': price},
                                http_method='POST')
