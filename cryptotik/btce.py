# -*- coding: utf-8 -*-

import requests
from decimal import Decimal
from .common import APIError, headers
import hmac
import hashlib

class Btce:

    def __init__(self, apikey=None, secret=None, timeout=None):

        if apikey:
            self.apikey = apikey.encode("utf-8")
            self.secret = secret.encode("utf-8")
        self.nonce = 1

    api_session = requests.Session()

    public_commands = ("info", "ticker", "depth", "trades")
    private_commands = ("getInfo", "Trade", "ActiveOrders", "OrderInfo",
                        "CancelOrder", "TradeHistory", "TransHistory",
                        "WithdrawCoin", "CreateCuopon", "RedeemCuopon")

    url = 'https://btc-e.com/api/3/'
    trade_url = 'https://btc-e.com/tapi/'
    delimiter = "_"
    case = "lower"
    headers = headers
    maker_fee, taker_fee = 0.002, 0.002
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

        result = cls.api_session.get(cls.url + command, headers=cls.headers,
                                     timeout=cls.timeout)

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

        result = requests.post(self.trade_url, data=params, headers=headers,
                               timeout=self.timeout)

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
    def get_market_orders(cls, pair, depth=None):
        """returns market order book on selected pair"""

        pair = cls.format_pair(pair)

        if depth == None:
            return cls.api("depth" + "/" + pair)[pair]

        if depth > 5000:
            raise ValueError("Btce API allows maximum depth of 5000 orders")

        return cls.api("depth" + "/" + pair + "/?limit={0}".format(depth))[pair]

    @classmethod
    def get_market_trade_history(cls, pair, limit=1000):
        """get market trade history"""

        pair = cls.format_pair(pair)

        if limit > 2000:
            raise APIError("Btc-e API can only return last 2000 trades.")

        if not isinstance(pair, list):
            return cls.api("trades" + "/" + pair + "/?limit={0}".format(limit))[pair]

        if pair == "all":  # returns market history for all pairs with default history size.
            return cls.api("trades" + "/" + "-".join(cls.get_markets() + "/?limit={0}".format(limit)))

        else:  # simply concat pairs in the list
            return cls.api("trades" + "/" + "-".join(pair) + "/?limit={0}".format(limit))

    @classmethod
    def get_market_depth(cls, pair):
        """get market order book depth"""

        pair = cls.format_pair(pair)
        order_book = cls.get_market_orders(pair, 5000)
        return {"bids": sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]]),
                "asks": sum([Decimal(i[1]) for i in order_book["asks"]])}

    @classmethod
    def get_market_spread(cls, pair):
        """get market spread"""

        pair = cls.format_pair(pair)

        order_book = cls.get_market_orders(pair, 1)
        return Decimal(order_book["asks"][0][0]) - Decimal(order_book["bids"][0][0])

    ####################
    # Private commands
    ####################

    def get_balances(self):
        '''
        Returns information about the user’s current balance, API-key privileges,
        the number of open orders and Server Time.
        '''

        return self.private_api({"method": "getInfo"})

    def buy(self, pair, rate, amount):
        '''submit spot buy order
        Expected result:

        * received: The amount of currency bought/sold.
        * remains: The remaining amount of currency to be bought/sold (and the initial order amount).
        * order_id: Is equal to 0 if the request was fully “matched” by the opposite orders, otherwise the ID of the executed order will be returned.
        * funds: Balance after the request.
        '''

        return self.private_api({"method": "Trade",
                                 "type": "buy",
                                 "pair": self.format_pair(pair),
                                 "amount": amount,
                                 "rate": rate
                                })

    def sell(self, pair, rate, amount):
        '''submit spot sell order
        Expected result:

        * received: The amount of currency bought/sold.
        * remains: The remaining amount of currency to be bought/sold (and the initial order amount).
        * order_id: Is equal to 0 if the request was fully “matched” by the opposite orders, otherwise the ID of the executed order will be returned.
        * funds: Balance after the request.
        '''

        return self.private_api({"method": "Trade",
                                 "type": "sell",
                                 "pair": self.format_pair(pair),
                                 "amount": amount,
                                 "rate": rate
                                })

    def cancel_order(self, order_id):
        '''cancel order by <order_id>
        Expected result:

        * order_id: The ID of canceled order.
        * funds: Balance upon request.
        '''

        return self.private_api({"method": "CancelOrder",
                                 "order_id": order_id
                                })

    def get_open_orders(self, pair=None):
        '''get open orders
        Expected result:

        Array key : Order ID.
        pair: The pair on which the order was created.
        type: Order type, buy/sell.
        amount: The amount of currency to be bought/sold.
        rate: Sell/Buy price.
        timestamp_created: The time when the order was created.
        '''

        if pair:
            return self.private_api({"method": "ActiveOrders", "pair": self.format_pair(pair)})
        else:
            return self.private_api({"method": "ActiveOrders"})

    def get_order_info(self, order_id):
        '''get order information'''

        return self.private_api({"method": "OrderInfo", "order_id": order_id})

    def withdraw(self, coin, amount, address):
        '''withdraw cryptocurrency
        Expected result:

        tId: Transaction ID.
        amountSent: The amount sent including commission.
        funds: Balance after the request.
        '''

        return self.private_api({"method": "WithdrawCoin",
                                 "coinName": coin.upper(),
                                 "amount": amount,
                                 "address": address})
