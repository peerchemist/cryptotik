import requests
from .common import APIError, headers

class OKcoin:

    url = 'https://www.okcoin.com/api/'
    delimiter = "_"
    headers = headers
    taker_fee, maker_fee = 0, 0
    #private_commands = ('getopenorders', 'cancel', 'sellmarket', 'selllimit', 'buymarket', 'buylimit')
    public_commands = ('ticker.do', 'depth.do', 'trades.do')

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
                   20006: 'Required field missing'
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

        result = requests.get(cls.url + command, params=params, headers=cls.headers,
                              timeout=3)

        assert result.status_code == 200

        try:
            if result.json()["result"] is False:
                raise APIError(cls.error_codes.get(result.json()["errorCode"]))
        except:
            return result.json()

    @classmethod
    def get_market_ticker(cls, pair):
        '''returns simple current market status report'''

        return cls.api("ticker.do", {"symbol": cls.format_pair(pair)})["ticker"]

    """
    @classmethod
    def get_futures_ticker(cls, pair, contract):
        '''returns simple current market status report - futures market'''

        return cls.api("future_ticker.do", {"symbol": pair, "contract": contract})["ticker"]
    """

    @classmethod
    def get_market_order_book(cls, pair, depth=200):
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

        ask = order_book["asks"][0][0]
        bid = order_book["bids"][0][0]

        return Decimal(ask) - Decimal(bid)

    @classmethod
    def get_market_trade_history(cls, pair):
        '''get market trade history for last <depth> trades'''

        return cls.api("trades.do", {"symbol": cls.format_pair(pair)})
