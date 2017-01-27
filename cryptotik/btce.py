import requests
from .common import APIError, headers
import hmac, hashlib

class Btce:

    def __init__(self, apikey=None, secret=None):

        self.apikey = key.encode("utf-8")
        self.secret = secret.encode("utf-8")
        self.nonce = 1

    public_commands = ("info", "ticker", "depth", "trades")
    private_commands = ("getInfo", "Trade", "ActiveOrders", "OrderInfo", "CancelOrder", "TradeHistory",
                        "TransHistory", "WithdrawCoin", "CreateCuopon", "RedeemCuopon")

    url = 'https://btc-e.com/api/3/'
    trade_url = 'https://btc-e.com/tapi/'
    delimiter = "_"
    case = "lower"
    headers = headers
    maker_fee, taker_fee = 0.002, 0.002

    @property
    def get_nonce(self):
        '''return nonce integer'''

        self.nonce += 1
        return self.nonce

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        if isinstance(pair, list):
            return pair

        pair = pair.replace("-", cls.delimiter)

        if not pair.islower():
            return pair.lower()
        else:
            return pair

    @classmethod
    def api(cls, command):
        """call remote API"""

        result = requests.get(cls.url + command, headers=cls.headers)

        assert result.status_code == 200, {"error": "http_error: " + str(result.status_code)}

        return result.json()

    def private_api(self, params):
        '''handles private api methods'''

        if not self.apikey or not self.secret:
            raise ValueError("A Key and Secret needed!")

        params["nonce"] = self.get_nonce
        encoded_params = requests.compat.urlencode(params)

        sig = hmac.new(self.secret,
                       encoded_params.encode("utf-8"),
                       hashlib.sha512)

        self.headers.update({
            "Key": self.apikey,
            "Sign": sig.hexdigest()
        })

        result = requests.post(self.trade_url, data=params, headers=headers, timeout=2)

        assert result.status_code == 200, {"error": "http_error: " + str(result.status_code)}
        return result.json()

    @classmethod
    def get_markets(cls):
        '''get all pairs supported by the exchange'''

        q = cls.api("info")
        return list(q['pairs'].keys())

    @classmethod
    def get_market_ticker(cls, pair):
        """return ticker for market"""

        pair = cls.format_pair(pair)
        return cls.api("ticker" + "/" + pair)

    @classmethod
    def get_markets_ticker(cls):
        """return ticker for all pairs"""

        pair = "-".join(cls.get_markets())
        return cls.api("ticker" + "/" + pair)

    @classmethod
    def get_market_orders(cls, pair, depth=None):
        """returns market order book on selected pair"""

        pair = cls.format_pair(pair)

        if depth == None:
            return cls.api("depth" + "/" + pair)[pair]

        if depth > 2000:
            raise ValueError("Btce API allows maximum depth of 2000 orders")

        return cls.api("depth" + "/" + pair + "/?limit={0}".format(depth))[pair]

    @classmethod
    def get_market_trade_history(cls, pair, limit=1000):
        """get market trade history"""

        pair = cls.format_pair(pair)

        if limit > 2000:
            raise APIError("Btc-e API can return only 2000 last trades.")

        if not isinstance(pair, list):
            return cls.api("trades" + "/" + pair + "/?limit={0}".format(limit))[pair]

        if pair == "all": ## returns market history for all pairs with default history size.
            return cls.api("trades" + "/" + "-".join(cls.get_markets() + "/?limit={0}".format(limit)))

        else: ## simply concat pairs in the list
            return cls.api("trades" + "/" + "-".join(pair) + "/?limit={0}".format(limit))

    @classmethod
    def get_market_depth(cls, pair):
        """get market order book depth"""

        from decimal import Decimal

        pair = cls.format_pair(pair)
        order_book = cls.get_market_orders(pair, 2000)
        return {"bids": sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]]),
                "asks": sum([Decimal(i[1]) for i in order_book["asks"]])}

    @classmethod
    def get_market_spread(cls, pair):
        """get market spread"""

        from decimal import Decimal
        pair = cls.format_pair(pair)

        order_book = cls.get_market_orders(pair, 1)
        return Decimal(order_book["asks"][0][0]) - Decimal(order_book["bids"][0][0])

