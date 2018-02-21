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
    name = 'therock'
    delimiter = ""
    headers = headers

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        '''initialize bittrex class'''

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

    @classmethod
    def format_pair(self, pair):
        """format the pair argument to format understood by remote API."""

        return "".join(findall(r"[^\W\d_]+|\d+", pair)).upper()

    def _verify_response(self, response):
        '''verify if API responded properly and raise apropriate error.'''

        try:
            if 'errors' in response.json().keys():
                raise APIError(response.json()['errors']['message'])
        except KeyError:
            pass

    def api(self, url):
        '''call api'''

        try:
            result = self.api_session.get(url, headers=self.headers,
                                          timeout=self.timeout, proxies=self.proxy)

            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(result)
        return result.json()

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

        try:
            result = self.api_session.request(http_method, url, headers=head,
                                              proxies=self.proxy)
            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(result)
        return result.json()

    def get_market_ticker(self, pair):
        '''returns simple current market status report'''

        return self.api(self.url + "funds/" + self.format_pair(pair) + "/ticker")

    def get_market_trade_history(self, pair, limit=10):
        '''get market trade history'''

        return self.api(self.url + "funds/" + self.format_pair(pair) + "/trades" +
                                "?per_page={}".format(limit))['trades']

    def get_market_orders(self, pair):
        '''return order book for the market'''

        return self.api(self.url + "funds/" + self.format_pair(pair) + "/orderbook")

    def get_market_spread(self, pair):
        '''return first buy order and first sell order'''

        order_book = self.get_market_orders(pair)

        ask = order_book["asks"][0]['price']
        bid = order_book["bids"][0]['price']

        return Decimal(ask) - Decimal(bid)

    def get_market_depth(self, pair):
        '''return sum of all bids and asks'''

        ob = self.get_market_orders(pair)
        return {"bids": Decimal(ob['bids'][-1]['depth']),
                "asks": Decimal(ob['asks'][-1]['depth'])}

    def get_markets(self):
        '''Find supported markets on this exchange'''

        r = self.api(self.url + "funds")['funds']
        pairs = [i["id"].lower() for i in r]

        return pairs

    def get_market_volume(self, pair):
        ''' return volume of last 24h'''

        return self.get_market_ticker(self.format_pair(pair))["volume"]

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

    def buy_limit(self, pair, price, quantity):
        '''creates buy order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "funds/"
                                + self.format_pair(pair) + "/orders",
                                params={'fund_id': self.format_pair(pair),
                                    'side': 'buy', 'amount': quantity,
                                    'price': price},
                                http_method='POST')

    def sell_limit(self, pair, price, quantity):
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
            all_pairs = []
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
