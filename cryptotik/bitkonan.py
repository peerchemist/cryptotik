# -*- coding: utf-8 -*-

'''https://bitkonan.com/info/api'''

import requests
from decimal import Decimal
import time
import hmac
import hashlib
from cryptotik.common import headers, ExchangeWrapper
from cryptotik.exceptions import APIError


class Bitkonan(ExchangeWrapper):

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):

        if apikey and secret:
            self.apikey = apikey
            self.secret = secret.encode("utf-8")

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
    private_api_url = api_url + 'private/'
    delimiter = "/"
    case = "lower"
    headers = headers
    _markets = ['btc-usd', 'ltc-usd']
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
        
        return self.base_currencies

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        pair = pair.replace("-", cls.delimiter)

        if not pair.isupper():
            return pair.upper()
        else:
            return pair

    def _verify_response(self, response):
        
        if 'errors' in response.json().keys():
            raise APIError(response.json()['errors'])

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

    def private_api(self, command, params=None):
        '''handles private api methods'''

        if not self.apikey:
            raise ValueError("A Key, Secret and customer_id required!")

        tstamp = str(int(time.time()))
        msg = (self.apikey + tstamp).encode('utf-8')
        sign = hmac.new(self.secret, 
                        msg, 
                        hashlib.sha256).hexdigest()
        data = {'key': self.apikey,
                'timestamp': tstamp,
                'sign': sign}
        if params:
            for k, v in params.items():
                data[k] = v
        
        try:
            response = self.api_session.post(self.private_api_url + command, headers=headers, 
                                params=data, timeout=self.timeout, proxies=self.proxy)

            response.raise_for_status()
            
        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(response)
        return response.json()['data']

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
        
        return self.private_api('balance')

    def get_deposit_address(self, coin=None):
        '''get deposit address'''

        raise NotImplementedError

    def buy_limit(self, pair, rate, amount):
        '''submit limit buy order'''

        return self.private_api('order/new', params={
                                'pair': self.format_pair(pair),
                                'side': 'BUY',
                                'type': 'LIMIT',
                                'amount': amount,
                                'limit': rate
                                })

    def buy_stop(self, pair, rate, amount):
        '''submit stop buy order'''

        return self.private_api('order/new', params={
                                'pair': self.format_pair(pair),
                                'side': 'BUY',
                                'type': 'STOP',
                                'amount': amount,
                                'stop': rate
                                })

    def buy_market(self, pair, amount):
        '''submit market buy order'''

        return self.private_api('order/new', params={
                                'pair': self.format_pair(pair),
                                'side': 'BUY',
                                'type': 'MARKET',
                                'amount': amount,
                                })

    def sell_limit(self, pair, rate, amount):
        '''submit limit sell order'''

        return self.private_api('order/new', params={
                                'pair': self.format_pair(pair),
                                'side': 'SELL',
                                'type': 'LIMIT',
                                'amount': amount,
                                'limit': rate
                                })
    def sell_stop(self, pair, rate, amount):
        '''submit stop sell order'''

        return self.private_api('order/new', params={
                                'pair': self.format_pair(pair),
                                'side': 'SELL',
                                'type': 'STOP',
                                'amount': amount,
                                'stop': rate
                                })

    def sell_market(self, pair, amount):
        '''submit market sell order'''

        return self.private_api('order/new', params={
                                'pair': self.format_pair(pair),
                                'side': 'SELL',
                                'type': 'MARKET',
                                'amount': amount,
                                })

    def cancel_order(self, order_id):
        '''cancel order by <order_id>'''

        return self.private_api('order/cancel', params={'id': order_id})

    def cancel_all_orders(self):
        
        for order in self.get_open_orders():
            self.cancel_order(order['id'])

    def get_open_orders(self, pair=None):
        '''Get open orders.'''

        return self.private_api('orders')

    def get_order(self, order_id):
        '''get order information'''

        raise NotImplementedError

    def withdraw(self, coin, amount, address):
        '''withdraw cryptocurrency'''

        raise NotImplementedError

    def get_transaction_history(self, limit = 100):
        '''Returns the history of transactions.'''

        return self.private_api('transactions', params={'limit': limit})

    def get_deposit_history(self, coin=None):
        '''get deposit history'''

        raise NotImplementedError

    def get_withdraw_history(self, coin=None):
        '''get withdrawals history'''

        raise NotImplementedError
