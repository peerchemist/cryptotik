# -*- coding: utf-8 -*-

''' Hitbct exchange '''

import time
import requests
from decimal import Decimal
from cryptotik.common import (headers, ExchangeWrapper,
                              NormalizedExchangeWrapper)
from cryptotik.exceptions import (InvalidBaseCurrencyError,
                                  InvalidDelimiterError, APIError)
import dateutil.parser


class Hitbtc(ExchangeWrapper):
    ''' Hitbct exchange '''

    url = 'https://api.hitbtc.com/api/2/'
    name = "hitbtc"
    delimiter = ""
    headers = headers
    base_currencies = ['btc', 'eth', 'usd']
    quote_order = 0

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        '''initialize object from Hitbtc class'''

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
    def format_pair(self, pair):
        '''Format the pair argument to format understood by remote API.'''

        pair = pair.replace("-", self.delimiter).upper()
        return pair

    def get_base_currencies(self):
        raise NotImplementedError

    def _verify_response(self, response):
        if type(response.json()) is dict and 'error' in response.json():
            raise APIError(response.json()['error'])

    def _generate_signature(self):
        pass  # not required for this exchange

    def api(self, url, params={}):
        '''call api'''

        try:
            result = requests.get(url, params=params, headers=self.headers,
                                  timeout=self.timeout, proxies=self.proxy)
            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        return result.json()

    def private_api(self, url, params={}, http_method='GET'):
        '''handles private api methods'''

        if http_method == 'GET':
            try:
                result = self.api_session.get(url, auth=(self.apikey, self.secret), proxies=self.proxy)
                result.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(e)

        elif http_method == 'POST':
            if not bool(params):
                raise AttributeError("Data parameters required for POST request")
            try:
                result = self.api_session.post(url, data=params, auth=(self.apikey, self.secret))
                result.raise_for_status()

            except requests.exceptions.HTTPError as e:
                print(e)

        elif http_method == 'PUT':
            try:
                result = self.api_session.put(url, auth=(self.apikey, self.secret), proxies=self.proxy)
                result.raise_for_status()

            except requests.exceptions.HTTPError as e:
                print(e)

        elif http_method == 'DELETE':
            try:
                result = self.api_session.delete(url, auth=(self.apikey, self.secret), proxies=self.proxy)
                result.raise_for_status()

            except requests.exceptions.HTTPError as e:
                print(e)

        self._verify_response(result)
        return result.json()

    def get_market_ticker(self, pair):
        '''returns simple current market status report'''

        return self.api(self.url + "public/"+ "ticker/" + self.format_pair(pair))

    def get_market_trade_history(self, pair, limit=1000):
        '''get market trade history'''

        return self.api(self.url + "public/trades/" + self.format_pair(pair), 
                        params={'limit': limit})

    def get_market_orders(self, pair, depth=100):
        '''return order book for the market'''

        return self.api(self.url + "public/orderbook/" + self.format_pair(pair),
                        params={'limit': depth})

    def get_market_sell_orders(self, pair):

        return self.get_market_orders(pair)['ask']

    def get_market_buy_orders(self, pair):

        return self.get_market_orders(pair)['bid']

    def get_market_spread(self, pair):
        '''return first buy order and first sell order'''

        order_book = self.get_market_orders(self.format_pair(pair))

        ask = order_book['ask'][0]['price']
        bid = order_book['bid'][0]['price']

        return Decimal(ask) - Decimal(bid)

    def get_markets(self):
        '''Find supported markets on this exchange'''

        r = self.api(self.url + "public/" + "symbol")

        pairs = [i["id"].lower() for i in r]
        return pairs

    def get_market_volume(self, pair):
        ''' return volume of last 24h'''

        return self.get_market_ticker(self.format_pair(pair))["volume"]

    def get_market_depth(self, pair):
        '''return sum of all bids and asks'''

        order_book = self.get_market_orders(self.format_pair(pair))
        asks = sum([Decimal(i['size']) for i in order_book['ask']])
        bid = sum([Decimal(i['size']) for i in order_book['bid']])

        return {"bids": bid, "asks": asks}

    def get_balances(self):
        """get all balances from your account"""

        balances = self.private_api(self.url + "trading/balance")

        return [i for i in balances if i["available"] != '0']

    def get_withdraw_history(self, currency):
        '''Retrieves withdrawal history.'''

        transactions = self.private_api(self.url + "account/transactions", 
                                        params={"currency": currency.upper()})
        return [i for i in transactions if i["type"] == 'payout']

    def withdraw(self, coin, amount, address):
        '''withdraw <coin> <amount> to <address>'''

        return self.private_api(self.url + "account/crypto/withdraw",
                                params={"currency": coin.upper(),
                                        "amount": amount,
                                        "address": address},
                                http_method='POST')

    def get_order(self, order_id):
        ''' Retreive a single order by it's ID '''

        return self.private_api(self.url + "history/order/" + order_id + "/trades")

    def sell_limit(self, pair, price, quantity):
        '''creates sell order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "order",
                                params={'symbol': self.format_pair(pair),
                                        'side': 'sell', 'quantity': quantity,
                                        'price': price},
                                http_method='POST')

    def cancel_all_orders(self):
        '''cancel all active orders'''

        return self.private_api(self.url + "order", http_method='DELETE')

    def cancel_order(self, clientOrderId):
        '''cancels order with id <clientOrderId>'''

        return self.private_api(self.url + "order/" + clientOrderId,
                                http_method='DELETE')

    def get_deposit_history(self, currency):
        '''Retreive deposit history.'''

        transactions = self.private_api(self.url + "account/transactions", 
                                            params={"currency": currency.upper()})
        return [i for i in transactions if i["type"] == 'payin']

    def get_open_orders(self, pair=None):
        '''get open orders for <pair>
           or all open orders if called without an argument.'''

        if pair:
            return self.private_api(self.url + "order", 
                                    params={'symbol': pair.upper()})
        return self.private_api(self.url + "order")

    def get_deposit_address(self, currency):
        ''' get deposit address for <currency> '''

        return self.private_api(self.url + "account/crypto/address/" + currency.upper())

    def buy_limit(self, pair, price, quantity):
        '''creates buy order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + "order",
                                params={'symbol': self.format_pair(pair),
                                    'side': 'buy', 'quantity': quantity,
                                    'price': price},
                                http_method='POST')


