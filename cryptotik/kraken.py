# -*- coding: utf-8 -*-

import hmac
import hashlib
import time
import base64
import requests
from cryptotik.common import (headers, ExchangeWrapper,
                              NormalizedExchangeWrapper)
from cryptotik.exceptions import (InvalidBaseCurrencyError,
                                  InvalidDelimiterError,
                                  APIError)
from re import findall
from decimal import Decimal
from datetime import datetime


class Kraken(ExchangeWrapper):

    url = 'https://api.kraken.com/0/'
    name = 'kraken'
    delimiter = ""
    headers = headers
    taker_fee, maker_fee = 0.00, 0.00
    quote_order = 0
    base_currencies = ['xbt', 'eur', 'usd', 'eth', 'cad', 'gbp', 'jpy']

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        return "".join(findall(r"[^\W\d_]+|\d+", pair)).upper()

    def get_base_currencies(self):
        raise NotImplementedError

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        '''initialize class'''

        if apikey and secret:
            self.apikey = apikey.encode('utf-8')
            self.secret = secret.encode('utf-8')

        if proxy:
            assert proxy.startswith('https'), {'Error': 'Only https proxies supported.'}
        self.proxy = {'https': proxy}

        if not timeout:
            self.timeout = (8, 15)
        else:
            self.timeout = timeout

        self.api_session = requests.Session()

    def _verify_response(self, response):

        if response.json()['error']:
            raise APIError(response.json()['error'])

    def _generate_signature(self, message):

        sig = hmac.new(base64.b64decode(self.secret), message, hashlib.sha512)
        return base64.b64encode(sig.digest()).decode()

    def api(self, url, params=None):
        '''call api'''

        try:
            result = self.api_session.get(url, headers=self.headers, 
                                          params=params, timeout=self.timeout,
                                          proxies=self.proxy)

            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(result)
        return result.json()['result']

    def get_nonce(self):
        '''return nonce integer'''

        return int(1000 * time.time())

    def private_api(self, url, params={}):
        '''handles private api methods'''

        urlpath = url[22:]
        data = params
        data['nonce'] = self.get_nonce()
        postdata = requests.compat.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        signature = self._generate_signature(message)

        try:
            result = self.api_session.post(url, data=data, headers={
                                           'API-Key': self.apikey,
                                           'API-Sign': signature},
                                           timeout=self.timeout,
                                           proxies=self.proxy)

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(result)
        return result.json()['result']

    def get_markets(self):
        '''Find supported markets on this exchange'''

        markets = self.api(self.url + "public/AssetPairs")
        return [markets[i]['altname'].lower() for i in markets.keys()]

    def get_market_ohlcv_data(self, pair, interval, since=None):
        '''Get OHLC data
        :pair [str] - market pair
        :interval [int] - 1 (default), 5, 15, 30, 60, 240, 1440, 10080, 21600 minutes
        '''

        if str(interval) not in "1, 5, 15, 30, 60, 240, 1440, 10080, 21600".split(', '):
            raise APIError('Unsupported interval.')

        return self.api(self.url + 'public/OHLC', params={'pair': self.format_pair(pair),
                                                          'interval': interval,
                                                          'since': since})

    def get_market_ticker(self, pair):
        '''returns simple current market status report'''
        p = self.format_pair(pair)
        return self.api(self.url + "public/Ticker", 
                params={'pair': p})[p]

    def get_market_volume(self, pair):
        ''' return volume of last 24h'''

        return self.get_market_ticker(self.format_pair(pair))['v'][1]

    def get_market_trade_history(self, pair, limit=200):
        '''get market trade history'''

        p = self.format_pair(pair)
        return self.api(self.url + "public/Trades",
                        params={'pair': p})[p][:limit]

    def get_market_orders(self, pair, depth=100):
        '''return order book for the market'''

        p = self.format_pair(pair)
        r = self.api(self.url + "public/Depth",
                     params={'pair': p, 'count': depth})

        pair_full_name = list(r.keys())[0]  # hack around this crazy naming scheme

        return r[pair_full_name]

    def get_market_sell_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['asks']

    def get_market_buy_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['bids']

    def get_balances(self):

        return self.private_api(self.url + "private/Balance")

    def get_deposit_method(self, currency):

        return self.private_api(self.url + "private/DepositMethods",
                                params={'asset': currency.upper()}
                                )[0]['method']

    def get_deposit_address(self, currency):
        ''' get deposit address for <currency> '''

        result = self.private_api(self.url + "private/DepositAddresses",
                                params={'asset': currency.upper(),
                                'method': self.get_deposit_method(currency)}
                                )
        if result == []:
            result = self.private_api(self.url + "private/DepositAddresses",
                                params={'asset': currency.upper(),
                                'method': self.get_deposit_method(currency),
                                'new': 'true'}
                                )

        return result[0]['address']

    def buy_limit(self, pair, price, quantity, leverage=None):
        '''creates buy limit order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + 'private/AddOrder',
                                params={'pair': self.format_pair(pair),
                                        'type': 'buy', 'ordertype': 'limit',
                                        'price': price, 'volume': quantity,
                                        'leverage': leverage
                                        })

    def buy_market(self, pair, price, quantity, leverage=None):
        '''creates buy market order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + 'private/AddOrder',
                                params={'pair': self.format_pair(pair),
                                        'type': 'buy', 'ordertype': 'market',
                                        'volume': quantity,
                                        'leverage': leverage
                                        })

    def sell_limit(self, pair, price, quantity, leverage=None):
        '''creates sell order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + 'private/AddOrder',
                                params={'pair': self.format_pair(pair),
                                        'type': 'sell', 'ordertype': 'limit',
                                        'price': price, 'volume': quantity,
                                        'leverage': leverage
                                        })

    def sell_market(self, pair, price, quantity, leverage=None):
        '''creates sell market order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + 'private/AddOrder',
                                params={'pair': self.format_pair(pair),
                                        'type': 'sell', 'ordertype': 'market',
                                        'volume': quantity,
                                        'leverage': leverage
                                        })

    def sell_stop_loss(self, pair, price, quantity, leverage=None):
        '''creates sell stop_loss order for <pair> triggered at <price>,
        stop is executed at market.'''

        return self.private_api(self.url + 'private/AddOrder',
                                params={'pair': self.format_pair(pair),
                                        'type': 'sell',
                                        'ordertype': 'stop-loss',
                                        'price': price,
                                        'volume': quantity,
                                        'leverage': leverage
                                        })

    def buy_stop_loss(self, pair, price, quantity, leverage=None):
        '''creates buy stop_loss order for <pair> triggered at <price>,
        stop is executed at market.'''

        return self.private_api(self.url + 'private/AddOrder',
                                params={'pair': self.format_pair(pair),
                                        'type': 'buy',
                                        'ordertype': 'stop-loss',
                                        'price': price,
                                        'volume': quantity,
                                        'leverage': leverage
                                        })

    def withdraw(self, currency, amount, withdrawal_key_name):
        '''withdraw <currency> <amount> to <withdrawal_key_name>, 
                which has to be set up on your account'''

        return self.private_api(self.url + 'private/Withdraw', 
                            params={'asset': currency.upper(),
                                'key': withdrawal_key_name, 'amount': amount
                            })

    def get_withdraw_history(self, currency):
        '''Retrieves withdrawal history for <currency>'''

        return self.private_api(self.url + "private/WithdrawStatus", 
                            params={'asset': currency.upper()})

    def get_deposit_history(self, currency):
        '''Retreive deposit history for <currency>.'''

        return self.private_api(self.url + "private/DepositStatus", 
                            params={'asset': currency.upper(),
                            'method': self.get_deposit_method(currency)
                            })

    def get_open_positions(self, docalcs=False):
        '''get open margin positions.
        : docalcs = whether or not to include profit/loss calculations (optional.  default = false)
        '''

        return self.private_api(self.url + "private/OpenPositions",
                                params={'docalcs': docalcs}
                                )

    def get_open_orders(self):
        '''get open orders.'''

        return self.private_api(self.url + "private/OpenOrders",
                            params={'trades': 'true'}
                            )['open']

    def get_order(self, orderId):
        """retrieve a single order by orderId."""

        return self.private_api(self.url + "private/QueryOrders",
                            params={'trades': 'true',
                            'txid': orderId})

    def cancel_order(self, orderId):
        """cancel order with <orderId>"""

        return self.private_api(self.url + "private/CancelOrder",
                            params={'txid': orderId})

    def cancel_all_orders(self):
        """cancel all orders"""

        for txid in self.get_open_orders():
            self.cancel_order(txid)


