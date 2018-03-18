# -*- coding: utf-8 -*-

''' Binance exchange '''

import hmac
import hashlib
import time
import requests
from decimal import Decimal
from cryptotik.common import (headers, ExchangeWrapper,
                              NormalizedExchangeWrapper)
from cryptotik.exceptions import (InvalidBaseCurrencyError,
                                  InvalidDelimiterError, APIError)
from datetime import datetime


class Binance(ExchangeWrapper):
    ''' Binance exchange class'''

    name = "binance"
    url = 'https://api.binance.com/'
    delimiter = ""
    headers = headers
    taker_fee, maker_fee = 0.001, 0.001
    base_currencies = ['btc', 'eth', 'bnb', 'usdt']
    quote_order = 0

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):

        if apikey and secret:
            self.apikey = apikey
            self.secret = bytes(secret.encode("utf-8"))

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

    def _verify_response(self, response):
        '''verify if API responded properly and raise apropriate error.'''

        if "msg" in response.json() and "code" in response.json():
            raise APIError(response.json()['msg'])

    def _generate_signature(self, query):

        return hmac.new(self.secret, query,
                        hashlib.sha256).hexdigest()

    def api(self, url, params):
        '''call api'''

        try:
            response = self.api_session.get(url, params=params, headers=self.headers,
                                            timeout=self.timeout, proxies=self.proxy)
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(response)
        return response.json()

    def private_api(self, url, params={}, http_method='GET'):
        '''handles private api methods'''

        query = requests.compat.urlencode(sorted(params.items()))
        query += "&timestamp={}".format(int(time.time() * 1000))
        query += "&signature={}".format(self._generate_signature(query.encode('utf-8')))

        try:
            response = self.api_session.request(http_method,
                                            url + "?" + query,
                                            headers={"X-MBX-APIKEY": self.apikey},
                                            proxies=self.proxy)
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(response)
        return response.json()

    @classmethod
    def format_pair(self, pair):
        '''Format the pair argument to format understood by remote API.'''

        pair = pair.replace("-", self.delimiter).upper()
        return pair

    def ping(self):
        '''Test connectivity to the Rest API.'''

        ping = self.api(self.url + 'api/v1/ping', params={})

        if ping == {}:
            return True

    def get_exchange_information(self):
        '''Current exchange trading rules and symbol information'''

        return self.api(self.url + 'api/v1/exchangeInfo', params={})

    def get_market_ticker(self, pair):
        '''returns simple current market status report'''

        params = (('symbol', self.format_pair(pair)),)

        return self.api(self.url + "api/v1/ticker/24hr", params)

    def get_market_trade_history(self, pair, depth=500):
        '''get market trade history
        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#recent-trades-list
        '''

        return self.api(self.url + "api/v1/trades",
                        params=(('symbol', self.format_pair(pair)), ('limit', depth),))

    def get_market_ohlcv_data(self, pair, interval, since=None,
                              until=None, limit=500):
        '''
        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#klinecandlestick-data

        Kline/candlestick bars for a symbol. Klines are uniquely identified by their open time.
        If since and until are not sent, the most recent klines are returned.

        : market [str]: market pair
        : interval [str]: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        : limit [int]: Default 500; max 500.
        : since [int]: timestamp
        : util [int]: timestamp
        '''

        if interval not in "1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M".split(', '):
            raise APIError('Unsupported interval.')

        return self.api(self.url + "api/v1/klines", params={'symbol': self.format_pair(pair),
                                                            'interval': interval,
                                                            'limit': 500,
                                                            'startTime': since,
                                                            'endTime': until
                                                            })

    def get_summaries(self):
        '''get summary of all active markets'''

        return self.api(self.url + 'api/v1/ticker/24hr',
                        params=())

    def get_market_orders(self, pair, depth=100):
        '''return sum of all bids and asks'''

        return self.api(self.url + 'api/v1/depth',
                        params={'symbol': self.format_pair(pair),
                                'limit': depth})

    def get_market_sell_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['asks']

    def get_market_buy_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['bids']

    def get_markets(self):
        '''Find supported markets on this exchange,
            use <filter> if needed'''

        r = self.api(self.url + "api/v1/ticker/allPrices", params=())
        return [i["symbol"].lower() for i in r]

    def get_market_volume(self, pair):
        ''' return volume of last 24h'''

        return self.get_market_ticker(self.format_pair(pair))["volume"]

    def get_balances(self):
        """get all balances from your account"""

        balances = self.private_api(self.url + "api/v3/account")["balances"]

        return [i for i in balances if i["free"] != '0.00000000']

    def buy_limit(self, pair, price, quantity, test=False):
        '''creates buy order for <pair> at <price> for <quantity>'''

        api_endpoint = "api/v3/order"
        if test:
            api_endpoint += '/test'

        return self.private_api(self.url + api_endpoint,
                                params={'symbol': self.format_pair(pair),
                                        'side': 'BUY', 'type': 'limit',
                                        'timeInForce': 'GTC',
                                        'quantity': quantity,
                                        'price': price},
                                http_method='POST')

    def buy_market(self, pair, quantity, test=False):
        '''execute market buy order'''

        api_endpoint = "api/v3/order"
        if test:
            api_endpoint += '/test'

        return self.private_api(self.url + api_endpoint,
                                params={'symbol': self.format_pair(pair),
                                        'side': 'BUY', 'type': 'market',
                                        'quantity': quantity
                                        },
                                http_method='POST')

    def get_deposit_address(self, currency):
        ''' get deposit address for <currency> '''

        return self.private_api(self.url + "/wapi/v3/depositAddress.html",
                                params={'asset': currency.upper()},
                                http_method='GET') 

    def get_open_orders(self, pair=None):
        '''get open orders for <pair>
           or all open orders if called without an argument.'''

        if pair:
            return self.private_api(self.url + "/api/v3/openOrders", 
                                    params={'symbol': pair.upper()})
        return self.private_api(self.url + "/api/v3/openOrders")

    def sell_limit(self, pair, price, quantity, test=False):
        '''creates sell order for <pair> at <price> for <quantity>'''

        api_endpoint = "api/v3/order"
        if test:
            api_endpoint += '/test'

        return self.private_api(self.url + api_endpoint,
                                params={'symbol': self.format_pair(pair),
                                        'side': 'SELL', 'type': 'limit',
                                        'timeInForce': 'GTC',
                                        'quantity': quantity,
                                        'price': price},
                                http_method='POST')

    def sell_market(self, pair, quantity, test=False):
        '''execute market sell order'''

        api_endpoint = "api/v3/order"
        if test:
            api_endpoint += '/test'

        return self.private_api(self.url + api_endpoint,
                                params={'symbol': self.format_pair(pair),
                                        'side': 'SELL', 'type': 'market',
                                        'quantity': quantity
                                        },
                                http_method='POST')

    def withdraw(self, coin, amount, address, name=None, address_tag=None):
        '''withdraw <coin> <amount> to <address> with <address_tag> if needed
        : name is description of the address.'''

        if address_tag:
            query = {'asset': coin.upper(),
                     'address': address,
                     'addressTag': address_tag,
                     'amount': amount}

        else:
            query = {'asset': coin.upper(),
                     'address': address,
                     'amount': amount}

        if not name:
            query['name'] = coin.upper()
        else:
            query['name'] = name

        return self.private_api(self.url + "/wapi/v3/withdraw.html",
                                params=query,
                                http_method='POST')

    def get_withdraw_history(self, currency=None):
        '''Retrieves withdrawal history.'''

        if currency:
            transactions = self.private_api(self.url + "/wapi/v3/withdrawHistory.html", 
                                            params={"asset": currency.upper()})
        else:
            transactions = self.private_api(self.url +
                                "/wapi/v3/withdrawHistory.html")

        return [i for i in transactions["withdrawList"]]

    def get_deposit_history(self, currency=None):
        '''Retreive deposit history.'''

        if currency:
            transactions = self.private_api(self.url + "/wapi/v3/depositHistory.html", 
                                            params={"asset": currency.upper()})
        else:
            transactions = self.private_api(self.url + "/wapi/v3/depositHistory.html")

        return [i for i in transactions["depositList"]]

    def get_order(self, symbol, order_id):
        """retrieve a single order by orderId."""

        return self.private_api(self.url + "/api/v3/order",
                                params={"symbol": symbol,
                                "orderId": order_id},
                                http_method='GET')

    def cancel_order(self, order_id, symbol):
        """cancel order with <order_id> for <symbol>"""

        return self.private_api(self.url + "/api/v3/order",
                                params={"symbol": symbol,
                                "orderId": order_id},
                                http_method='DELETE')

    def cancel_all_orders(self):

        for order in self.get_open_orders():
            self.cancel_order(order['orderId'], order['symbol'])

    def get_nonce(self):
        pass


