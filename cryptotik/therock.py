# -*- coding: utf-8 -*-

import hmac
import hashlib
import time
import requests
from cryptotik.common import (headers, ExchangeWrapper,
                              NormalizedExchangeWrapper)
from cryptotik.exceptions import (InvalidBaseCurrencyError,
                                  InvalidDelimiterError,
                                  APIError,
                                  OutdatedBaseCurrenciesError)
from cryptotik.common import is_sale
import dateutil.parser
from re import findall
from decimal import Decimal


class TheRock(ExchangeWrapper):

    url = 'https://api.therocktrading.com/v1/'
    name = 'therock'
    delimiter = ""
    headers = headers
    quote_order = 0
    base_currencies = ['eur', 'btc']

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        '''initialize bittrex class'''

        if apikey and secret:
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

    def get_base_currencies(self):
        raise NotImplementedError

    @classmethod
    def format_pair(self, pair):
        """format the pair argument to format understood by remote API."""

        return "".join(findall(r"[^\W\d_]+|\d+", pair)).upper()

    def _verify_response(self, response):
        '''verify if API responded properly and raise apropriate error.'''

        try:
            if 'errors' in response.json().keys():
                raise APIError(response.json()['errors'][0]['message'])
        except KeyError:
            pass

    def _generate_signature(self, data):

        return hmac.new(self.secret,
                        data.encode("utf-8"),
                        hashlib.sha512).hexdigest()

    def api(self, url):
        '''call api'''

        try:
            result = self.api_session.get(url, headers=self.headers,
                                          timeout=self.timeout, proxies=self.proxy)

            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(result)
        return result.json()

    def private_api(self, url, http_method='GET', params={}):
        '''handles private api methods'''

        if not self.apikey or not self.secret:
            raise ValueError("A Key and Secret needed!")

        nonce = str(self.get_nonce())
        if params:
            url += "?" + requests.compat.urlencode(sorted(params.items()))
        nonce_plus_url = str(nonce) + url

        head = {"Content-Type": "application/json",
                "X-TRT-KEY": self.apikey,
                "X-TRT-SIGN": self._generate_signature(nonce_plus_url),
                "X-TRT-NONCE": nonce}

        try:
            result = self.api_session.request(http_method, url, headers=head,
                                              proxies=self.proxy)
            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(result)
        return result.json()

    def get_market_ticker(self, pair):
        '''returns simple current market status report'''

        return self.api(self.url + "funds/" + self.format_pair(pair) + "/ticker")

    def get_market_trade_history(self, pair, depth=10):
        '''get market trade history'''

        return self.api(self.url + "funds/" + self.format_pair(pair) + "/trades" +
                                "?per_page={}".format(depth))['trades']

    def get_market_orders(self, pair, depth=100):
        '''return order book for the market'''

        orders = self.api(self.url + "funds/" + self.format_pair(pair) + "/orderbook")
        return {'bids': orders['bids'][:depth],
                'asks': orders['asks'][:depth]}

    def get_market_sell_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['asks']

    def get_market_buy_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['bids']

    def get_markets(self):
        '''Find supported markets on this exchange'''

        r = self.api(self.url + "funds")['funds']
        pairs = [i["id"].lower() for i in r]

        return [i for i in pairs if not i.startswith('noku') and not i.endswith('eurn')]

    def get_market_volume(self, pair):
        ''' return volume of last 24h'''

        return self.get_market_ticker(self.format_pair(pair))["volume"]

    def get_nonce(self):
        '''return nonce integer'''

        nonce = getattr(self, '_nonce', 0)
        if nonce:
            nonce += 1
        # If the unix time is greater though, use that instead (helps low
        # concurrency multi-threaded apps always call with the largest nonce).
        self._nonce = max(int(time.time()), nonce)
        return self._nonce

    def get_balances(self):
        """get all balances from your account"""

        balances = self.private_api(self.url + "balances")
        return [i for i in balances['balances'] if i["trading_balance"] != 0.0]

    def get_deposit_address(self, currency):
        ''' get deposit address for <currency> '''

        return self.private_api(self.url + "currencies/" + currency.upper() +
                                "/addresses",
                                http_method='GET',
                                params={'unused': 'true'})

    def buy_limit(self, pair, price, quantity):
        '''creates buy order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "funds/"
                                + self.format_pair(pair) + "/orders",
                                params={'fund_id': self.format_pair(pair),
                                    'side': 'buy', 'amount': quantity,
                                    'price': price},
                                http_method='POST')

    def sell_limit(self, pair, price, quantity):
        '''creates sell order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "funds/" 
                                + self.format_pair(pair) + "/orders",
                                params={'fund_id': self.format_pair(pair),
                                    'side': 'sell', 'amount': quantity,
                                    'price': price},
                                http_method='POST')

    def withdraw(self, coin, amount, address):
        '''withdraw <coin> <amount> to <address> with <address_tag> if needed'''

        return self.private_api(self.url + "atms/withdraw",
                                params={'currency': coin.upper(),
                                        'destination_address': address, 
                                        'amount': amount},
                                http_method='POST')

    def get_withdraw_history(self, currency=None):
        '''Retrieves withdrawal history.'''

        if currency:
            transactions = self.private_api(self.url + "transactions",
                                        params={'currency': currency.upper()})["transactions"] 
        else:
            transactions = self.private_api(self.url + "transactions")["transactions"]

        return [i for i in transactions if i["type"] == "withdraw"]

    def get_deposit_history(self, currency=None):
        '''Retreive deposit history.'''

        if currency:
            transactions = self.private_api(self.url + "transactions",
                                        params={'currency': currency})["transactions"] 
        else:
            transactions = self.private_api(self.url + "transactions")["transactions"]

        return [i for i in transactions if i["type"] == "atm_payment"]

    def get_open_orders(self, pair=None):
        '''get open orders for <pair>
           or all open orders if called without an argument.'''

        if not pair:
            all_pairs = []
            for market in self.get_markets():
                all_pairs += self.private_api(self.url + "funds/" + 
                                              self.format_pair(market) + "/orders")
                return all_pairs
        else:
            return self.private_api(self.url + "funds/" + self.format_pair(pair) 
                                    + "/orders")["orders"]

    def get_order(self, symbol, order_id):
        """retrieve a single order by orderId."""

        return self.private_api(self.url + "funds/" + symbol + "/orders/" + order_id,
                                http_method='GET')

    def cancel_order(self, order_id, symbol):
        """cancel order with <order_id> for <symbol>"""

        return self.private_api(self.url + "funds/" + symbol +
                                "/orders/" + order_id,
                                http_method='DELETE')

    def cancel_all_orders(self, symbol):
        """cancel all orders for <symbol> """

        return self.private_api(self.url + "funds/" + symbol +
                                "/orders/remove_all",
                                http_method='DELETE')


