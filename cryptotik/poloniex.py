# -*- coding: utf-8 -*-

from cryptotik.common import (headers, ExchangeWrapper,
                              NormalizedExchangeWrapper)
from cryptotik.exceptions import (InvalidBaseCurrencyError,
                                  InvalidDelimiterError,
                                  APIError,
                                  OutdatedBaseCurrenciesError)
from cryptotik.common import is_sale
import datetime, time
import requests
import hmac, hashlib
from decimal import Decimal


class Poloniex(ExchangeWrapper):

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):

        if apikey is not None and secret is not None:
            self.apikey = apikey.encode("utf-8")
            self.secret = secret.encode("utf-8")

        if proxy:
            assert proxy.startswith('https'), {'Error': 'Only https proxies supported.'}
        self.proxy = {'https': proxy}

        if not timeout:
            self.timeout = (8, 15)
        else:
            self.timeout = timeout

        try:  # at Poloniex, fees may vary per user (https://poloniex.com/fees/)
            self.taker_fee, self.maker_fee = self.get_fee_info()["takerFee"], self.get_fee_info()["makerFee"]
        except:
            self.taker_fee, self.maker_fee = "0.0025", "0.0015"

        self.api_session = requests.Session()

    name = 'poloniex'
    url = 'https://poloniex.com/'
    public_commands = ('returnTicker', 'returnOrderBook', 'returnTradeHistory',
                       'returnChartData', 'return24hVolume', 'returnLoanOrders',
                       'returnCurrencies')

    private_commands = ('returnBalances', 'returnCompleteBalances',
                        'returnDepositAddresses', 'generateNewAddress',
                        'returnDepositsWithdrawals', 'returnOpenOrders',
                        'returnTradeHistory', 'returnAvailableAccountBalances',
                        'returnTradableBalances', 'returnOpenLoanOffers',
                        'returnOrderTrades', 'returnActiveLoans',
                        'returnLendingHistory', 'createLoanOffer',
                        'cancelLoanOffer', 'toggleAutoRenew', 'buy', 'sell',
                        'cancelOrder', 'moveOrder', 'withdraw', 'returnFeeInfo',
                        'transferBalance', 'returnMarginAccountSummary',
                        'marginBuy', 'marginSell', 'getMarginPosition',
                        'closeMarginPosition')

    time_limit = datetime.timedelta(days=35)  # Poloniex will provide just 1 month of data
    delimiter = "_"
    case = "upper"
    headers = headers
    base_currencies = ['btc', 'eth', 'usdt', 'xmr']
    quote_order = 1

    def get_base_currencies(self):
        '''return base markets supported by this exchange.'''

        bases = list(set([i.split('_')[0].lower() for i in self.get_markets()]))
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
        self._nonce = max(int(time.time() * 1000000010), nonce)
        return self._nonce

    @staticmethod
    def _subtract_one_month(t):
        """Return a `datetime.date` or `datetime.datetime` (as given) that is
        one month later.

        Note that the resultant day of the month might change if the following
        month has fewer days:

            >>> _subtract_one_month(datetime.date(2010, 3, 31))
            datetime.date(2010, 2, 28)
        """

        one_day = datetime.timedelta(days=1)
        one_month_earlier = t - one_day
        while one_month_earlier.month == t.month or one_month_earlier.day > t.day:
            one_month_earlier -= one_day
        return one_month_earlier

    @staticmethod
    def _to_timestamp(datetime):
        '''convert datetime to unix timestamp in python2 compatible manner.'''

        try:
            return datetime.timestamp()
        except AttributeError:
            return int(datetime.strftime('%s'))

    @classmethod
    def format_pair(self, pair):
        '''formats pair string in format understood by remote API'''

        if not self.delimiter in pair and len(pair) > 5:
            pair = pair.replace("-", self.delimiter)

        if not pair.isupper():
            pair = pair.upper()

        return pair

    def _verify_response(self, response):
        '''verify if API responded properly and raise apropriate error.'''

        try:
            if "error" in response.json().keys():
                raise APIError(response.json()['error'])
        except AttributeError:  # response has no error key
            pass

    def _generate_signature(self, pdata):

        return hmac.new(self.secret, pdata, hashlib.sha512).hexdigest()

    def api(self, params):
        '''API calls'''

        assert params["command"] in self.public_commands

        try:
            response = self.api_session.get(self.url + "public?", params=params,
                                            headers=self.headers, timeout=self.timeout,
                                            proxies=self.proxy)
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(response)
        return response.json()

    def private_api(self, data):
        '''private API methods which require authentication'''

        assert data["command"] in self.private_commands

        data["nonce"] = self.get_nonce()  # add nonce to post data
        pdata = requests.compat.urlencode(data).encode("utf-8")
        self.headers.update(
            {"Sign": self._generate_signature(pdata),
             "Key": self.apikey
             })

        try:
            response = self.api_session.post(self.url + "tradingApi", data=data,
                                             headers=self.headers, timeout=self.timeout,
                                             proxies=self.proxy)
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(response)
        return response.json()

    def get_markets(self):
        '''return all supported markets.'''

        return [i for i in self.api({"command": 'returnTicker', "currencyPair": 'all'})]

    def get_market_ticker(self, pair):
        '''Returns the ticker for all markets'''

        if pair.lower() != "all":
            return self.api({"command": 'returnTicker'})[self.format_pair(pair)]
        else:
            return self.api({"command": 'returnTicker',
                            "currencyPair": pair.lower()})

    def get_market_trade_history(self, pair, depth=200, since=None,
                                 until=int(time.time())):
        """Requests trade history for >pair<, of <depth> from >since< to >until<
        selected timeframe expressed in seconds (unix time)
        Each request is limited to 50000 trades or 1 year.
        If called without arguments, it will request last 200 trades for the pair."""

        query = {"command": "returnTradeHistory",
                 "currencyPair": self.format_pair(pair)}

        if depth is None:
            depth = 200

        if since is None and depth is not None and depth > 200:
            raise APIError("You can't get depth > 200 without <since> argument.")

        if since is None:  # default, return 200 last trades
            if depth is not None:
                return self.api(query)[-depth:]
            else:
                return self.api(query)

        if since > time.time():
            raise APIError("AYYY LMAO start time is in the future, take it easy.")

        if since is not None and self._to_timestamp(datetime.datetime.now() - self.time_limit) <= since:
            query.update({"start": str(since),
                          "end": str(until)}
                         )
            return self.api(query)

        else:
            raise APIError('''Poloniex API does no support queries for data older than a month.
            Earilest data we can get is since {0} UTC'''.format((
                datetime.datetime.now() - self.time_limit).isoformat())
                            )

    def get_full_market_trade_history(self, pair):
        """get trade history of the last month."""

        start = self._to_timestamp(self._subtract_one_month(datetime.datetime.now()))
        return self.get_market_trade_history(self.format_pair(pair), since=int(start))

    def get_loans(self, coin):
        '''return loan offers for coin'''

        loans = self.api({"command": 'returnLoanOrders',
                         "currency": self.format_pair(coin)
                         })

        return {"demands": loans["demands"], "offers": loans["offers"]}

    def get_loans_depth(self, coin):
        """return loans depth"""

        loans = self.get_loans(coin)
        return {"offers": sum([Decimal(i["amount"]) for i in loans["offers"]]),
                "demands": sum([Decimal(i["amount"]) for i in loans["demands"]])
                }

    def get_market_orders(self, pair, depth=999999):
        '''return order book for the market <pair>'''

        r = self.api({"command": "returnOrderBook",
                     "currencyPair": self.format_pair(pair),
                     "depth": depth
                     })

        return {k: v for k, v in r.items() if k in ['asks', 'bids']}

    def get_market_sell_orders(self, pair, depth=999999):

        return self.get_market_orders(pair, depth)['asks']

    def get_market_buy_orders(self, pair, depth=999999):

        return self.get_market_orders(pair, depth)['bids']

    def get_market_volume(self, pair=None):
        '''Returns the volume for past 24h'''

        q = self.api({"command": 'return24hVolume'})

        if pair:
            return q[self.format_pair(pair)]
        else:
            return q

    def get_markets_status(self):
        ''' Returns additional market info for all markets '''

        return self.api({'command': 'returnCurrencies'})

    def get_order_history(self, pair, since=None, until=int(time.time())):
        """Returns the past 200 trades, or up to 50,000 trades
         between a range specified in UNIX timestamps by the "start" and
         "end" GET parameters."""

        if pair is not "all":
            query = {"command": "returnTradeHistory", "currencyPair": self.format_pair(pair)}
        else:
            query = {"command": "returnTradeHistory", "currencyPair": 'all'}

        if since is None:  # default, return 200 last trades
            return self.private_api(query)

        if since > time.time():
            raise APIError("AYYY LMAO start time is in the future, take it easy.")

        if self._to_timestamp(datetime.datetime.now() - self.time_limit) <= since:
            query.update({"start": str(since),
                          "end": str(until)}
                         )
            return self.private_api(query)

        else:
            raise APIError('''Poloniex API does no support queries for data older than a year.\n
                                Earilest data we can get is since {0} UTC'''.format((datetime.datetime.now() - self.time_limit).isoformat())
                                    )

    def get_balances(self, coin=None):
        '''get balances of my account, <coin> argument is optional'''

        balances = self.private_api({'command': 'returnBalances'})
        if coin:
            return balances[coin.upper()]

        return balances

    def get_available_balances(self):
        '''get available account balances'''

        return self.private_api({'command': 'returnAvailableAccountBalances'})

    def get_margin_account_summary(self):
        """margin account summary"""

        return self.private_api({'command': 'returnMarginAccountSummary'})

    def get_margin_position(self, pair=None):
        """get margin position for <pair> or for all pairs"""

        if pair:
            return self.private_api({'command': 'getMarginPosition',
                                     'currencyPair': self.format_pair(pair)
                                     })

        return self.private_api({'command': 'getMarginPosition'})

    def get_complete_balances(self, account='all'):
        """Returns all of your balances, including available balance,
           balance on orders, and the estimated BTC value of your balance."""

        return self.private_api({'command': 'returnCompleteBalances',
                                 'account': account
                                 })

    def get_new_deposit_address(self, coin):
        """Generates a new deposit address for the currency specified by the
           <coin> parameter."""

        return self.private_api({'command': 'generateNewAddress',
                                 'currency': coin.upper()
                                 })

    def get_deposit_address(self, coin=None):
        """get deposit addresses"""

        if coin:
            return self.private_api({'command': 'returnDepositAddresses'})[coin.upper()]
        else:
            return self.private_api({'command': 'returnDepositAddresses'})[coin.upper()]

    def get_open_orders(self, pair="all"):
        """get your open orders for [pair='all']"""

        orders = self.private_api({'command': 'returnOpenOrders',
                                   'currencyPair': self.format_pair(pair)})

        if pair == "all":
            return {k: v for k, v in orders.items() if v}
        else:
            return orders

    def cancel_all_orders(self):

        orders = self.get_open_orders()

        for i in orders.keys():
            for order in orders[i]:
                self.cancel_order(order['orderNumber'])

    def get_order(self, order_id):
        '''get details about order'''

        open_orders = self.get_open_orders()

        for pair in open_orders.keys():
            for order in open_orders[pair]:
                if order['orderNumber'] == order_id:
                    return order

    def get_deposits_withdrawals(self, since=None, until=int(time.time())):
        """Returns your deposit and withdrawal history within a range,
        specified by the <since> and <until> parameters, both of which should
        be given as UNIX timestamps. (defaults to 1 month)"""

        if not since:
            since = self._to_timestamp(self._subtract_one_month(
                                       datetime.datetime.now()))

        if since > time.time():
            raise APIError("Start time can't be future.")

        return self.private_api({'command': 'returnDepositsWithdrawals',
                                 'start': since,
                                 'end': until})

    def get_deposit_history(self, since=None, until=int(time.time())):
        """Returns deposit history within a range,
        specified by the <since> and <until> parameters."""

        return self.get_deposits_withdrawals(since, until)["deposits"]

    def get_withdraw_history(self, since=None, until=int(time.time())):
        """Returns withdrawal history within a range,
        specified by the <since> and <until> parameters."""

        return self.get_deposits_withdrawals(since, until)["withdrawals"]

    def get_tradable_balances(self):
        """Returns your current tradable balances for each currency in
           each market for which margin trading is enabled."""

        return self.private_api({'command': 'returnTradableBalances'})

    def get_active_loans(self):
        """Returns your active loans for each currency."""

        return self.private_api({'command': 'returnActiveLoans'})

    def get_open_loan_offers(self):
        """Returns your open loan offers for each currency"""

        return self.private_api({'command': 'returnOpenLoanOffers'})

    def get_fee_info(self):
        """If you are enrolled in the maker-taker fee schedule,
        returns your current trading fees and trailing 30-day volume in BTC.
        This information is updated once every 24 hours."""

        return self.private_api({'command': 'returnFeeInfo'})

    def get_lending_history(self, since=None, until=int(time.time()),
                            limit=None):
        '''
        Returns your lending history within a time range specified by the
        <since> and <until> parameters as UNIX timestamps.
        <limit> may also be specified to limit the number of rows returned.
        '''

        if not since:
            since = self.to_timestamp(self.subtract_one_month(datetime.datetime.now()
                                            ))

        if since > time.time():
            raise APIError("Start time can't be future.")

        return self.private_api({'command': 'returnLendingHistory',
                                 'start': since,
                                 'end': until,
                                 'limit': limit})

    def get_order_trades(self, order_id):
        """Returns any trades made from <orderId>"""

        return self.private_api({'command': 'returnOrderTrades', 
                                 'orderNumber': order_id})

    def create_loan_offer(self, coin, amount, rate, auto_renew=0):
        """Creates a loan offer for <coin> for <amount> at <rate>"""

        return self.private_api({'command': 'createLoanOffer',
                                 'currency': coin.upper(),
                                 'amount': amount,
                                 'autoRenew': auto_renew,
                                 'lendingRate': rate
                                 })

    def cancel_loan_offer(self, order_id):
        """Cancels the loan offer with <orderId>"""

        return self.private_api({'command': 'cancelLoanOffer', 
                                 'orderNumber': order_id})

    def toggle_auto_renew(self, order_id):
        """Toggles the 'autorenew' feature on loan <orderId>"""

        return self.private_api({'command': 'toggleAutoRenew',
                                 'orderNumber': order_id})

    def close_margin_position(self, pair):
        """Closes the margin position on <pair>"""

        return self.private_api({'command': 'closeMarginPosition',
                                 'currencyPair': self.format_pair(pair)})

    def buy_margin(self, pair, rate, amount, lending_rate=2):
        """Creates <pair> margin buy order at <rate> for <amount>"""

        return self.private_api({'command': 'marginBuy',
                                 'currencyPair': self.format_pair(pair),
                                 'rate': rate,
                                 'amount': amount,
                                 'lendingRate': lending_rate
                                 })

    def sell_margin(self, pair, rate, amount, lending_rate=2):
        """Creates <pair> margin sell order at <rate> for <amount>"""

        return self.private_api({'command': 'marginSell',
                                'currencyPair': self.format_pair(pair),
                                 'rate': rate,
                                 'amount': amount,
                                 'lendingRate': lending_rate
                                 })

    def buy_limit(self, pair, rate, amount):
        """Creates buy order for <pair> at <rate> for <amount>"""

        return self.private_api({'command': 'buy',
                                 'currencyPair': self.format_pair(pair),
                                 'rate': rate,
                                 'amount': amount
                                 })

    def sell_limit(self, pair, rate, amount):
        """Creates sell order for <pair> at <rate> for <amount>"""

        return self.private_api({'command': 'sell',
                                 'currencyPair': self.format_pair(pair),
                                 'rate': rate,
                                 'amount': amount
                                 })

    def cancel_order(self, order_id):
        """Cancels order <orderId>"""

        return self.private_api({'command': 'cancelOrder',
                                 'orderNumber': order_id
                                 })

    def move_order(self, order_id, rate, amount):
        """Cancels an order and places a new one of the same type in a single
           atomic transaction, meaning either both operations will succeed
           or both will fail."""

        return self.private_api({'command': 'moveOrder',
                                 'orderNumber': order_id,
                                 'rate': rate,
                                 'amount': amount
                                 })

    def withdraw(self, coin, amount, address):
        """Withdraws <coin> <amount> to <address>"""

        return self.private_api({'command': 'withdraw',
                                 'currency': coin.upper(),
                                 'amount': amount,
                                 'address': address
                                 })

    def transfer_balance(self, coin, amount, fromac, toac):
        """Transfers coins between accounts (exchange, margin, lending)
        - moves <coin> <amount> from <fromac> to <toac>"""

        return self.private_api({'command': 'transferBalance',
                                 'currency': coin.upper(),
                                 'amount': amount,
                                 'fromAccount': fromac,
                                 'toAccount': toac
                                 })


