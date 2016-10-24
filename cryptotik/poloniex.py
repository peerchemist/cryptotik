from .common import APIError, headers
import datetime, time
import requests
import hmac, hashlib

class Poloniex:

    url = 'https://poloniex.com/'
    public_commands = ['returnTicker', 'returnOrderBook', 'returnTradeHistory', 'returnChartData',
                        'return24hVolume', 'returnLoanOrders']

    private_commands = ['returnBalances', 'returnCompleteBalances', 'returnDepositAddresses',
                        'generateNewAddress', 'returnDepositsWithdrawals', 'returnOpenOrders',
                        'returnTradeHistory', 'returnAvailableAccountBalances', 'returnTradableBalances',
                        'returnOpenLoanOffers', 'returnOrderTrades', 'returnActiveLoans',
                        'returnLendingHistory', 'createLoanOffer', 'cancelLoanOffer', 'toggleAutoRenew',
                        'buy', 'sell', 'cancelOrder', 'moveOrder', 'withdraw', 'returnFeeInfo',
                        'transferBalance', 'returnMarginAccountSummary', 'marginBuy', 'marginSell',
                        'getMarginPosition', 'closeMarginPosition']

    def __init__(self, key, secret):
        self.key = key.encode("utf-8")
        self.secret = secret.encode("utf-8")
        self.nonce = int(time.time())

    time_limit = datetime.timedelta(days=365) # Poloniex will provide just 1 year of data
    delimiter = "_"
    case = "upper"
    headers = headers
    try:
        taker_fee, maker_fee = self.get_fee_info()["takerFee"], self.get_fee_info()["makerFee"]
    except:
        taker_fee, maker_fee = "0.0025", "0.0025"

    @property
    def get_nonce(self):
        '''return nonce integer'''

        self.nonce += 1
        return self.nonce

    @classmethod
    def format_pair(cls, pair):
        '''formats pair string in format understood by remote API'''

        if not cls.delimiter in pair and len(pair) > 5:
            pair = pair.replace("-", cls.delimiter)

        if not pair.isupper():
            return pair.upper()
        else:
            return pair

    @classmethod
    def api(cls, params):
        '''API calls'''

        assert params["command"] in cls.public_commands

        try:
            result = requests.get(cls.url + "public?", params=params, headers=cls.headers, timeout=3)
            assert result.status_code == 200
            return result.json()
        except requests.exceptions.RequestException as e:
            print("Error!", e)

    def private_api(self, data):
        '''private API methods which require authentication'''

        assert data["command"] in self.private_commands

        if not self.key or not self.secret:
            raise ValueError("A Key and Secret needed!")

        data["nonce"] = self.get_nonce ## add nonce to post data
        pdata = requests.compat.urlencode(data).encode("utf-8")
        _headers = self.headers
        _headers["Sign"] = hmac.new(self.secret, pdata, hashlib.sha512).hexdigest()
        _headers["Key"] = self.key

        try:
            result = requests.post(self.url + "tradingApi", data=data,
                                headers=_headers, timeout=3)
            assert result.status_code == 200
            return result.json()
        except requests.exceptions.RequestException as e:
            print("Error!", e)

    ### Public methods ##

    @classmethod
    def get_markets(cls):
        '''return all supported markets.'''

        markets = [i for i in cls.get_market_ticker("all")]
        base_pairs = set([i.split(cls.delimiter)[0] for i in markets])
        market_pairs = set([i.split(cls.delimiter)[1] for i in markets])

        return {"base": base_pairs, "market_pairs": market_pairs,
                "markets": markets}

    @classmethod
    def get_market_ticker(cls, pair):
        '''Returns the ticker for all markets'''

        if pair.lower() != "all":
            return cls.api({"command": 'returnTicker'})[cls.format_pair(pair)]
        else:
            return cls.api({"command": 'returnTicker', "currencyPair": pair.lower()})

    @classmethod
    def get_market_trade_history(cls, pair, since=None, until=int(time.time())):
        """Requests trade history for >pair< from >since< to >until< selected timeframe expressed in seconds (unix time)\n
            Each request is limited to 50000 trades or 1 year.\n
            If called without arguments, it will requets last 200 trades for the pair."""

        query = {"command": "returnTradeHistory", "currencyPair": cls.format_pair(pair)}

        if since is None: # default, return 200 last trades
            return cls.api(query)

        if since > time.time():
            raise APIError("AYYY LMAO start time is in the future, take it easy.")

        if (datetime.datetime.now() - cls.time_limit).timestamp() <= since:
            query.update({"start": str(since),
                            "end": str(until)}
                            )
            return cls.api(query)

        else:
            raise APIError('''Poloniex API does no support queries for data older than a year.\n
                                Earilest data we can get is since {0} UTC'''.format((datetime.datetime.now() - cls.time_limit).isoformat())
                                    )

    @classmethod
    def get_full_market_trade_history(cls, pair):
        """get full (maximium) trade history for this pair from one year ago until now, or last 50k trades - whichever comes first."""

        start = (datetime.datetime.now() - cls.time_limit).timestamp() + 1
        return cls.get_market_trade_history(cls.format_pair(pair), int(start))

    @classmethod
    def get_loans(cls, coin):
        '''return loan offers for coin'''

        loans = cls.api({"command": 'returnLoanOrders',
                         "currency": cls.format_pair(coin)
                        })
        return {"demands": loans["demands"], "offers": loans["offers"]}

    @classmethod
    def get_loan_depth(cls, coin):
        """return loans depth"""
        from decimal import Decimal

        loans = cls.get_loans(coin)
        return {"offers": sum([Decimal(i["amount"]) for i in loans["offers"]]),
                "demands": sum([Decimal(i["amount"]) for i in loans["demands"]])
                }

    @classmethod
    def get_market_order_book(cls, pair, depth=999999):
        '''return order book for the market'''

        return cls.api({"command": "returnOrderBook",
                        "currencyPair": cls.format_pair(pair),
                        "depth": depth
                        })

    @classmethod
    def get_market_depth(cls, pair):
        '''return sum of all bids and asks'''

        from decimal import Decimal

        order_book = cls.get_market_order_book(cls.format_pair(pair))
        asks = sum([Decimal(i[1]) for i in order_book["asks"]])
        bid = sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]])

        return {"bids": bid, "asks": asks} ## bids are expressed in base pair

    @classmethod
    def get_market_spread(cls, pair):
        '''returns market spread'''

        from decimal import Decimal

        order_book = cls.get_market_order_book(cls.format_pair(pair), 1)
        ask = order_book["asks"][0][0]
        bid = order_book["bids"][0][0]

        return Decimal(ask) - Decimal(bid)
    
    @classmethod
    def get_market_volume(cls, pair=None):
        '''Returns the volume for past 24h'''

        q = cls.api({"command": 'return24hVolume'})
        
        if pair != None:
            return q[cls.format_pair(pair)]
        else:    
            return q
    
    @classmethod
    def get_markets_status(cls):
        ''' Returns additional market info for all markets '''

        return cls.api({'command': 'returnCurrencies'})

    ### Private methods ##

    def get_account_trade_history(self, pair, since=None, until=int(time.time())):
        """Returns the past 200 trades, or up to 50,000 trades
         between a range specified in UNIX timestamps by the "start" and "end" GET parameters."""

        if pair is not "all":
            query = {"command": "returnTradeHistory", "currencyPair": self.format_pair(pair)}
        else:
            query = {"command": "returnTradeHistory", "currencyPair": 'all'}

        if since is None: # default, return 200 last trades
            return self.private_api(query)

        if since > time.time():
            raise APIError("AYYY LMAO start time is in the future, take it easy.")

        if (datetime.datetime.now() - self.time_limit).timestamp() <= since:
            query.update({"start": str(since),
                            "end": str(until)}
                            )
            return self.private_api(query)

        else:
            raise APIError('''Poloniex API does no support queries for data older than a year.\n
                                Earilest data we can get is since {0} UTC'''.format((datetime.datetime.now() - self.time_limit).isoformat())
                                    )

    def get_balances(self, pair):
        '''get balances of my account'''
        if pair:
            return self.private_api({'command': 'returnBalances'})[self.format_pair(pair)]
        return self.private_api({'command': 'returnBalances'})

    def get_available_balances(self):
        '''get available account balances'''
        return self.private_api({'command': 'returnAvailableAccountBalances'})

    def get_margin_account_summary(self):
        """margin account summary"""
        return self.private_api({'command': 'returnMarginAccountSummary'})

    def get_margin_position(self, pair):
        """get margin position for <pair> or for all pairs"""
        if pair:
            return self.private_api({'command': 'getMarginPosition', 'currencyPair': self.format_pair(pair)
            })
        return self.private_api({'command': 'getMarginPosition'})

    def get_complete_balances(self, account='all'):
        """Returns all of your balances, including available balance, balance on orders, 
        and the estimated BTC value of your balance."""
        return self.private_api({'command': 'returnCompleteBalances', 'account': account
            })

    def get_deposit_addresses(self):
        """get deposit addresses"""
        return self.private_api({'command:', 'returnDepositAddresses'})

    def get_open_orders(self, pair="all"):
        """get your open orders for [pair='all']"""
        return self.private_api({'command': 'returnOpenOrders', 'currencyPair': self.format_pair(pair)})

    def get_deposits_withdrawals(self):
        """get deposit/withdraw history"""
        return self.private_api({'command':'returnDepositsWithdrawals'})

    def get_tradable_balances(self):
        """Returns your current tradable balances for each currency in each market for which margin trading is enabled."""
        return self.private_api({'command': 'returnTradableBalances'})

    def get_active_loans(self):
        """Returns your active loans for each currency."""
        return self.private_api({'command': 'returnActiveLoans'})

    def get_open_loan_offers(self):
        """Returns your open loan offers for each currency"""
        return self.private_api('returnOpenLoanOffers')

    def get_fee_info(self):
        """If you are enrolled in the maker-taker fee schedule,
        returns your current trading fees and trailing 30-day volume in BTC.
        This information is updated once every 24 hours."""
        return self.private_api({'command': 'returnFeeInfo'})

    '''
    def returnLendingHistory(self, start=False, end=time(), limit=False):
        if not start:
            start = time()-self.MONTH
        args = {'start': str(start), 'end': str(end)}
        if limit:
            args['limit'] = str(limit)
        return self.private_api('returnLendingHistory', args)
    '''

    def get_order_trades(self, order_id):
        """Returns any trades made from <orderId>"""
        return self.private_api({'command': 'returnOrderTrades', 'orderNumber': order_id})

    def create_loan_offfer(self, coin, amount, rate, auto_renew=0):
        """Creates a loan offer for <coin> for <amount> at <rate>"""
        return self.private_api({'command': 'createLoanOffer',
                                'currency': coin.upper(),
                                'amount': amount,
                                'autoRenew': auto_renew,
                                'lendingRate': rate
                                })

    def cancel_loan_offer(self, order_id):
        """Cancels the loan offer with <orderId>"""
        return self.private_api({'command': 'cancelLoanOffer', 'orderNumber': order_id})

    def toggle_auto_renew(self, order_id):
        """Toggles the 'autorenew' feature on loan <orderId>"""
        return self.private_api({'command': 'toggleAutoRenew', 'orderNumber': order_id})

    def close_margin_position(self, pair):
        """Closes the margin position on <pair>"""
        return self.private_api({'command': 'closeMarginPosition', 'currencyPair': self.format_pair(pair)})

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
                                'lendingRate': lendingRate
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
        """Cancels an order and places a new one of the same type in a single atomic transaction,
         meaning either both operations will succeed or both will fail. """
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