class KrakenNormalized(Kraken, NormalizedExchangeWrapper):

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        super(KrakenNormalized, self).__init__(apikey, secret, timeout, proxy)

    @classmethod
    def format_pair(self, market_pair):
        """
        Expected input is quote - base.
        Normalize the pair inputs and
        format the pair argument to a format understood by the remote API."""

        market_pair = market_pair.upper()  # kraken takes uppercase

        if "-" not in market_pair:
            raise InvalidDelimiterError('Agreed upon delimiter is "-".')

        quote, base = market_pair.split('-')

        if base == "BTC":
            base = "XBT"

        if base.lower() not in self.base_currencies:
            raise InvalidBaseCurrencyError('''Expected input is quote-base, you have provided with {pair}'''.format(pair=market_pair))

        return quote + self.delimiter + base  # for kraken quote comes first

    @staticmethod
    def _tstamp_to_datetime(timestamp):
        '''convert unix timestamp to datetime'''

        return datetime.fromtimestamp(timestamp)

    @staticmethod
    def _is_sale(s):

        if s == "s":
            return True
        else:
            return False

    def get_markets(self):

        upstream = super(KrakenNormalized, self).get_markets()

        quotes = []

        for i in upstream:
            for base in self.base_currencies:
                if base in i:
                    quotes.append("".join(i.rsplit(base, 1)) + '-' + base)

        return quotes

    def get_market_ticker(self, market):
        '''
        :return :
            dict['ask': float, 'bid': float, 'last': float]
            example: {'ask': float, 'bid': float, 'last': float}
        '''

        ticker = super(KrakenNormalized, self).get_market_ticker(market)

        return {
            'ask': ticker['a'][0],
            'bid': ticker['b'][0],
            'last': ticker['c'][0]
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

        upstream = super(KrakenNormalized, self).get_market_trade_history(market, depth)
        downstream = []

        for data in upstream:

            downstream.append({
                'timestamp': self._tstamp_to_datetime(data[2]),
                'is_sale': self._is_sale(data[3]),
                'rate': data[0],
                'amount': data[1],
                'trade_id': data[2]
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

        upstream = super(KrakenNormalized, self).get_market_orders(market, depth)

        return {
            'bids': [[i[0], i[1]] for i in upstream['bids']],
            'asks': [[i[0], i[1]] for i in upstream['asks']]
        }

    def get_market_sell_orders(self, market, depth=100):

        return self.get_market_orders(market, depth)['asks']

    def get_market_buy_orders(self, market, depth=100):

        return self.get_market_orders(market, depth)['bids']

    def get_market_spread(self, market):
        '''return first buy order and first sell order'''

        order_book = super(KrakenNormalized, self).get_market_orders(market, 1)

        ask = order_book['asks'][0][0]
        bid = order_book['bids'][0][0]

        return Decimal(ask) - Decimal(bid)

    def get_market_depth(self, market):
        '''return sum of all bids and asks'''

        order_book = self.get_market_orders(market, 1000)

        return {"bids": sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]]),
                "asks": sum([Decimal(i[1]) for i in order_book["asks"]])
                }
