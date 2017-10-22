# -*- coding: utf-8 -*-

import requests
from decimal import Decimal
import time
from cryptotik.common import headers, ExchangeWrapper


class Bitstamp(ExchangeWrapper):

    def __init__(self, apikey=None, secret=None, customer_id=None, timeout=None):

        if apikey:
            self.apikey = apikey.encode("utf-8")
            self.secret = secret.encode("utf-8")
            self.customer_id = customer_id.encode("utf-8")
        self.nonce = int(time.time())

    api_session = requests.Session()

    public_commands = ("ticker", "transactions", "order_book")
    private_commands = ("balance", "user_transactions", "open_orders", "order_status",
                        "cancel_order", "cancel_all_orders", "buy",
                        "sell")

    name = 'bitstamp'
    url = 'https://www.bitstamp.net/api/v2/'
    trade_url = url
    delimiter = ""
    case = "lower"
    headers = headers
    _markets = 'btcusd, btceur, eurusd, xrpusd, xrpeur, xrpbtc, ltcusd, ltceur, ltcbtc, ethusd, etheur, ethbtc'.split(', ')
    maker_fee, taker_fee = 0.002, 0.002
    try:
        assert timeout is not None
    except:
        timeout = (8, 15)

    @property
    def _nonce(self):
        '''return nonce integer'''

        self.nonce += 17
        return self.nonce

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
