# -*- coding: utf-8 -*-

import requests
import hashlib
from .common import APIError, headers

class OKcoin:

    url = 'https://www.okcoin.$/api/v1/' # OKcoin cny and usd markets do no use the same domain
    delimiter = "_"
    headers = headers
    taker_fee, maker_fee = 0, 0
    private_commands = ('userinfo.do', 'trade', 'trade_histroy', 'batch_trade', 'cancel_order', 'order_book',
                        'order_info', 'orders_info', 'order_history', 'withdraw', 'cancel_withdraw', 'withdraw_info',
                        'order_fee')
    public_commands = ('ticker.do', 'depth.do', 'trades.do')
    futures_public_commands = ('future_ticker.do', 'future_depth', 'future_trades', 'future_index')

    def __init__(self, apikey, secret, domain="com"):
        '''
        To use private API methods, initialize class with <partner_id> and <secret_key> arguments,
        you should also provide the OKcoin domain you registred at. OKcoin.com deals only with USD,
        and OKcoin.cn deals only with CNY.
        .com is taken as default.
        '''

        self.apikey = apikey
        self.secret = secret
        self.domain = domain

    error_codes = {10000: 'Required parameter can not be null',
                   10001: 'Requests are too frequent',
                   10002: 'System Error',
                   10003: 'Restricted list request, please try again later',
                   10004: 'IP restriction',
                   10005: 'Key does not exist',
                   10006: 'User does not exist',
                   10007: 'Signatures do not match',
                   10008: 'Illegal parameter',
                   10009: 'Order does not exist',
                   10010: 'Insufficient balance',
                   10011: 'Order is less than minimum trade amount',
                   10012: 'Unsupported symbol (not btc_cny or ltc_cny)',
                   10013: 'This interface only accepts https requests',
                   10014: 'Order price must be between 0 and 1,000,000',
                   10015: 'Order price differs from current market price too much',
                   10016: 'Insufficient coins balance',
                   20006: 'Required field missing',
                   20007: 'Illegal parameter'
                  }

    @classmethod
    def format_pair(cls, pair):
        """format the pair argument to format understood by remote API."""

        if not "_" in pair:
            pair = pair.replace("-", cls.delimiter)

        if not pair.islower():
            return pair.lower()
        else:
            return pair

    @classmethod
    def api(cls, command, params):
        """call api"""

        if "usd" in params["symbol"]: # OKcoin API uses .com domain for USD pairs
            result = requests.get(cls.url.replace("$", "com") + command, params=params,
                                  headers=cls.headers, timeout=3)
        if "cny" in params["symbol"]: # OKcoin API uses .cn domain for CNY pairs
            result = requests.get(cls.url.replace("$", "cn") + command, params=params,
                                  headers=cls.headers, timeout=3)

        assert result.status_code == 200, {"error": "http_error: " + str(result.status_code)}

        try: ## try to get the error
            if result.json().get("result") is False:

                try: # API is not consistant about naming error field
                    raise APIError(cls.error_codes.get(result.json()["errorCode"]))
                except KeyError:
                    raise APIError(cls.error_codes.get(result.json()["error_code"]))

        except AttributeError:
            pass

        return result.json()

    def build_signature(self, params):
        '''calculate signature for this API call'''

        sign = ''
        for key in sorted(params.keys()): # alphabetically sorted
            sign += key + '=' + str(params[key]) +'&'
        data = sign + 'secret_key=' + self.secret
        return hashlib.md5(data.encode("utf8")).hexdigest().upper()

    def private_api(self, command, params):
        '''handles private api methods'''

        if not self.apikey or not self.secret:
            raise ValueError("API key and secret key required!")

        params["api_key"] = self.apikey
        params["sign"] = self.build_signature(params)

        result = requests.post(self.url.replace("$", "com") + command, params=params,
                               headers=self.headers, timeout=3)

        if self.domain == "com":
            result = requests.get(self.url.replace("$", "com") + command, params=params,
                                  headers=self.headers, timeout=3)
        if self.domain == "cny":
            result = requests.get(self.url.replace("$", "cn") + command, params=params,
                                  headers=self.headers, timeout=3)

        assert result.status_code == 200, {"error": "http_error: " + str(result.status_code)}

        try: ## try to get the error
            if result.json().get("result") is False:
                # API is not consistent about naming error field
                if result.json()["errorCode"]:
                    raise APIError(self.error_codes.get(result.json()["errorCode"]))
                else:
                    raise APIError(self.error_codes.get(result.json()["error_code"]))

        except AttributeError:
            pass

        return result.json()

    @classmethod
    def get_market_ticker(cls, pair):
        '''returns simple current market status report'''

        return cls.api("ticker.do", {"symbol": cls.format_pair(pair)})["ticker"]

    @classmethod
    def get_market_orders(cls, pair, depth=200):
        '''get market depth up to 200'''

        assert depth <= 200, "maximum depth is 200"

        return cls.api("depth.do", {"symbol": cls.format_pair(pair), "size": depth})

    @classmethod
    def get_market_depth(cls, pair):
        '''get market depth'''

        from decimal import Decimal

        order_book = cls.get_market_order_book(cls.format_pair(pair))
        return {"bids": sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]]),
                "asks": sum([Decimal(i[1]) for i in order_book["asks"]])
               }

    @classmethod
    def get_market_spread(cls, pair):
        '''get market spread'''

        from decimal import Decimal

        order_book = cls.get_market_order_book(pair)

        ask = order_book["asks"][-1][0]
        bid = order_book["bids"][0][0]

        return Decimal(ask) - Decimal(bid)

    @classmethod
    def get_market_trade_history(cls, pair):
        '''get market trade history'''

        return cls.api("future_trades.do", {"symbol": cls.format_pair(pair)})

    @classmethod
    def get_futures_market_ticker(cls, pair, contract="this_week"):
        '''
        returns simple current market status report - futures market
        <contract> can be this_week|next_week|quarter
        '''

        return cls.api("future_ticker.do", {"symbol": cls.format_pair(pair),
                                            "contract_type": contract})["ticker"]

    @classmethod
    def get_futures_market_order_book(cls, pair, depth=200, contract="this_week"):
        '''
        get futures market depth up to 200
        <contract> can be this_week|next_week|quarter
        '''

        assert depth <= 200, "maximum depth is 200"

        return cls.api("depth.do", {"symbol": cls.format_pair(pair), "size": depth,
                                    "contract_type": contract})

    @classmethod
    def get_futures_market_depth(cls, pair, contract="this_week"):
        '''
        get market depth
        <contract> can be this_week|next_week|quarter
        '''

        from decimal import Decimal

        order_book = cls.get_futures_market_order_book(cls.format_pair(pair), contract=contract)
        return {"bids": sum([Decimal(i[0]) * Decimal(i[1]) for i in order_book["bids"]]),
                "asks": sum([Decimal(i[1]) for i in order_book["asks"]])
               }

    @classmethod
    def get_futures_market_spread(cls, pair, contract="this_week"):
        '''
        get market spread
        <contract> can be this_week|next_week|quarter
        '''

        from decimal import Decimal

        order_book = cls.get_futures_market_order_book(pair, contract=contract)

        ask = order_book["asks"][-1][0]
        bid = order_book["bids"][0][0]

        return Decimal(ask) - Decimal(bid)

    @classmethod
    def get_futures_market_trade_history(cls, pair, contract="this_week"):
        '''
        get futures market trade history
        <contract> can be this_week|next_week|quarter
        '''

        return cls.api("trades.do", {"symbol": cls.format_pair(pair),
                                     "contract_type": contract})

    @classmethod
    def get_futures_market_index(cls, pair):
        '''get futures index price'''

        return cls.api("future_index.do", {"symbol": cls.format_pair(pair)})

    #########################################################
    #  Private API commands from here on
    #########################################################

    def get_userinfo(self):
        '''Get User Account Info'''

        self.private_api("userinfo.do", {})

    def buy_limit(self, pair, rate, amount):
        '''spot limit buy order'''

        assert amount > 0.1, "minimum buying unit is 0.1"

        self.private_api("trade.do", {"symbol": pair, "price": rate,
                                      "amount": amount, "type": "limit"})

    def buy_market(self, pair, rate, amount):
        '''spot market buy order'''

        assert amount > 0.1, "minimum buying unit is 0.1"

        self.private_api("trade.do", {"symbol": pair, "price": rate,
                                      "amount": amount, "type": "market"})
    
                                      

    