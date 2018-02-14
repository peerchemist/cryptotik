# -*- coding: utf-8 -*-

'''https://www.bitstamp.net/api/'''

import requests
from decimal import Decimal
import time
from cryptotik.common import headers, ExchangeWrapper, APIError
import hmac
import hashlib


class Bitstamp(ExchangeWrapper):

    def __init__(self, apikey=None, secret=None, customer_id=None,
                 timeout=None, proxy=None):

        if apikey:
            self._apikey = apikey
            self._secret = secret
            self._customer_id = customer_id

        if proxy:
            assert proxy.startswith('https'), {'Error': 'Only https proxies supported.'}
        self.proxy = {'https': proxy}

        if not timeout:
            self.timeout = (8, 15)
        else:
            self.timeout = timeout

        self.api_session = requests.Session()

    public_commands = ("ticker", "transactions", "order_book")
    private_commands = ("balance", "user_transactions", "open_orders", "order_status",
                        "cancel_order", "cancel_all_orders", "buy",
                        "sell")

    name = 'bitstamp'
    url = 'https://www.bitstamp.net/'
    api_url = url + 'api/'
    delimiter = ""
    case = "lower"
    headers = headers
    _markets = 'btcusd, btceur, eurusd, xrpusd, xrpeur, xrpbtc, ltcusd, ltceur, ltcbtc, ethusd, etheur, ethbtc'.split(', ')
    maker_fee, taker_fee = 0.002, 0.002

    def get_nonce(self):
        '''return nonce integer'''

        nonce = getattr(self, '_nonce', 0)
        if nonce:
            nonce += 1
        # If the unix time is greater though, use that instead (helps low
        # concurrency multi-threaded apps always call with the largest nonce).
        self._nonce = max(int(time.time() * 1000000), nonce)
        return self._nonce

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        pair = pair.replace("-", cls.delimiter)

        if not pair.islower():
            return pair.lower()
        else:
            return pair

    def _verify_response(self, response):
        '''verify if API responded properly and raise apropriate error.'''

        if 'v2' in response.url:  # works only for v2 calls
            try:
                if response.json()['error']:
                    raise APIError(response.json()['reason'])
            except (KeyError, TypeError):
                pass

    def api(self, command):
        """call remote API"""

        try:
            response = self.api_session.get(self.api_url + 'v2/' + command, headers=self.headers,
                                            timeout=self.timeout, proxies=self.proxy)

            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            raise APIError(e)

        self._verify_response(response)
        return response.json()

    def private_api(self, command, data={}):
        '''handles private api methods'''

        if not self._customer_id or not self._apikey or not self._secret:
            raise ValueError("A Key, Secret and customer_id required!")

        nonce = self.get_nonce()
        data['key'] = self._apikey
        message = str(nonce) + self._customer_id + self._apikey

        sig = hmac.new(self._secret.encode('utf-8'),
                       msg=message.encode('utf-8'),
                       digestmod=hashlib.sha256).hexdigest().upper()

        data['signature'] = sig
        data['nonce'] = nonce

        try:
            response = self.api_session.post(url=self.api_url + command,
                                             data=data,
                                             headers=self.headers,
                                             timeout=self.timeout,
                                             proxies=self.proxy)

            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        self._verify_response(response)
        return response.json()

    def get_markets(self):
        '''get all market pairs supported by the exchange'''

        return self._markets

    def get_summaries(self):
        '''get summary of all active markets'''

        raise NotImplementedError

    def get_market_ticker(self, pair):
        """return ticker for market <pair>"""

        pair = self.format_pair(pair)
        return self.api("ticker/" + pair)

    def get_market_orders(self, pair):
        """returns market order book for <pair>"""

        pair = self.format_pair(pair)
        return self.api("order_book/" + pair)

    def get_market_trade_history(self, pair, since="hour"):
        """get market trade history; since {minute, hour, day}"""

        pair = self.format_pair(pair)

        return self.api("transactions/" + pair + "/?time={0}".format(since))

    def get_market_depth(self, pair):
        """get market order book depth"""

        pair = self.format_pair(pair)
        order_book = self.get_market_orders(pair)
        return {"bids": sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]]),
                "asks": sum([Decimal(i[1]) for i in order_book["asks"]])}

    def get_market_spread(self, pair):
        """get market spread"""

        pair = self.format_pair(pair)

        order_book = self.get_market_orders(pair)
        return Decimal(order_book["asks"][0][0]) - Decimal(order_book["bids"][0][0])

    def get_market_volume(self, pair):
        '''return market volume [of last 24h]'''

        pair = self.format_pair(pair)

        return self.get_market_ticker(pair)['volume']

    ########################
    # Private methods bellow
    ########################

    def get_balances(self, coin=None):
        '''Returns the values relevant to the specified <coin> parameter.'''

        if not coin:
            return self.private_api("v2/balance/")
        else:
            return {k: v for k, v in self.private_api("v2/balance/").items() if k.startswith(coin.lower())}

    def get_deposit_address(self, coin=None):
        '''get deposit address'''

        if coin == 'btc':
            command = 'bitcoin_deposit_address/'
        if coin == 'ltc':
            command = 'v2/ltc_address/'
        if coin == 'eth':
            command = 'v2/eth_address/'
        if coin == 'xrp':
            command = 'ripple_address/'
        if coin == 'bch':
            command = 'v2/bch_address/'

        return self.private_api(command)

    def get_liquidation_address(self, fiat):
        '''Creates new liquidation address which will automatically sell your BTC for specified liquidation_currency.'''

        return self.private_api('v2/liquidation_address/new/',
                                data={'liquidation_currency': fiat.lower()})

    def get_liquidation_address_info(self, address=None):
        '''Shows transactions (BTC to liquidation_currency) for liquidation address.'''

        return self.private_api('v2/liquidation_address/info/',
                                data={'address': address})

    def buy_limit(self, pair, rate, amount, daily_order=False):
        '''submit limit buy order

        daily_order: opens buy limit order which will be canceled at 0:00 UTC unless it already has been executed. Possible value: True'''

        pair = self.format_pair(pair)
        return self.private_api('v2/buy/{}/'.format(pair),
                                data={'amount': amount,
                                      'price': rate,
                                      'daily_order': daily_order
                                      }
                                )

    def buy_market(self, pair, amount):
        '''submit market buy order'''

        pair = self.format_pair(pair)
        return self.private_api('v2/buy/market/{}/'.format(pair),
                                data={'amount': amount}
                                )

    def sell_limit(self, pair, rate, amount, daily_order=False):
        '''submit limit sell order'''

        pair = self.format_pair(pair)
        return self.private_api('v2/sell/{}/'.format(pair),
                                data={'amount': amount,
                                      'price': rate,
                                      'daily_order': daily_order
                                      }
                                )

    def sell_market(self, pair, amount):
        '''submit market sell order'''

        pair = self.format_pair(pair)
        return self.private_api('v2/sell/market/{}/'.format(pair),
                                data={'amount': amount})

    def cancel_order(self, order_id):
        '''cancel order by <order_id>'''

        return self.private_api('v2/cancel_order/', data={'id': order_id})

    def cancel_all_orders(self):
        '''cancel all active orders'''

        return self.private_api('cancel_all_orders/')

    def get_open_orders(self, pair):
        '''Get open orders.'''

        pair = self.format_pair(pair)
        return self.private_api("v2/open_orders/{}/".format(pair))

    def get_order(self, order_id):
        '''get order information'''

        return self.private_api('orders_status/', data={'id': order_id})

    def withdraw(self, coin, amount, address):
        '''withdraw cryptocurrency'''

        if coin == 'btc':
            command = 'bitcoin_withdrawal/'
        if coin == 'ltc':
            command = 'v2/ltc_withdrawal/'
        if coin == 'eth':
            command = 'v2/eth_withdrawal/'
        if coin == 'xrp':
            command = 'ripple_withdrawal/'
        if coin == 'bch':
            command = 'v2/bch_withdrawal/'

        return self.private_api(command, data={'amount': amount,
                                               'address': address}
                                )

    def get_transaction_history(self):
        '''Returns the history of transactions.'''

        raise NotImplementedError

    def get_deposit_history(self, coin=None):
        '''get deposit history'''

        raise NotImplementedError

    def get_withdraw_history(self, coin=None, timedelta=50000000):
        '''get withdrawals history'''

        return self.private_api('v2/withdrawal-requests/',
                                data={'timedelta': timedelta})