class HitbtcNormalized(Hitbtc):

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        super(HitbtcNormalized, self).__init__(apikey, secret, timeout, proxy)

    @classmethod
    def format_pair(self, market_pair):
        """
        Expected input is quote - base.
        Normalize the pair inputs and
        format the pair argument to a format understood by the remote API."""

        if "-" not in market_pair:
            raise InvalidDelimiterError('Agreed upon delimiter is "-".')

        quote, base = market_pair.split('-')

        if base.lower() not in self.base_currencies:
            raise InvalidBaseCurrencyError('''Expected input is quote-base, you have provided with {pair}'''.format(pair=market_pair))

        return quote + self.delimiter + base

    @staticmethod
    def _iso_string_to_datetime(ts):
        '''convert ISO timestamp to unix timestamp'''

        return dateutil.parser.parse(ts)

    @staticmethod
    def _is_sale(Type):

        if Type == 'sell':
            return True
        else:
            return False

    def get_markets(self):

        upstream = super(HitbtcNormalized, self).get_markets()

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

        ticker = super(HitbtcNormalized, self).get_market_ticker(market)

        return {
            'ask': float(ticker['ask']),
            'bid': float(ticker['bid']),
            'last': float(ticker['last'])
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

        upstream = super(HitbtcNormalized, self).get_market_trade_history(market, depth)
        downstream = []

        for data in upstream:

            downstream.append({
                'timestamp': self._iso_string_to_datetime(data['timestamp']),
                'is_sale': self._is_sale(data['side']),
                'rate': float(data['price']),
                'amount': float(data['quantity']),
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

        upstream = super(HitbtcNormalized, self).get_market_orders(market, depth)

        return {
            'bids': [[i['price'], i['size']] for i in upstream['bid']],
            'asks': [[i['price'], i['size']] for i in upstream['ask']]
        }

    def get_market_sell_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['asks']

    def get_market_buy_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['bids']

    def get_market_spread(self, market):
        '''return first buy order and first sell order'''

        order_book = self.get_market_orders(market)

        ask = order_book['asks'][0][0]
        bid = order_book['bids'][0][0]

        return Decimal(ask) - Decimal(bid)

    def get_market_depth(self, market):
        '''return sum of all bids and asks'''

        order_book = self.get_market_orders(market, 1000)

        return {"bids": sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]]),
                "asks": sum([Decimal(i[1]) for i in order_book["asks"]])
                }
