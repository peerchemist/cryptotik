# -*- coding: utf-8 -*-

import hmac
import json
import hashlib
import time
import base64
import requests
from cryptotik.common import APIError, headers, ExchangeWrapper
from decimal import Decimal


class Cryptopia(ExchangeWrapper):

    url = 'https://www.cryptopia.co.nz/'
    namre = 'cryptopia'
    delimiter = "_"
    headers = headers
    taker_fee, maker_fee = 0.00, 0.00

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        pair = pair.replace("-", cls.delimiter)

        if not pair.isupper():
            return pair.upper()
        else:
            return pair

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

        nonce = str(self.get_nonce())
        md5 = hashlib.md5()
        md5.update(json.dumps(params).encode('utf-8'))
        rcb64 = base64.b64encode(md5.digest()).decode('utf-8')
        signature = self.apikey + "POST" + requests.compat.quote_plus(url).lower() + nonce + rcb64 
        hmacsignature = base64.b64encode(hmac.new(base64.b64decode(self.secret),
                        signature.encode('utf-8'),
                        hashlib.sha256).digest())
        header_value = "amx " + self.apikey + ":" + hmacsignature.decode('utf-8') + ":" + nonce

        try:
            result = self.api_session.post(url, json=params,
                                           headers={'Authorization': header_value},
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

        r = self.api(self.url + "api/getMarket/" + self.format_pair(pair))
        result={}
        result['bid']=r['BidPrice']
        result['ask']=r['AskPrice']
        result['last']=r['LastPrice']
        return result

    def get_market_volume(self, pair):
        ''' return volume of last 24h'''

        return self.api(self.url + "api/getMarket/" + 
                        self.format_pair(pair))['Volume']

    def get_market_trade_history(self, pair, limit=100):
        '''get market trade history'''

        return self.api(self.url + "api/getMarketHistory/" + 
                        self.format_pair(pair))[:limit]

    def get_market_orders(self, pair, limit=100):
        '''return order book for the market'''

        result = self.api(self.url + "api/GetMarketOrders/" + 
                        self.format_pair(pair) + "/" + str(limit))
        result['asks'] = result.pop('Buy')
        result['bids'] = result.pop('Sell')
        return result

    def get_market_spread(self, pair):
        '''return first buy order and first sell order'''

        order_book = self.get_market_orders(self.format_pair(pair))

        ask = order_book["asks"][0]['Price']
        bid = order_book["bids"][0]['Price']

        return Decimal(ask) - Decimal(bid)

    def get_market_depth(self, pair):
        '''return sum of all bids and asks'''

        order_book = self.get_market_orders(self.format_pair(pair))
        order_book = self.get_market_orders(self.format_pair(pair))
        asks = sum([Decimal(i['Volume']) for i in order_book['asks']])
        bids = sum([Decimal(i['Volume']) for i in order_book['bids']])

        return {"bids": bids, "asks": asks}

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