class TheRockNormalized(TheRock, NormalizedExchangeWrapper):

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        super(TheRockNormalized, self).__init__(apikey, secret, timeout, proxy)

    @staticmethod
    def _iso_to_datetime(iso):
        '''convert ISO style date expression to datetime object'''

        return dateutil.parser.parse(iso)

    @classmethod
    def format_pair(self, market_pair):
        """
        Expected input is quote - base.
        Normalize the pair inputs and
        format the pair argument to a format understood by the remote API."""

        if "-" not in market_pair:
            raise InvalidDelimiterError('Agreed upon delimiter is "-".')

        quote, base = market_pair.upper().split('-')

        if base.lower() not in self.base_currencies:
            raise InvalidBaseCurrencyError("""Expected input is quote-base, you have provided with {pair}""".format(pair=market_pair))

        if quote == "xrp":
            return base + self.delimiter + quote  # unless it's xrp, which comes second
        else:
            return quote + self.delimiter + base  # for therock quote comes first

    def get_markets(self):

        upstream = super(TheRockNormalized, self).get_markets()

        quotes = []

        for i in upstream:
            for base in self.base_currencies:
                if base in i:
                    quotes.append(i.replace(base, '') + '-' + base)

        return quotes

    def get_market_ticker(self, market):
        '''
        :return :
            dict['ask': float, 'bid': float, 'last': float]
            example: {'ask': float, 'bid': float, 'last': float}
        '''

        ticker = super(TheRockNormalized, self).get_market_ticker(market)

        return {
            'ask': ticker['ask'],
            'bid': ticker['bid'],
            'last': ticker['last']
        }

    def get_market_trade_history(self, market, depth=100):
        '''
        :return:
            list -> dict['timestamp': datetime.datetime,
                        'is_sale': bool,
                        'rate': float,
                        'amount': float,
                        'trade_id': any]
        '''

        upstream = super(TheRockNormalized, self).get_market_trade_history(market, depth)
        downstream = []

        for data in upstream:

            downstream.append({
                'timestamp': self._iso_to_datetime(data['date']),
                'is_sale': is_sale(data['side']),
                'rate': data['price'],
                'amount': data['amount'],
                'trade_id': data['id']
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

        upstream = super(TheRockNormalized, self).get_market_orders(market, depth)

        return {
            'bids': [[i['price'], i['amount']] for i in upstream['bids']],
            'asks': [[i['price'], i['amount']] for i in upstream['asks']]
        }

    def get_market_sell_orders(self, market):

        return self.get_market_orders(market)['asks']

    def get_market_buy_orders(self, market):

        return self.get_market_orders(market)['bids']

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
