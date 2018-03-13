# -*- coding: utf-8 -*-

import hmac
import json
import hashlib
import time
import base64
import requests
from datetime import datetime
from decimal import Decimal
from cryptotik.common import (headers, ExchangeWrapper,
                              NormalizedExchangeWrapper)
from cryptotik.exceptions import (InvalidBaseCurrencyError,
                                  InvalidDelimiterError, APIError)


class Cryptopia(ExchangeWrapper):

    url = 'https://www.cryptopia.co.nz/'
    name = 'cryptopia'
    delimiter = "_"
    headers = headers
    taker_fee, maker_fee = 0.00, 0.00
    quote_order = 0
    base_currencies = ['btc']

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        if "-" not in pair:
            raise InvalidDelimiterError('Agreed upon delimiter is "-".')

        pair = pair.replace("-", cls.delimiter)

        if not pair.isupper():
            return pair.upper()
        else:
            return pair

    def get_base_currencies(self):
        '''return base markets supported by this exchange.'''
        raise NotImplementedError

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        '''initialize class'''

        if apikey and secret:
            self.apikey = apikey
            self.secret = secret

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

        return int(1000*time.time())

    def _verify_response(self, response):
        '''verify if API responded properly and raise apropriate error.'''

        if not response.json()['Success'] or response.json()['Error']:
            raise APIError(response.json()['Error'])

    def _generate_signature(self, url, params):

        nonce = str(self.get_nonce())
        md5 = hashlib.md5()
        md5.update(json.dumps(params).encode('utf-8'))
        rcb64 = base64.b64encode(md5.digest()).decode('utf-8')
        signature = self.apikey + "POST" + requests.compat.quote_plus(url).lower() + nonce + rcb64 
        hmacsignature = base64.b64encode(hmac.new(base64.b64decode(self.secret),
                        signature.encode('utf-8'),
                        hashlib.sha256).digest())
        return "amx " + self.apikey + ":" + hmacsignature.decode('utf-8') + ":" + nonce

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
        return result.json()['Data']   

    def private_api(self, url, params={}):
        '''handles private api methods'''

        try:
            result = self.api_session.post(url, json=params,
                                           headers={'Authorization': self._generate_signature(url, params)},
                                           timeout=self.timeout, proxies=self.proxy)
            result.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(result)
        return result.json()['Data']

    def get_markets(self):
        '''Find supported markets on this exchange'''

        r = self.api(self.url + "api/GetMarkets/BTC")
        return [i['Label'] for i in r]

    def get_market_ticker(self, pair):
        '''returns simple current market status report'''

        return self.api(self.url + "api/getMarket/" + self.format_pair(pair))
        
    def get_market_volume(self, pair):
        ''' return volume of last 24h'''

        return self.api(self.url + "api/getMarket/" + 
                        self.format_pair(pair))['Volume']

    def get_market_trade_history(self, pair, limit=100):
        '''get market trade history'''

        return self.api(self.url + "api/getMarketHistory/" + 
                        self.format_pair(pair))[:limit]

    def get_market_orders(self, pair, depth=100):
        '''return order book for the market'''

        return self.api(self.url + "api/GetMarketOrders/" +
                          self.format_pair(pair) + "/" + str(depth))

    def get_market_sell_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['asks']

    def get_market_buy_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['bids']

    def get_balances(self):
        
        result = self.private_api(self.url + "Api/getBalance")
        return [i for i in result if i['Total'] != 0.0]

    def get_deposit_address(self, currency):
        ''' get deposit address for <currency> '''
        
        return self.private_api(self.url + "Api/GetDepositAddress", 
                            params={'Currency': currency.upper()})['Address']

    def buy_limit(self, pair, price, quantity):
        '''creates buy order for <pair> at <price> for <quantity>'''

        return self.private_api(self.url + 'Api/SubmitTrade',
                            params={'Market': self.format_pair(pair), 'Type': 'Buy',
                                'Rate': price, 'Amount': quantity})

    def sell_limit(self, pair, price, quantity):
        '''creates sell order for <pair> at <price> for <quantity>'''
        
        return self.private_api(self.url + 'Api/SubmitTrade',
                            params={'Market': self.format_pair(pair), 'Type': 'Sell',
                                'Rate': price, 'Amount': quantity})

    def withdraw(self, currency, amount, address):
        '''withdraw <currency> <amount> to <address>, 
                which has to be set up on your account'''
        
        return self.private_api(self.url + 'Api/SubmitWithdraw', 
                            params={'Currency': currency.upper(),
                                'Address': address, 'Amount': amount
                            })

    def get_withdraw_history(self):
        '''Retrieves withdrawal history'''

        return self.private_api(self.url + "Api/GetTransactions",
                            params={'Type': 'Withdraw'})

    def get_deposit_history(self):
        '''Retreive deposit history'''

        return self.private_api(self.url + "Api/GetTransactions",
                            params={'Type': 'Deposit'})

    def get_open_orders(self):
        '''get open orders'''

        return self.private_api(self.url + "Api/GetOpenOrders",
                            params={})

    def get_order(self, orderId):
        """retrieve a single active order by orderId."""

        for o in self.get_open_orders():
            if o['OrderId'] == orderId:
                return o

    def cancel_order(self, orderId):
        """cancel order with <orderId>"""

        return self.private_api(self.url + "Api/CancelTrade", params={
                            'Type': 'Trade', 'OrderId': orderId})

    def cancel_all_orders(self):
        """cancel all orders"""
        return self.private_api(self.url + "Api/CancelTrade", params={
                            'Type': 'All'})


