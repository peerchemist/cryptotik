# -*- coding: utf-8 -*-

import hmac
import hashlib
import time
import base64
import requests
from cryptotik.common import APIError, headers, ExchangeWrapper
from re import findall
from decimal import Decimal


class Kraken(ExchangeWrapper):

    url = 'https://api.kraken.com/0/'
    name = 'kraken'
    delimiter = ""
    headers = headers
    taker_fee, maker_fee = 0.00, 0.00

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        return "".join(findall(r"[^\W\d_]+|\d+", pair)).upper()

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        '''initialize class'''

        if apikey and secret:
            self.apikey = apikey.encode('utf-8')
            self.secret = secret.encode('utf-8')

        if proxy:
            assert proxy.startswith('https'), {'Error': 'Only https proxies supported.'}
        self.proxy = {'https': proxy}

        if not timeout:
            self.timeout = (8, 15)
        else:
            self.timeout = timeout

        self.api_session = requests.Session()

    def _verify_response(self, response):

        if response.json()['error']:
            raise APIError(response.json()['error'])

    def api(self, url, params=None):
        '''call api'''

        try:
            result = self.api_session.get(url, headers=self.headers, 
                                          params=params, timeout=self.timeout,
                                          proxies=self.proxy)

            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(result)
        return result.json()['result']

    def get_nonce(self):
        '''return nonce integer'''

        return int(1000 * time.time())

    def private_api(self, url, params={}):
        '''handles private api methods'''

        urlpath = url[22:]
        data = params
        data['nonce'] = self.get_nonce()
        postdata = requests.compat.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        signature = hmac.new(base64.b64decode(self.secret),
                    message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())

        try:
            result = self.api_session.post(url, data=data, headers={
                                           'API-Key': self.apikey,
                                           'API-Sign': sigdigest.decode()},
                                           timeout=self.timeout,
                                           proxies=self.proxy)

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(result)
        return result.json()['result']

    def get_markets(self):
        '''Find supported markets on this exchange'''

        r = self.api(self.url + "public/AssetPairs")
        return [i.lower() for i in r]

    def get_market_ticker(self, pair):
        '''returns simple current market status report'''
        p = self.format_pair(pair)
        return self.api(self.url + "public/Ticker", 
                params={'pair': p})[p]

    def get_market_volume(self, pair):
        ''' return volume of last 24h'''

        return self.get_market_ticker(self.format_pair(pair))['v'][1]

    def get_market_trade_history(self, pair, limit=10):
        '''get market trade history'''

        p = self.format_pair(pair)
        return self.api(self.url + "public/Trades", 
                        params={'pair': p})[p][:limit]

    def get_market_orders(self, pair, limit=100):
        '''return order book for the market'''

        p = self.format_pair(pair)
        return self.api(self.url + "public/Depth", 
                        params={'pair': p, 'count': limit})[p]

    def get_market_spread(self, pair):
        '''return first buy order and first sell order'''

        order_book = self.get_market_orders(self.format_pair(pair))

        ask = order_book["asks"][0][0]
        bid = order_book["bids"][0][0]

        return Decimal(ask) - Decimal(bid)

    def get_market_depth(self, pair):
        '''return sum of all bids and asks'''

        order_book = self.get_market_orders(self.format_pair(pair))
        asks = sum([Decimal(i[1]) for i in order_book['asks']])
        bid = sum([Decimal(i[1]) for i in order_book['bids']])

        return {"bids": bid, "asks": asks}

    def get_balances(self):

        return self.private_api(self.url + "private/Balance")

    def get_deposit_method(self, currency):

        return self.private_api(self.url + "private/DepositMethods",
                                params={'asset': currency.upper()}
                                )[0]['method']

    def get_deposit_address(self, currency):
        ''' get deposit address for <currency> '''

        result = self.private_api(self.url + "private/DepositAddresses",
                                params={'asset': currency.upper(),
                                'method': self.get_deposit_method(currency)}
                                )
        if result == []:
            result = self.private_api(self.url + "private/DepositAddresses",
                                params={'asset': currency.upper(),
                                'method': self.get_deposit_method(currency),
                                'new': 'true'}
                                )

        return result[0]['address']

    def buy_limit(self, pair, price, quantity):
        '''creates buy limit order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + 'private/AddOrder',
                                params={'pair': self.format_pair(pair),
                                        'type': 'buy', 'ordertype': 'limit',
                                        'price': price, 'volume': quantity
                                        })

    def buy_market(self, pair, price, quantity):
        '''creates buy market order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + 'private/AddOrder',
                                params={'pair': self.format_pair(pair),
                                        'type': 'buy', 'ordertype': 'market',
                                        'volume': quantity
                                        })

    def sell_limit(self, pair, price, quantity):
        '''creates sell order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + 'private/AddOrder',
                                params={'pair': self.format_pair(pair),
                                        'type': 'sell', 'ordertype': 'limit',
                                        'price': price, 'volume': quantity
                                        })

    def sell_market(self, pair, price, quantity):
        '''creates sell market order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + 'private/AddOrder',
                                params={'pair': self.format_pair(pair),
                                        'type': 'sell', 'ordertype': 'market',
                                        'volume': quantity
                                        })

    def withdraw(self, currency, amount, withdrawal_key_name):
        '''withdraw <currency> <amount> to <withdrawal_key_name>, 
                which has to be set up on your account'''

        return self.private_api(self.url + 'private/Withdraw', 
                            params={'asset': currency.upper(),
                                'key': withdrawal_key_name, 'amount': amount
                            })

    def get_withdraw_history(self, currency):
        '''Retrieves withdrawal history for <currency>'''

        return self.private_api(self.url + "private/WithdrawStatus", 
                            params={'asset': currency.upper()})

    def get_deposit_history(self, currency):
        '''Retreive deposit history for <currency>.'''

        return self.private_api(self.url + "private/DepositStatus", 
                            params={'asset': currency.upper(),
                            'method': self.get_deposit_method(currency)
                            })

    def get_open_orders(self):
        '''get open orders.'''

        return self.private_api(self.url + "private/OpenOrders",
                            params={'trades': 'true'}
                            )['open']

    def get_order(self, orderId):
        """retrieve a single order by orderId."""

        return self.private_api(self.url + "private/QueryOrders",
                            params={'trades': 'true',
                            'txid': orderId})

    def cancel_order(self, orderId):
        """cancel order with <orderId>"""

        return self.private_api(self.url + "private/CancelOrder",
                            params={'txid': orderId})

    def cancel_all_orders(self):
        """cancel all orders"""

        for txid in self.get_open_orders():
              self.cancel_order(txid)
