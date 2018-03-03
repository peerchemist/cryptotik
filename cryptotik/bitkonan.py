# -*- coding: utf-8 -*-

'''https://bitkonan.com/info/api'''

import requests
from decimal import Decimal
import time
from cryptotik.common import headers, ExchangeWrapper
from cryptotik.exceptions import APIError


class Bitkonan(ExchangeWrapper):

    def __init__(self, apikey=None, timeout=None, proxy=None):

        if apikey:
            self._apikey = apikey

        if proxy:
            assert proxy.startswith('https'), {'Error': 'Only https proxies supported.'}
        self.proxy = {'https': proxy}

        if not timeout:
            self.timeout = (8, 15)
        else:
            self.timeout = timeout

        self.api_session = requests.Session()

    public_commands = ("ticker", "transactions", "order_book")
    private_commands = ("balance", "user_transactions", "open_orders", "order_status",
                        "cancel_order", "cancel_all_orders", "buy",
                        "sell")

    name = 'bitkonan'
    url = 'https://www.bitkonan.com/'
    api_url = url + 'api/'
    delimiter = "/"
    case = "lower"
    headers = headers
    _markets = 'btc-usd', 'ltc-usd'
    maker_fee, taker_fee = 0.0029, 0.0029
    quote_order = 0
    base_currencies = ['usd', 'eur']

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

        pair = pair.replace("-", cls.delimiter)

        if not pair.isupper():
            return pair.upper()
        else:
            return pair

    def _verify_response(self, response):
        raise NotImplementedError

    def _generate_signature(self):
        raise NotImplementedError

    def api(self, command, params={}):
        """call remote API"""

        try:
            result = self.api_session.get(self.api_url + command, params=params,
                                          headers=self.headers, timeout=self.timeout,
                                          proxies=self.proxy)

            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        return result.json()

    def private_api(self, command):
        '''handles private api methods'''

        if not self._apikey:
            raise ValueError("A Key, Secret and customer_id required!")

        raise NotImplementedError

    def get_markets(self):
        '''get all market pairs supported by the exchange'''

        return self._markets

    def get_market_ticker(self, pair):
        """return ticker for market <pair>"""

        pair = self.format_pair(pair)

        if 'BTC' in pair:
            return self.api("ticker")
        if 'LTC' in pair:
            return self.api("ltc_ticker")

    def get_market_orders(self, pair, group=True):
        """returns market order book for <pair>,
            group=True to group the orders with the same price."""

        pair = self.format_pair(pair)
        if 'BTC' in pair:
            u = 'btc_orderbook/'
        if 'LTC' in pair:
            u = 'ltc_orderbook/'

        return self.api(u, params={'group': group})

    def get_market_sell_orders(self, pair):

        return self.get_market_orders(pair)['asks']

    def get_market_buy_orders(self, pair):

        return self.get_market_orders(pair)['bids']

    def get_market_trade_history(self, pair, limit=200, sort='desc'):
        """get market trade history; limit to see only last <n> trades.
           sort - sorting by date and time (asc - ascending; desc - descending). Default: desc."""

        pair = self.format_pair(pair)
        if 'BTC' in pair:
            u = 'transactions/'
        if 'LTC' in pair:
            u = 'ltc_transactions/'

        return self.api(u, params={'limit': limit, 'sort': sort})

    def get_market_depth(self, pair):
        """get market order book depth"""

        pair = self.format_pair(pair)
        order_book = self.get_market_orders(pair)

        return {"bids": sum([i['usd'] for i in order_book['bid']]),
                "asks": sum([i[pair.split('/')[0].lower()] for i in order_book['ask']])
                }

    def get_market_spread(self, pair):
        """get market spread"""

        pair = self.format_pair(pair)

        order = self.get_market_ticker(pair)
        return Decimal(order["ask"]) - Decimal(order["bid"])

    def get_market_volume(self, pair):
        '''return market volume [of last 24h]'''

        raise NotImplementedError

    def get_balances(self, coin=None):
        '''Returns the values relevant to the specified <coin> parameter.'''

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
        raise NotImplementedError

    def get_open_orders(self, pair=None):
        '''Get open orders.'''

        raise NotImplementedError

    def get_order(self, order_id):
        '''get order information'''

        raise NotImplementedError

    def withdraw(self, coin, amount, address):
        '''withdraw cryptocurrency'''

        raise NotImplementedError

    def get_transaction_history(self):
        '''Returns the history of transactions.'''

        raise NotImplementedError

    def get_deposit_history(self, coin=None):
        '''get deposit history'''

        raise NotImplementedError

    def get_withdraw_history(self, coin=None):
        '''get withdrawals history'''

        raise NotImplementedError
