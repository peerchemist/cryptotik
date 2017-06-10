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

    def __init__(self, apikey, secret):
        self.apikey = apikey.encode("utf-8")
        self.secret = secret.encode("utf-8")
        self.nonce = int(time.time())

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
                                     timeout=(3, 5)).json()

        assert result["success"] is True
        return result

    def private_api(self, url, params):
        '''handles private api methods'''

        if not self.apikey or not self.secret:
            raise ValueError("A Key and Secret needed!")

        params.update({"apikey": self.apikey, "nonce": self.get_nonce})
        url += "?" + requests.compat.urlencode(params)
        self.headers.update({"apisign": hmac.new(self.secret, url.
                                                 encode(), hashlib.sha512).hexdigest()
                            })

        result = requests.get(url, headers=self.headers, timeout=3)

        assert result["success"] is True

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

    @classmethod
    def sort_markets_by_volume(cls, n=10):
        """returns list of >n< markets sorted by daily volume expressed in base pair"""

        r = cls.get_markets_summaries()
        markets = sorted(r, key=lambda k: k['BaseVolume'])
        markets.reverse()
        volume = [i["BaseVolume"] for i in markets[:n]]
        name = [i["MarketName"].lower() for i in markets[:n]]

        return zip(name, volume)

    def buy(self, pair, rate, amount):  # buy_limit as default
        """creates buy order for <pair> at <rate> for <amount>"""

        return self.private_api(self.url + "market" + "/buylimit",
                                params={"market": self.format_pair(pair),
                                        "quantity": amount,
                                        "rate": rate})["result"]

    def sell(self, pair, rate, amount):  # sell_limit as default
        """creates sell order for <pair> at <rate> for <amount>"""

        return self.private_api(self.url + "market" + "/selllimit",
                                params={"market": self.format_pair(pair),
                                        "quantity": amount,
                                        "rate": rate})["result"]

    def cancel_order(self, order_id):
        """cancel order <id>"""

        return self.private_api(self.url + "market" + "/cancel",
                                params={"uuid": order_id})["result"]

    def get_open_orders(self, market=None):
        """get open orders for <market> or all"""

        return self.private_api(self.url + "market" + "/getopenorders",
                                params={"market": self.format_pair(market)})["result"]

    def get_balances(self):
        """get all balances from your account"""

        return self.private_api(self.url + "account" + "/getbalances",
                                params={})["result"]

    def get_deposit_addresses(self, coin):
        """retrieve or generate an address for a specific currency.
        If one does not exist, the call will fail and return ADDRESS_GENERATING until one is available."""

        return self.private_api(self.url + "account" + "/getdepositaddress",
                                params={"currency": coin.upper()})["result"]

    def withdraw(self, coin, amount, address):
        """withdraw <coin> <amount> to <address>"""

        return self.private_api(self.url + "account" + "/withdraw",
                                params={"currency": coin.upper(),
                                        "quantity": amount,
                                        "address": address})["result"]