class BinanceNormalized(Binance, NormalizedExchangeWrapper):

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        super(BinanceNormalized, self).__init__(apikey, secret, timeout, proxy)

    @classmethod
    def format_pair(self, market_pair):
        """
        Expected input is quote - base.
        Normalize the pair inputs and
        format the pair argument to a format understood by the remote API."""

        market_pair = market_pair.upper()  # binance takes uppercase

        if "-" not in market_pair:
            raise InvalidDelimiterError('Agreed upon delimiter is "-".')

        quote, base = market_pair.split('-')

        if base.lower() not in self.base_currencies:
            raise InvalidBaseCurrencyError('''Expected input is quote-base, you have provided with {pair}'''.format(pair=market_pair))

        return quote + self.delimiter + base  # for binance quote comes first

    @staticmethod
    def _is_sale(isBuyerMaker):

        if isBuyerMaker:
            return True
        else:
            return False

    @staticmethod
    def _tstamp_to_datetime(timestamp):
        '''convert unix timestamp to datetime'''

        return datetime.fromtimestamp(timestamp / 1000)

    def get_markets(self):

        upstream = super(BinanceNormalized, self).get_markets()

        quotes = []

        for i in upstream:
            for base in self.base_currencies:
                if i.endswith(base):
                    quotes.append(i.replace(base, '') + '-' + base)

        return quotes

    def get_market_ticker(self, market):
        '''
        :return :
            dict['ask': float, 'bid': float, 'last': float]
            example: {'ask': float, 'bid': float, 'last': float}
        '''

        ticker = super(BinanceNormalized, self).get_market_ticker(market)

        return {
            'ask': float(ticker['askPrice']),
            'bid': float(ticker['bidPrice']),
            'last': float(ticker['lastPrice'])
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

        upstream = super(BinanceNormalized, self).get_market_trade_history(market, depth)
        downstream = []

        for data in upstream:

            downstream.append({
                'timestamp': self._tstamp_to_datetime(data['time']),
                'is_sale': self._is_sale(data['isBuyerMaker']),
                'rate': float(data['price']),
                'amount': float(data['qty']),
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

        upstream = super(BinanceNormalized, self).get_market_orders(market, depth)

        return {
            'bids': [[i[0], i[1]] for i in upstream['bids']],
            'asks': [[i[0], i[1]] for i in upstream['asks']]
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

    def get_market_ohlcv_data(self, market, interval, since=None,
                              until=datetime.now().timestamp()):
        '''
        : since - UNIX timestamp
        : until - UNIX timestamp
        '''

        if interval not in "1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M".split(', '):
            raise APIError('Unsupported OHLCV interval.')

        upstream = super(BinanceNormalized, self).get_market_ohlcv_data(market,
                                                 interval,
                                                 int(since*1000),
                                                 int(until*1000)
                                                 )
        r = []

        for ohlcv in upstream:
            r.append({
                'open': float(ohlcv[1]),
                'high': float(ohlcv[2]),
                'low': float(ohlcv[3]),
                'close': float(ohlcv[4]),
                'volume': float(ohlcv[5]),
                'time': self._tstamp_to_datetime(int(ohlcv[6]))
            })

        return r
