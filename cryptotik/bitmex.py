# -*- coding: utf-8 -*-

import requests
import hashlib
import hmac
import json
from decimal import Decimal
import time
from cryptotik.common import is_sale
from cryptotik.common import (headers, ExchangeWrapper)
from cryptotik.exceptions import APIError


class Bitmex(ExchangeWrapper):

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None,
                 testnet=False):

        if apikey and secret:
            self.apikey = apikey
            self.secret = secret

        if proxy:
            assert proxy.startswith('https'), {'Error': 'Only https proxies supported.'}
        self.proxy = {'https': proxy}

        if not timeout:
            self.timeout = (8, 15)
        else:
            self.timeout = timeout

        self.api_session = requests.Session()

        if testnet:
            self.url = 'https://testnet.bitmex.com/api/v1'

    url = 'https://bitmex.com/api/v1'
    name = 'bitmex'
    delimiter = ""
    case = "upper"
    headers = headers
    maker_fee, taker_fee = 0.002, 0.002
    base_currencies = ['xbt']
    quote_order = 0

    def get_nonce(self):
        '''return nonce integer'''

        nonce = getattr(self, '_nonce', 0)
        if nonce:
            nonce += 1
        # If the unix time is greater though, use that instead (helps low
        # concurrency multi-threaded apps always call with the largest nonce).
        self._nonce = max(int(time.time()), nonce)
        return self._nonce

    def get_base_currencies(self):
        raise NotImplementedError

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        if isinstance(pair, list):
            return pair

        pair = pair.replace("-", cls.delimiter)

        if not pair.isupper():
            return pair.upper()
        else:
            return pair

    def _verify_response(self, response):
        '''verify if API responded properly and raise apropriate error.'''

        try:
            if response.json()['error']:
                raise APIError(response.json())
        except TypeError:
            pass

    def api(self, command):
        """call remote API"""

        try:
            result = self.api_session.get(self.url + command, headers=self.headers,
                                          timeout=self.timeout, proxies=self.proxy)

            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(result)
        return result.json()

    def _generate_signature(self, url, params, expires):

        # request type + path + str(nonce) + data
        message = 'POST/api/v1' + url + str(expires) + str(json.dumps(params)).replace(" ", "")

        signature = hmac.new(bytes(self.secret, 'utf8'),
                             bytes(message, 'utf8'),
                             digestmod=hashlib.sha256).hexdigest()
        return signature

    def private_api(self, url, params):
        '''handles private api methods'''

        expires = int(round(time.time()) + 5)  # 5s grace period in case of clock skew
        self.headers.update({
            'api-expires': str(expires),
            'api-key': self.apikey,
            'api-signature': self._generate_signature(url, params,
                                                      expires)
        })

        try:
            result = self.api_session.post(self.url, data=params,
                                           headers=headers,
                                           timeout=self.timeout,
                                           proxies=self.proxy)

            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(result)
        return result.json()

    def get_markets(self):
        '''get all pairs supported by the exchange'''

        q = self.api("/instrument/active")

        return [i['symbol'] for i in q]

    def get_market_ticker(self, pair):
        """return ticker for market"""

        pair = self.format_pair(pair)

        q = [i for i in self.api("/instrument/active") if i['symbol'] == pair][0]

        return {
                'lastPrice': q['lastPrice'],
                'lastChangePcnt': q['lastChangePcnt'],
                'lastTickDirection': q['lastTickDirection'],
                'lowPrice': q['lowPrice'],
                'prevClosePrice': q['prevClosePrice'],
                'timestamp': q['timestamp'],
                'volume24h': q['volume24h'],
                'vwap': q['vwap']
                }

    def get_market_volume(self, pair):
        '''get the market volume'''

        return self.get_market_ticker(self.format_pair(pair),
                                      )['volume24h']

    def get_market_orders(self, pair, depth=100):
        """returns market order book on selected pair."""

        params = {'symbol': self.format_pair(pair),
                  'depth': depth
                  }

        return self.api("/orderBook/L2" + "?" +
                        requests.compat.urlencode(params))

    def get_market_sell_orders(self, pair, depth=100):

        return [i for i in self.get_market_orders(pair, depth)
                if i['side'] == 'Sell']

    def get_market_buy_orders(self, pair, depth=100):

        return [i for i in self.get_market_orders(pair, depth)
                if i['side'] == 'Buy']

    def get_market_trade_history(self, pair, count=100):
        """get market trade history"""

        params = {'symbol': Bitmex.format_pair(pair),
                  'count': count
                  }

        return self.api("/trade" + "?" +
                        requests.compat.urlencode(params))

    def get_funding_history(self, pair, count=10):
        '''get market funding history'''

        params = {'symbol': self.format_pair(pair),
                  'count': count
                  }

        return self.api("/funding" + "?" +
                        requests.compat.urlencode(params))

    def get_balances(self):
        '''
        Returns information about the user’s current balance, API-key privileges,
        the number of open orders and Server Time.
        '''

        raise NotImplementedError

    def get_deposit_address(self, coin=None):
        '''get deposit address'''

        raise NotImplementedError

    def buy_limit(self, pair, rate, amount):
        '''submit spot buy order'''

        raise NotImplementedError

    def sell_limit(self, pair, rate, amount):
        '''submit spot sell order'''

        raise NotImplementedError

    def cancel_order(self, order_id):
        '''cancel order by <order_id>'''

        raise NotImplementedError

    def cancel_all_orders(self):
        '''cancel all active orders'''

        raise NotImplementedError

    def get_open_orders(self, pair=None):
        '''get open orders'''

        raise NotImplementedError

    def get_order(self, order_id):
        '''get order information'''

        raise NotImplementedError

    def withdraw(self, coin, amount, address):
        '''withdraw cryptocurrency'''

        raise NotImplementedError

    def get_transaction_history(self, since=1, until=time.time()):
        '''Returns the history of transactions.'''

        raise NotImplementedError

    def get_deposit_history(self, coin=None):
        '''get deposit history'''

        raise NotImplementedError

    def get_withdraw_history(self, coin=None):
        '''get withdrawals history'''

        raise NotImplementedError