class CryptopiaNormalized(Cryptopia):

    def __init__(self, apikey=None, secret=None, timeout=None, proxy=None):
        super(CryptopiaNormalized, self).__init__(apikey, secret, timeout, proxy)

    @classmethod
    def format_pair(self, market_pair):

        if "-" not in market_pair:
            raise InvalidDelimiterError('Agreed upon delimiter is "-".')
        market_pair = market_pair.upper()
        quote, base = market_pair.split('-')

        if base.lower() not in self.base_currencies:
            raise InvalidBaseCurrencyError('''Expected input is quote-base, you have provided with {pair}'''.format(pair=market_pair))

        return quote + self.delimiter + base

    @staticmethod
    def _tstamp_to_datetime(timestamp):
        '''convert unix timestamp to datetime'''

        return datetime.utcfromtimestamp(timestamp)
    
    @staticmethod
    def _is_sale(Type):

        if Type == 'Sell':
            return True
        else:
            return False

    def get_markets(self):
    
        upstream = super(CryptopiaNormalized, self).get_markets()
        quotes = []
        for i in upstream:
            quotes.append(i.lower().replace('/', '-'))

        return quotes

    def get_market_ticker(self, market):

        ticker = super(CryptopiaNormalized, self).get_market_ticker(market)

        return {
            'ask': ticker['AskPrice'],
            'bid': ticker['BidPrice'],
            'last': ticker['LastPrice']
        }

    def get_market_trade_history(self, market, limit=100):
        '''
        :return:
            list -> dict['timestamp': datetime.datetime,
                        'is_sale': bool,
                        'rate': float,
                        'amount': float,
                        'trade_id': any]
        '''

        upstream = super(CryptopiaNormalized, self).get_market_trade_history(market, limit)
        
        downstream = []
        for data in upstream:
            downstream.append({
                'timestamp': self._tstamp_to_datetime(data['Timestamp']),
                'is_sale': self._is_sale(data['Type']),
                'rate': data['Price'],
                'amount': data['Amount'],
                'trade_id': 'not available'
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

        upstream = super(CryptopiaNormalized, self).get_market_orders(market, depth)

        return {
            'bids': [[i['Price'], i['Volume']] for i in upstream['Buy']],
            'asks': [[i['Price'], i['Volume']] for i in upstream['Sell']]
        }

    def get_market_sell_orders(self, pair, depth=100):
    
        return self.get_market_orders(pair, depth)['asks']

    def get_market_buy_orders(self, pair, depth=100):

        return self.get_market_orders(pair, depth)['bids']
    
    def get_market_spread(self, pair):
        '''return first buy order and first sell order'''

        order_book = self.get_market_orders(pair)

        ask = order_book["asks"][0][0]
        bid = order_book["bids"][0][0]

        return Decimal(ask) - Decimal(bid)

    def get_market_depth(self, pair):
        '''return sum of all bids and asks'''

        order_book = self.get_market_orders(pair)
        asks = sum([Decimal(i[1]) for i in order_book['asks']])
        bids = sum([Decimal(i[1]) for i in order_book['bids']])

        return {"bids": bids, "asks": asks}