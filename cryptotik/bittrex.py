# -*- coding: utf-8 -*-

import requests
from .common import APIError, headers
import time
import hmac, hashlib

class Bittrex:

    url = 'https://bittrex.com/api/v1.1/'
    delimiter = "-"
    headers = headers
    taker_fee, maker_fee = 0.0025, 0.0025
    private_commands = ('getopenorders', 'cancel', 'sellmarket', 'selllimit',
                        'buymarket', 'buylimit')
    public_commands = ('getbalances', 'getbalance', 'getdepositaddress',
                       'withdraw')
    api_session = requests.Session()

    def __init__(self, apikey=None, secret=None, timeout=None):
        '''initialize bittrex class'''

        if apikey and secret:
            self.apikey = apikey.encode("utf-8")
            self.secret = secret.encode("utf-8")
            self.nonce = int(time.time())

    try:
        assert timeout is not None
    except:
        timeout = (8, 15)

    @property
    def get_nonce(self):
        '''return nonce integer'''

        self.nonce += 1
        return self.nonce

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        pair = pair.replace("_", cls.delimiter)

        if not pair.islower():
            return pair.lower()
        else:
            return pair

    @classmethod
    def api(cls, url, params):
        """call api"""

        result = cls.api_session.get(url, params=params, headers=cls.headers,
                                     timeout=cls.timeout).json()

        assert result["success"] is True
        return result

    def private_api(self, url, params):
        '''handles private api methods'''

        if not self.apikey or not self.secret:
            raise ValueError("A Key and Secret needed!")

        params.update({"apikey": self.apikey, "nonce": self.get_nonce})
        url += "?" + requests.compat.urlencode(params)
        self.headers.update({"apisign": hmac.new(self.secret, url.
                                                 encode(), hashlib.sha512
                                                 ).hexdigest()
                             })

        result = requests.get(url, headers=self.headers, timeout=self.timeout)

        assert result.status_code == 200
        return result.json()

    @classmethod
    def get_markets(cls):
        '''find out supported markets on this exhange.'''

        r = cls.api(cls.url + "public" + "/getmarkets", params={})["result"]
        pairs = [i["MarketName"].lower() for i in r]

        return pairs

    @classmethod
    def get_market_ticker(cls, pair):
        '''returns simple current market status report'''

        return cls.api(cls.url + "public" + "/getticker",
                       params={"market": cls.format_pair(pair)})["result"]

    @classmethod
    def get_market_trade_history(cls, pair, depth=200):
        '''returns last <n> trades for the pair'''

        if depth > 200:
            raise ValueError("Bittrex API allows maximum history of last 200 trades.")

        return cls.api(cls.url + "public" + "/getmarkethistory",
                       params={"market": cls.format_pair(pair)}
                       )["result"][-depth:]

    @classmethod
    def get_market_orders(cls, pair, depth=50):
        '''return market order book, default <depth> is 50'''

        if depth > 50:
            raise ValueError("Bittrex API allows maximum depth of last 50 offers.")

        order_book = cls.api(cls.url + "public" + "/getorderbook",
                             params={'market': cls.format_pair(pair),
                                     'type': 'both',
                                     'depth': depth})["result"]

        return order_book

    @classmethod
    def get_market_depth(cls, pair):
        '''returns market depth'''

        from decimal import Decimal

        order_book = cls.get_market_orders(cls.format_pair(pair))
        return {"bids": sum([Decimal(i["Quantity"]) * Decimal(i["Rate"]) for i in order_book["buy"]]),
                "asks": sum([Decimal(i["Quantity"]) for i in order_book["sell"]])
                }

    @classmethod
    def get_market_summary(cls, pair):
        '''return basic market information'''

        return cls.api(cls.url + "public" + "/getmarketsummary",
                       params={"market": cls.format_pair(pair)})["result"][0]

    @classmethod
    def get_market_spread(cls, pair):
        '''return first buy order and first sell order'''

        from decimal import Decimal

        d = cls.get_market_summary(cls.format_pair(pair))
        return Decimal(d["Ask"]) - Decimal(d["Bid"])

    def buy(self, pair, rate, amount):  # buy_limit as default
        """creates buy order for <pair> at <rate> for <amount>"""

        return self.private_api(self.url + "market" + "/buylimit",
                                params={"market": self.format_pair(pair),
                                        "quantity": amount,
                                        "rate": rate})

    def sell(self, pair, rate, amount):  # sell_limit as default
        """creates sell order for <pair> at <rate> for <amount>"""

        return self.private_api(self.url + "market" + "/selllimit",
                                params={"market": self.format_pair(pair),
                                        "quantity": amount,
                                        "rate": rate})

    def cancel_order(self, order_id):
        """cancel order <id>"""

        return self.private_api(self.url + "market" + "/cancel",
                                params={"uuid": order_id})["result"]

    def get_open_orders(self, market=None):
        """get open orders for <market>
           or all open orders if called without an argument."""

        if market:
            params = {"market": self.format_pair(market)}
        else:
            params = {}

        return self.private_api(self.url + "market" + "/getopenorders",
                                params=params)["result"]

    def get_order_history(self):
        """get order history"""

        return self.private_api(self.url + "account" + "/getorderhistory",
                                params={})["result"]

    def get_balances(self):
        """get all balances from your account"""

        balances = self.private_api(self.url + "account" + "/getbalances",
                                    params={})["result"]

        return [i for i in balances if i["Balance"] > 0]

    def get_deposit_address(self, coin):
        """retrieve or generate an address for <coin>.
        If there is none, call will return empty, call again to get it."""

        addr = self.private_api(self.url + "account" + "/getdepositaddress",
                                params={"currency": coin.upper()})["result"]

        return addr["Address"]

    def withdraw(self, coin, amount, address):
        """withdraw <coin> <amount> to <address>"""

        return self.private_api(self.url + "account" + "/withdraw",
                                params={"currency": coin.upper(),
                                        "quantity": amount,
                                        "address": address})

    def get_order(self, order_id):
        """retrieve a single order by uuid."""

        return self.private_api(self.url + "account" + "/getorder",
                                params={"uuid": order_id})["result"]

    def get_withdrawal_history(self, coin=None):
        """retrieve withdrawal history."""

        if coin:
            params = {"currency": self.format_pair(coin)}
        else:
            params = {}

        return self.private_api(self.url + "account" + "/getwithdrawalhistory",
                                params=params)["result"]

    def get_deposit_history(self, coin=None):
        """retreive deposit history."""

        if coin:
            params = {"currency": self.format_pair(coin)}
        else:
            params = {}

        return self.private_api(self.url + "account" + "/getdeposithistory",
                                params=params)["result"]

