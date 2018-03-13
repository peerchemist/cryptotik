# -*- coding: utf-8 -*-

import requests
from decimal import Decimal
import time
from cryptotik.common import is_sale
from cryptotik.common import (headers, ExchangeWrapper,
                              NormalizedExchangeWrapper)
from cryptotik.exceptions import (InvalidBaseCurrencyError,
                                  InvalidDelimiterError,
                                  APIError,
                                  OutdatedBaseCurrenciesError)
import hmac
import hashlib
from datetime import datetime


class Wex(ExchangeWrapper):

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):

        if apikey:
            self.apikey = apikey.encode("utf-8")
            self.secret = secret.encode("utf-8")

        if proxy:
            assert proxy.startswith('https'), {'Error': 'Only https proxies supported.'}
        self.proxy = {'https': proxy}

        if not timeout:
            self.timeout = (8, 15)
        else:
            self.timeout = timeout

        self.api_session = requests.Session()

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
    base_currencies = ['eur', 'dsh', 'ltc', 'usd', 'rur', 'zec', 'btc']
    quote_order = 0

    def get_base_currencies(self):
        '''return base markets supported by this exchange.'''

        markets = [i for i in self.get_markets() if "et" not in i]  # drop tokens
        bases = list(set([i.split('_')[1].lower() for i in markets]))
        try:
            assert sorted(bases) == sorted(self.base_currencies)
        except AssertionError:
            raise OutdatedBaseCurrenciesError('Update the hardcoded base currency clist!',
                                              {'actual': bases,
                                               'hardcoded': self.base_currencies})

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

    def _verify_response(self, response):
        '''verify if API responded properly and raise apropriate error.'''

        if not response.json()['success'] is 1:
            raise APIError(response.json()['error'])

    def _generate_signature(self, params):

        return hmac.new(self.secret,
                        params.encode("utf-8"),
                        hashlib.sha512).hexdigest()

    def api(self, command):
        """call remote API"""

        try:

            result = self.api_session.get(self.url + command, headers=self.headers,
                                          timeout=self.timeout, proxies=self.proxy)

            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        return result.json()

    def private_api(self, params):
        '''handles private api methods'''

        params["nonce"] = self.get_nonce()
        encoded_params = requests.compat.urlencode(params)

        self.headers.update({
            "Key": self.apikey,
            "Sign": self._generate_signature(encoded_params)
        })

        try:
            result = self.api_session.post(self.trade_url, data=params, headers=headers,
                                           timeout=self.timeout, proxies=self.proxy)

            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(result)
        return result.json()

    def get_markets(self):
        '''get all pairs supported by the exchange'''

        q = self.api("info")
        return list(q['pairs'].keys())

    def get_market_ticker(self, pair):
        """return ticker for market"""

        pair = self.format_pair(pair)
        return self.api("ticker" + "/" + pair)[pair]

    def get_market_orders(self, pair, depth=100):
        """returns market order book on selected pair."""

        pair = self.format_pair(pair)

        if depth == None:
            return self.api("depth" + "/" + pair)[pair]

        if depth > 5000:
            raise ValueError("Wex API allows maximum depth of 5000 orders")

        return self.api("depth" + "/" + pair + "/?limit={0}".format(depth))[pair]

    def get_market_sell_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['asks']

    def get_market_buy_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['bids']

    def get_market_trade_history(self, pair, limit=1000):
        """get market trade history"""

        pair = self.format_pair(pair)

        if limit > 2000:
            raise APIError("Btc-e API can only return last 2000 trades.")

        if not isinstance(pair, list):
            return self.api("trades" + "/" + pair + "/?limit={0}".format(limit))[pair]

        if pair == "all":  # returns market history for all pairs with default history size.
            return self.api("trades" + "/" + "-".join(cls.get_markets() + "/?limit={0}".format(limit)))

        else:  # simply concat pairs in the list
            return self.api("trades" + "/" + "-".join(pair) + "/?limit={0}".format(limit))

    def get_market_volume(self, pair):
        '''return market volume [of last 24h]'''

        pair = self.format_pair(pair)
        smry = self.get_market_ticker(pair)

        return {pair.split(self.delimiter)[1].upper(): smry['vol'],
                pair.split(self.delimiter)[0].upper(): smry['vol_cur']}

    def get_balances(self):
        '''
        Returns information about the user’s current balance, API-key privileges,
        the number of open orders and Server Time.
        '''

        return self.private_api({"method": "getInfo"})['return']['funds']

    def get_deposit_address(self, coin=None):
        '''get deposit address'''

        return self.private_api({"method": "CoinDepositAddress", "coinName": coin})['return']

    def buy_limit(self, pair, rate, amount):
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

    def sell_limit(self, pair, rate, amount):
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


class WexNormalized(Wex, NormalizedExchangeWrapper):

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        super(WexNormalized, self).__init__(apikey, secret, timeout, proxy)

    @staticmethod
    def _tstamp_to_datetime(timestamp):
        '''convert unix timestamp to datetime'''

        return datetime.fromtimestamp(timestamp)

    @classmethod
    def format_pair(self, market_pair):
        """
        Expected input is quote - base.
        Normalize the pair inputs and
        format the pair argument to a format understood by the remote API."""

        market_pair = market_pair.lower()  # wex takes lowercase

        if "-" not in market_pair:
            raise InvalidDelimiterError('Agreed upon delimiter is "-".')

        quote, base = market_pair.split('-')

        if base not in self.base_currencies:
            raise InvalidBaseCurrencyError('''Expected input is quote-base, you have provided with {pair}'''.format(pair=market_pair))

        return quote + self.delimiter + base  # for wex quote comes first

    def get_markets(self):

        upstream = super(WexNormalized, self).get_markets()

        return [i.replace('_', ('-')) for i in upstream if "et_" not in i]

    def get_market_ticker(self, market):

        ticker = super(WexNormalized, self).get_market_ticker(market)

        return {
            'ask': ticker['sell'],
            'bid': ticker['buy'],
            'last': ticker['last']
        }

    def get_market_trade_history(self, market, depth=100):

        upstream = super(WexNormalized, self).get_market_trade_history(market, depth)
        downstream = []

        for data in upstream:

            downstream.append({
                    'timestamp': self._tstamp_to_datetime(data['timestamp']),
                    'is_sale': is_sale(data['type']),
                    'rate': data['price'],
                    'amount': data['amount'],
                    'trade_id': data['tid']
            })

        return downstream

    def get_market_orders(self, market, depth=100):

        return super(WexNormalized, self).get_market_orders(market, depth)

    def get_market_sell_orders(self, market, depth=100):

        return self.get_market_orders(market, depth)['asks']

    def get_market_buy_orders(self, market, depth=100):

        return self.get_market_orders(market, depth)['bids']

    def get_market_depth(self, market):
        '''return sum of all bids and asks'''

        order_book = self.get_market_orders(market)
        return {"bids": sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]]),
                "asks": sum([Decimal(i[1]) for i in order_book["asks"]])
                }

    def get_market_spread(self, market):
        '''returns market spread'''

        order_book = self.get_market_orders(market, 1)
        ask = order_book["asks"][0][0]
        bid = order_book["bids"][0][0]

        return Decimal(ask) - Decimal(bid)
