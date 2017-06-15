# -*- coding: utf-8 -*-

from .common import APIError, headers
import datetime, time
import requests
import hmac, hashlib
from decimal import Decimal


class Poloniex:

    def __init__(self, apikey=None, secret=None, timeout=130):
        '''
        Initialize class when you want to use private commands.
        '''

        if apikey is not None and secret is not None:
            self.apikey = apikey.encode("utf-8")
            self.secret = secret.encode("utf-8")
            self.nonce = int(time.time()) * 1000000010
            self.timeout = timeout

    url = 'https://poloniex.com/'
    public_commands = ['returnTicker', 'returnOrderBook', 'returnTradeHistory',
                       'returnChartData', 'return24hVolume', 'returnLoanOrders',
                       'returnCurrencies']

    private_commands = ['returnBalances', 'returnCompleteBalances',
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
                        'closeMarginPosition']

    time_limit = datetime.timedelta(days=365)  # Poloniex will provide just 1 year of data
    delimiter = "_"
    case = "upper"
    headers = headers
    try:  # at Poloniex, fees may vary per user (https://poloniex.com/fees/)
        taker_fee, maker_fee = self.get_fee_info()["takerFee"], self.get_fee_info()["makerFee"]
    except:
        taker_fee, maker_fee = "0.0025", "0.0015"

    try:
        assert timeout is not None
    except:
        timeout = (8, 15)

    api_session = requests.Session()

    @property
    def get_nonce(self):
        '''return nonce integer'''

        self.nonce += 17
        return self.nonce

    @staticmethod
    def subtract_one_month(t):
        """Return a `datetime.date` or `datetime.datetime` (as given) that is
        one month later.

        Note that the resultant day of the month might change if the following
        month has fewer days:

            >>> subtract_one_month(datetime.date(2010, 3, 31))
            datetime.date(2010, 2, 28)
        """

        one_day = datetime.timedelta(days=1)
        one_month_earlier = t - one_day
        while one_month_earlier.month == t.month or one_month_earlier.day > t.day:
            one_month_earlier -= one_day
        return one_month_earlier

    @staticmethod
    def to_timestamp(datetime):
        '''convert datetime to unix timestamp in python2 compatible manner.'''

        try:
            return datetime.timestamp()
        except AttributeError:
            return int(datetime.strftime('%s'))

    @classmethod
    def format_pair(cls, pair):
        '''formats pair string in format understood by remote API'''

        if not cls.delimiter in pair and len(pair) > 5:
            pair = pair.replace("-", cls.delimiter)

        if not pair.isupper():
            pair = pair.upper()

        return pair

    @classmethod
    def api(cls, params):
        '''API calls'''

        assert params["command"] in cls.public_commands

        try:
            result = cls.api_session.get(cls.url + "public?", params=params,
                                         headers=cls.headers, timeout=cls.timeout)
            assert result.status_code == 200
            return result.json()
        except requests.exceptions.RequestException as e:
            raise APIError(e)

    def private_api(self, data):
        '''private API methods which require authentication'''

        assert data["command"] in self.private_commands

        if not self.apikey or not self.secret:
            raise ValueError("A Key and Secret needed!")

        data["nonce"] = self.get_nonce  # add nonce to post data
        pdata = requests.compat.urlencode(data).encode("utf-8")
        self.headers.update(
            {"Sign": hmac.new(self.secret, pdata, hashlib.sha512).hexdigest(),
             "Key": self.apikey
             })

        try:
            result = requests.post(self.url + "tradingApi", data=data,
                                   headers=self.headers, timeout=self.timeout)
            #assert result.status_code == 200
            return result.json()
        except requests.exceptions.RequestException as e:
            return APIError(e)

    ### Public methods ##

    @classmethod
    def get_markets(cls):
        '''return all supported markets.'''

        return [i for i in cls.get_market_ticker("all")]

    @classmethod
    def get_market_ticker(cls, pair):
        '''Returns the ticker for all markets'''

        if pair.lower() != "all":
            return cls.api({"command": 'returnTicker'})[cls.format_pair(pair)]
        else:
            return cls.api({"command": 'returnTicker',
                            "currencyPair": pair.lower()})

    @classmethod
    def get_market_trade_history(cls, pair, since=None, until=int(time.time())):
        """Requests trade history for >pair< from >since< to >until< selected
           timeframe expressed in seconds (unix time)\n
           Each request is limited to 50000 trades or 1 year.\n
           If called without arguments, it will request last 200 trades for the pair."""

        query = {"command": "returnTradeHistory",
                 "currencyPair": cls.format_pair(pair)}

        if since is None:  # default, return 200 last trades
            return cls.api(query)

        if since > time.time():
            raise APIError("AYYY LMAO start time is in the future, take it easy.")

        if cls.to_timestamp(datetime.datetime.now() - cls.time_limit) <= since:
            query.update({"start": str(since),
                          "end": str(until)}
                         )
            return cls.api(query)

        else:
            raise APIError('''Poloniex API does no support queries for data older than a year.\n
            Earilest data we can get is since {0} UTC'''.format((
                datetime.datetime.now() - cls.time_limit).isoformat())
                            )

    @classmethod
    def get_full_market_trade_history(cls, pair):
        """get full (maximium) trade history for this pair from one year ago
        until now, or last 50k trades - whichever comes first."""

        start = cls.to_timestamp(datetime.datetime.now() - cls.time_limit) + 1
        return cls.get_market_trade_history(cls.format_pair(pair), int(start))

    @classmethod
    def get_loans(cls, coin):
        '''return loan offers for coin'''

        loans = cls.api({"command": 'returnLoanOrders',
                         "currency": cls.format_pair(coin)
                         })

        return {"demands": loans["demands"], "offers": loans["offers"]}

    @classmethod
    def get_loans_depth(cls, coin):
        """return loans depth"""

        loans = cls.get_loans(coin)
        return {"offers": sum([Decimal(i["amount"]) for i in loans["offers"]]),
                "demands": sum([Decimal(i["amount"]) for i in loans["demands"]])
                }

    @classmethod
    def get_market_orders(cls, pair, depth=999999):
        '''return order book for the market'''

        return cls.api({"command": "returnOrderBook",
                        "currencyPair": cls.format_pair(pair),
                        "depth": depth
                        })

    @classmethod
    def get_market_depth(cls, pair):
        '''return sum of all bids and asks'''

        order_book = cls.get_market_orders(cls.format_pair(pair))
        asks = sum([Decimal(i[1]) for i in order_book["asks"]])
        bid = sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]])

        return {"bids": bid, "asks": asks}  # bids are expressed in base pair

    @classmethod
    def get_market_spread(cls, pair):
        '''returns market spread'''

        order_book = cls.get_market_orders(cls.format_pair(pair), 1)
        ask = order_book["asks"][0][0]
        bid = order_book["bids"][0][0]

        return Decimal(ask) - Decimal(bid)

    @classmethod
    def get_market_volume(cls, pair=None):
        '''Returns the volume for past 24h'''

        q = cls.api({"command": 'return24hVolume'})

        if pair:
            return q[cls.format_pair(pair)]
        else:
            return q

    @classmethod
    def get_markets_status(cls):
        ''' Returns additional market info for all markets '''

        return cls.api({'command': 'returnCurrencies'})

    ### Private methods ##

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

        if self.to_timestamp(datetime.datetime.now() - self.time_limit) <= since:
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

    def generate_new_address(self, coin):
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

        return self.private_api({'command': 'returnOpenOrders', 
                                 'currencyPair': self.format_pair(pair)})

    def get_deposits_withdrawals(self, since=None, until=int(time.time())):
        """Returns your deposit and withdrawal history within a range,
        specified by the <since> and <until> parameters, both of which should
        be given as UNIX timestamps. (defaults to 1 month)"""

        if not since:
            since = self.to_timestamp(self.subtract_one_month(
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

    def get_withdrawal_history(self, since=None, until=int(time.time())):
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

    def margin_buy(self, pair, rate, amount, lending_rate=2):
        """Creates <pair> margin buy order at <rate> for <amount>"""

        return self.private_api({'command': 'marginBuy',
                                 'currencyPair': self.format_pair(pair),
                                 'rate': rate,
                                 'amount': amount,
                                 'lendingRate': lending_rate
                                 })

    def margin_sell(self, pair, rate, amount, lending_rate=2):
        """Creates <pair> margin sell order at <rate> for <amount>"""

        return self.private_api({'command': 'marginSell',
                                'currencyPair': self.format_pair(pair),
                                 'rate': rate,
                                 'amount': amount,
                                 'lendingRate': lending_rate
                                 })

    def buy(self, pair, rate, amount):
        """Creates buy order for <pair> at <rate> for <amount>"""

        return self.private_api({'command': 'buy',
                                 'currencyPair': self.format_pair(pair),
                                 'rate': rate,
                                 'amount': amount
                                 })

    def sell(self, pair, rate, amount):
        """Creates sell order for <pair> at <rate> for <amount>"""

        return self.private_api({'command': 'sell',
                                 'currencyPair': self.format_pair(pair),
                                 'rate': rate,
                                 'amount': amount
                                 })

    def cancel_order(self, order_id):
        """Cancels order <orderId>"""

        return self.private_api('cancelOrder', {'orderNumber': order_id})

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

