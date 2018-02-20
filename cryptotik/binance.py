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

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):

        if apikey and secret:
            self.apikey = apikey
            self.secret = bytes(secret.encode("utf-8"))

        if proxy:
            assert proxy.startswith('https'), {'Error': 'Only https proxies supported.'}
        self.proxy = {'https': proxy}

        if not timeout:
            self.timeout = (8, 15)
        else:
            self.timeout = timeout

        self.api_session = requests.Session()

    def _verify_response(self, response):
        '''verify if API responded properly and raise apropriate error.'''

        if "msg" in response.json() and "code" in response.json():
            raise APIError(response.json()['msg'])

    def api(self, url, params):
        '''call api'''

        try:
            response = self.api_session.get(url, params=params, headers=self.headers,
                                            timeout=self.timeout, proxies=self.proxy)
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(response)
        return response.json()

    def private_api(self, url, params={}, http_method='GET'):
        '''handles private api methods'''

        query = requests.compat.urlencode(sorted(params.items()))
        query += "&timestamp={}".format(int(time.time() * 1000))

        signature = hmac.new(self.secret, query.encode("utf-8"),
                             hashlib.sha256).hexdigest()

        query += "&signature={}".format(signature)

        try:
            response = self.api_session.request(http_method,
                                            url + "?" + query,
                                            headers={"X-MBX-APIKEY": self.apikey},
                                            proxies=self.proxy)
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(response)
        return response.json()

    @classmethod
    def format_pair(self, pair):
        '''Format the pair argument to format understood by remote API.'''

        pair = pair.replace("-", self.delimiter).upper()
        return pair

    def get_market_ticker(self, pair):
        '''returns simple current market status report'''

        params = (('symbol', self.format_pair(pair)),)

        return self.api(self.url + "api/v1/ticker/24hr", params)

    def get_market_trade_history(self, pair, limit=100):
        '''get market trade history'''

        return self.api(self.url + "api/v1/aggTrades", 
                        params=(('symbol', self.format_pair(pair)), ('limit', limit),))

    def get_summaries(self):
        '''get summary of all active markets'''

        return self.api(self.url + 'api/v1/ticker/24hr',
                        params=())

    def get_market_orders(self, pair, limit=100):
        '''return sum of all bids and asks'''

        params = (('symbol', self.format_pair(pair)), ('limit', limit),)

        return self.api(self.url + 'api/v1/depth', params)

    def get_market_spread(self, pair):
        '''return first buy order and first sell order'''

        order_book = self.get_market_orders(self.format_pair(pair))

        ask = order_book['asks'][0][0]
        bid = order_book['bids'][0][0]

        return Decimal(ask) - Decimal(bid)

    def get_market_depth(self, pair):
        '''return sum of all bids and asks'''

        order_book = self.get_market_orders(self.format_pair(pair))
        asks = sum([Decimal(i[1]) for i in order_book['asks']])
        bid = sum([Decimal(i[1]) for i in order_book['bids']])

        return {"bids": bid, "asks": asks}

    def get_markets(self, filter=None):
        '''Find supported markets on this exchange,
            use <filter> if needed'''

        r = self.api(self.url + "api/v1/ticker/allPrices", params=())
        pairs = [i["symbol"].lower() for i in r]
        if filter:
            pairs = [p for p in pairs if filter in p]
        return pairs

    def get_market_volume(self, pair):
        ''' return volume of last 24h'''

        return self.get_market_ticker(self.format_pair(pair))["volume"]

    def get_balances(self):
        """get all balances from your account"""

        balances = self.private_api(self.url + "api/v3/account")["balances"]

        return [i for i in balances if i["free"] != '0.00000000']

    def buy_limit(self, pair, price, quantity):
        '''creates buy order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "api/v3/order",
                                params={'symbol': self.format_pair(pair),
                                        'side': 'BUY', 'type': 'limit',
                                        'timeInForce': 'GTC', 'quantity': quantity,
                                        'price': price},
                                http_method='POST')

    def buy_market(self, pair, quantity):
        '''execute market buy order'''

        return self.private_api(self.url + "api/v3/order",
                                params={'symbol': self.format_pair(pair),
                                        'side': 'BUY', 'type': 'market',
                                        'quantity': quantity
                                        },
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

    def sell_limit(self, pair, price, quantity):
        '''creates sell order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "api/v3/order",
                                params={'symbol': self.format_pair(pair),
                                        'side': 'SELL', 'type': 'limit',
                                        'timeInForce': 'GTC', 'quantity': quantity,
                                        'price': price},
                                http_method='POST')

    def sell_market(self, pair, quantity):
        '''execute market sell order'''

        return self.private_api(self.url + "api/v3/order",
                                params={'symbol': self.format_pair(pair),
                                        'side': 'SELL', 'type': 'market',
                                        'quantity': quantity
                                        },
                                http_method='POST')

    def withdraw(self, coin, amount, address, name=None, address_tag=None):
        '''withdraw <coin> <amount> to <address> with <address_tag> if needed
        : name is description of the address.'''

        if address_tag:
            query = {'asset': coin.upper(),
                     'address': address,
                     'addressTag': address_tag,
                     'amount': amount}

        else:
            query = {'asset': coin.upper(),
                     'address': address,
                     'amount': amount}

        if not name:
            query['name'] = coin.upper()
        else:
            query['name'] = name

        return self.private_api(self.url + "/wapi/v3/withdraw.html",
                                params=query,
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
