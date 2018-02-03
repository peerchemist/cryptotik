# -*- coding: utf-8 -*-

'''https://www.bitstamp.net/api/'''

import requests
from decimal import Decimal
import time
from cryptotik.common import headers, ExchangeWrapper, APIError
import hmac
import hashlib


class Bitstamp(ExchangeWrapper):

    def __init__(self, apikey=None, secret=None, customer_id=None,
                 timeout=None, proxy=None):

        if apikey:
            self._apikey = apikey
            self._secret = secret
            self._customer_id = customer_id

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

    name = 'bitstamp'
    url = 'https://www.bitstamp.net/'
    trade_url = url + 'api/v2/'
    delimiter = ""
    case = "lower"
    headers = headers
    _markets = 'btcusd, btceur, eurusd, xrpusd, xrpeur, xrpbtc, ltcusd, ltceur, ltcbtc, ethusd, etheur, ethbtc'.split(', ')
    maker_fee, taker_fee = 0.002, 0.002

    def get_nonce(self):
        '''return nonce integer'''

        nonce = getattr(self, '_nonce', 0)
        if nonce:
            nonce += 1
        # If the unix time is greater though, use that instead (helps low
        # concurrency multi-threaded apps always call with the largest nonce).
        self._nonce = max(int(time.time() * 1000000), nonce)
        return self._nonce

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        pair = pair.replace("-", cls.delimiter)

        if not pair.islower():
            return pair.lower()
        else:
            return pair

    def api(self, command):
        """call remote API"""

        try:
            result = self.api_session.get(self.trade_url + command, headers=self.headers,
                                          timeout=self.timeout, proxies=self.proxy)

        assert result.status_code == 200, {"error": "http_error: " + str(result.status_code)}
        return result.json()
        except requests.exceptions.RequestException as e:
            raise APIError(e)

    def private_api(self, command):
        '''handles private api methods'''

        if not self._customer_id or not self._apikey or not self._secret:
            raise ValueError("A Key, Secret and customer_id required!")

        nonce = self.get_nonce()
        data = {}
        data['key'] = self._apikey
        message = str(nonce) + self._customer_id + self._apikey

        sig = hmac.new(self._secret.encode('utf-8'),
                       msg=message.encode('utf-8'),
                       digestmod=hashlib.sha256).hexdigest().upper()

        data['signature'] = sig
        data['nonce'] = nonce

        result = self.api_session.post(url=self.trade_url + command,
                                       data=data,
                                       headers=self.headers,
                                       timeout=self.timeout,
                                       proxies=self.proxy)

        assert result.status_code == 200, {"error": "http_error: " + str(result.status_code)}

        return result

    def get_markets(self):
        '''get all market pairs supported by the exchange'''

        return self._markets

    def get_market_ticker(self, pair):
        """return ticker for market <pair>"""

        pair = self.format_pair(pair)
        return self.api("ticker/" + pair)

    def get_market_orders(self, pair):
        """returns market order book for <pair>"""

        pair = self.format_pair(pair)
        return self.api("order_book/" + pair)

    def get_market_trade_history(self, pair, since="hour"):
        """get market trade history; since {minute, hour, day}"""

        pair = self.format_pair(pair)

        return self.api("transactions/" + pair + "/?time={0}".format(since))

    def get_market_depth(self, pair):
        """get market order book depth"""

        pair = self.format_pair(pair)
        order_book = self.get_market_orders(pair)
        return {"bids": sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]]),
                "asks": sum([Decimal(i[1]) for i in order_book["asks"]])}

    def get_market_spread(self, pair):
        """get market spread"""

        pair = self.format_pair(pair)

        order_book = self.get_market_orders(pair)
        return Decimal(order_book["asks"][0][0]) - Decimal(order_book["bids"][0][0])

    def get_market_volume(self, pair):
        '''return market volume [of last 24h]'''

        pair = self.format_pair(pair)

        return self.get_market_ticker(pair)['volume']

    ########################
    # Private methods bellow
    ########################

    def get_balances(self, coin=None):
        '''Returns the values relevant to the specified <coin> parameter.'''

        if not coin:
            return self.private_api("balance/")
        else:
            return self.private_api("balance/{}".format(coin.lower()))

    def get_deposit_address(self, coin=None):
        '''get deposit address'''

        raise NotImplementedError

    def buy(self, pair, rate, amount):
        '''submit spot buy order'''

        raise NotImplementedError

    def sell(self, pair, rate, amount):
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