class PoloniexNormalized(Poloniex, NormalizedExchangeWrapper):

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        super(PoloniexNormalized, self).__init__(apikey, secret, timeout, proxy)

    @staticmethod
    def _string_to_datetime(string):
        '''convert datetime string to datetime object'''

        return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

    @classmethod
    def format_pair(self, market_pair):
        """
        Expected input is quote - base.
        Normalize the pair inputs and
        format the pair argument to a format understood by the remote API."""

        if "-" not in market_pair:
            raise InvalidDelimiterError('Agreed upon delimiter is "-".')

        quote, base = market_pair.split('-')

        if base not in self.base_currencies:
            raise InvalidBaseCurrencyError('''Expected input is quote-base, you have provided with {pair}'''.format(pair=market_pair))

        return base.upper() + self.delimiter + quote.upper()  # for poloniex quote comes second

    def get_markets(self):
        '''normalized Poloniex.get_markets'''

        m = []
        for i in super(PoloniexNormalized, self).get_markets():
            base, quote = i.split('_')
            m.append(quote.lower() + '-' + base.lower())

        return m

    def get_market_ticker(self, market):

        ticker = super(PoloniexNormalized, self).get_market_ticker(market)

        return {'ask': float(ticker['lowestAsk']),
                'bid': float(ticker['highestBid']),
                'last': float(ticker['last'])
                }

    def get_market_trade_history(self, market, depth=100):

        upstream = super(PoloniexNormalized, self).get_market_trade_history(market, depth)
        downstream = []

        for data in upstream:

            downstream.append({
                'timestamp': self._string_to_datetime(data['date']),
                'is_sale': is_sale(data['type']),
                'rate': float(data['rate']),
                'amount': float(data['amount']),
                'trade_id': data['globalTradeID']
            })

        return downstream

    def get_market_orders(self, market, depth=100):
        '''
        :return:
            dict['bids': list[price, quantity],
                 'asks': list[price, quantity]
                ]
        bids[0] should be first next to the spread
        asks[0] should be first next to the spread
        '''
        return super(PoloniexNormalized, self).get_market_orders(market, depth)

    def get_market_sell_orders(self, market, depth=100):
        '''
        :return:
            list[price, quantity]
        '''
        return super(PoloniexNormalized, self).get_market_orders(market, depth)['asks']

    def get_market_buy_orders(self, market, depth=100):
        '''
        :return:
            list[price, quantity]
        '''
        return super(PoloniexNormalized, self).get_market_orders(market, depth)['bids']

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
