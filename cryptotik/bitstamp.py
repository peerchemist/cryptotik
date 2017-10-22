# -*- coding: utf-8 -*-

import requests
from decimal import Decimal
import time
from cryptotik.common import headers, ExchangeWrapper
import hmac
import hashlib


class Bitstamp(ExchangeWrapper):

    def __init__(self, apikey=None, secret=None, customer_id=None, timeout=None):

        if apikey:
            self._apikey = apikey
            self._secret = secret
            self._customer_id = customer_id

    api_session = requests.Session()

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
        """format the pair argument to format understood by remote API."""

        pair = pair.replace("-", cls.delimiter)

        if not pair.islower():
            return pair.lower()
        else:
            return pair

    @classmethod
    def api(cls, command):
        """call remote API"""

        result = cls.api_session.get(cls.url + command, headers=cls.headers,
                                     timeout=cls.timeout)

        assert result.status_code == 200, {"error": "http_error: " + str(result.status_code)}

        return result.json()

    def private_api(self, command):
        '''handles private api methods'''

        if not self._customer_id or not self._apikey or not self._secret:
            raise ValueError("A Key, Secret and customer_id required!")

        nonce = str(self.get_nonce())
        message = (nonce + self._customer_id + self._apikey).encode('utf-8')

        sig = hmac.new(self._secret.encode('utf-8'),
                       msg=message,
                       digestmod=hashlib.sha256).hexdigest().upper()

        result = self.api_session.post(self.trade_url+command,
                                       data={'key': self._apikey,
                                             'nonce': nonce,
                                             'signature': sig},
                                       headers=headers,
                                       timeout=self.timeout)

        assert result.status_code == 200, {"error": "http_error: " + str(result.status_code)}

        return result

    @classmethod
    def get_markets(cls):
        '''get all market pairs supported by the exchange'''

        return cls._markets

    @classmethod
    def get_market_ticker(cls, pair):
        """return ticker for market <pair>"""

        pair = cls.format_pair(pair)
        return cls.api("ticker/" + pair)

    @classmethod
    def get_market_orders(cls, pair):
        """returns market order book for <pair>"""

        pair = cls.format_pair(pair)
        return cls.api("order_book/" + pair)

    @classmethod
    def get_market_trade_history(cls, pair, since="hour"):
        """get market trade history; since {minute, hour, day}"""

        pair = cls.format_pair(pair)

        return cls.api("transactions/" + pair + "/?time={0}".format(since))

    @classmethod
    def get_market_depth(cls, pair):
        """get market order book depth"""

        pair = cls.format_pair(pair)
        order_book = cls.get_market_orders(pair)
        return {"bids": sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]]),
                "asks": sum([Decimal(i[1]) for i in order_book["asks"]])}

    @classmethod
    def get_market_spread(cls, pair):
        """get market spread"""

        pair = cls.format_pair(pair)

        order_book = cls.get_market_orders(pair)
        return Decimal(order_book["asks"][0][0]) - Decimal(order_book["bids"][0][0])

    @classmethod
    def get_market_volume(cls, pair):
        '''return market volume [of last 24h]'''

        pair = cls.format_pair(pair)

        return cls.get_market_ticker(pair)['volume']

    ########################
    # Private methods bellow
    ########################

    def get_balances(self, coin=None):
        '''Returns the values relevant to the specified <coin> parameter.'''

        if not coin:
            return self.private_api("balance")
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
