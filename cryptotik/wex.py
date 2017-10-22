# -*- coding: utf-8 -*-

import requests
from decimal import Decimal
import time
from cryptotik.common import APIError, headers, ExchangeWrapper
import hmac
import hashlib


class Wex(ExchangeWrapper):

    def __init__(self, apikey=None, secret=None, timeout=None):

        if apikey:
            self.apikey = apikey.encode("utf-8")
            self.secret = secret.encode("utf-8")

    api_session = requests.Session()

    public_commands = ("info", "ticker", "depth", "trades")
    private_commands = ("getInfo", "Trade", "ActiveOrders", "OrderInfo",
                        "CancelOrder", "TradeHistory", "TransHistory",
                        "WithdrawCoin", "CreateCuopon", "RedeemCuopon")

    name = 'wex'
    url = 'https://wex.nz/api/3/'
    trade_url = 'https://wex.nz/tapi/'
    delimiter = "_"
    case = "lower"
    headers = headers
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

        params["nonce"] = self.get_nonce()
        encoded_params = requests.compat.urlencode(params)

        sig = hmac.new(self.secret,
                       encoded_params.encode("utf-8"),
                       hashlib.sha512)

        self.headers.update({
            "Key": self.apikey,
            "Sign": sig.hexdigest()
        })

        result = self.api_session.post(self.trade_url, data=params, headers=headers,
                                       timeout=self.timeout)

        assert result.status_code == 200, {"error": "http_error: " + str(result.status_code)}
        if result.json()['success'] != 1:
            raise ValueError(result.json()['error'])
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
        return cls.api("ticker" + "/" + pair)[pair]

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

    @classmethod
    def get_market_volume(cls, pair):
        '''return market volume [of last 24h]'''

        pair = cls.format_pair(pair)
        smry = cls.get_market_ticker(pair)

        return {pair.split(cls.delimiter)[1].upper(): smry['vol'], pair.split(cls.delimiter)[0].upper(): smry['vol_cur']}

    ####################
    # Private commands
    ####################

    def get_balances(self):
        '''
        Returns information about the user’s current balance, API-key privileges,
        the number of open orders and Server Time.
        '''

        return self.private_api({"method": "getInfo"})['return']['funds']

    def get_deposit_address(self, coin=None):
        '''get deposit address'''

        return self.private_api({"method": "CoinDepositAddress", "coinName": coin})['return']

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
                                })['return']

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
                                })['return']

    def cancel_order(self, order_id):
        '''cancel order by <order_id>
        Expected result:

        * order_id: The ID of canceled order.
        * funds: Balance upon request.
        '''

        return self.private_api({"method": "CancelOrder",
                                 "order_id": order_id
                                })['return']

    def cancel_all_orders(self):
        '''cancel all active orders'''

        raise NotImplementedError

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
            return self.private_api({"method": "ActiveOrders", "pair": self.format_pair(pair)})['return']
        else:
            return self.private_api({"method": "ActiveOrders"})['return']

    def get_order(self, order_id):
        '''get order information'''

        return self.private_api({"method": "OrderInfo", "order_id": order_id})['return']

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
                                 "address": address})['return']

    def get_transaction_history(self, since=1, until=time.time()):
        '''Returns the history of transactions.

        since: the time to start the display [unix timestamp]
        until: the time to end the display [unix timestamp]
        '''

        try:
            txn_history = self.private_api({"method": "TransHistory",
                                            "since": since,
                                            "end": int(until)})['return']
            return txn_history

        except ValueError:
            return {}

    def get_deposit_history(self, coin=None):
        '''get deposit history'''

        hist = {k: v for k, v in self.get_transaction_history().items() if  v['type'] == 1}

        if coin:
            return {k: v for k, v in hist.items() if v['currency'] == coin.upper()}

        return hist

    def get_withdraw_history(self, coin=None):
        '''get withdrawals history'''

        hist = {k: v for k, v in self.get_transaction_history().items() if  v['type'] == 2}

        if coin:
            return {k: v for k, v in hist.items() if v['currency'] == coin.upper()}

        return hist
