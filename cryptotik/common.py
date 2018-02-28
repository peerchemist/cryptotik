# -*- coding: utf-8 -*-

import abc
import six


class APIError(Exception):
    "Raise exception when the remote API returned an error."
    pass


class OutdatedBaseCurrenciesError(Exception):
    "Raise exception when hardcoded base currencies are outdated."
    pass


headers = {    # common HTTPS headers
    'Accept': 'application/json',
    'Accept-Charset': 'utf-8',
    'Accept-Encoding': 'identity',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    "Content-type": "application/x-www-form-urlencoded"
    }


@six.add_metaclass(abc.ABCMeta)
class ExchangeWrapper:

    def __init__(self, apikey, secret, timeout):
        self.apikey = apikey
        self.secret = secret

    @property
    @abc.abstractmethod
    def name(self):
        '''lowercase name of the exchange.'''
        self.name

    @property
    @abc.abstractmethod
    def quote_order(self):
        '''does quote come before or after the delimiter [0, 1]'''
        self.quote_order

    @property
    @abc.abstractmethod
    def base_currencies(self):
        '''The base currency – also called the transaction currency -
        is the first currency appearing in a currency pair quotation,
        followed by the second part of the quotation, called the quote
        currency or the counter currency.'''
        self.base_currencies

    @abc.abstractmethod
    def get_base_currencies(self):
        '''get the list of base currencies on this exchange.'''
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def url(self):
        self.url

    @property
    @abc.abstractmethod
    def delimiter(self):
        self.delimiter

    @abc.abstractmethod
    def get_nonce(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _verify_response(self):
        '''verify if API responded properly and raise apropriate error.'''
        raise NotImplementedError

    @abc.abstractmethod
    def _generate_signature(self):
        '''generate signed signature for the private api methods.'''
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def format_pair(self):
        raise NotImplementedError

    @abc.abstractmethod
    def api(self):
        raise NotImplementedError

    @abc.abstractmethod
    def private_api(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_markets(self):
        '''
        :params:
            -
        :return: 
            list -> str
            example: ['bcheur', 'bchusd', 'bchxbt']
        '''
        raise NotImplementedError

    @abc.abstractmethod
    def get_market_ticker(self, pair):
        '''
        :params:
            pair: str
        :return: 
            dict['ask': float, 'bid': float, 'last': float]
            example: {'ask': Decimal, 'bid': Decimal, 'last': Decimal}
        '''
        raise NotImplementedError

    @abc.abstractmethod
    def get_market_trade_history(self, pair, limit):
        '''
        :params:
            pair: str, limit: int
        :return:
            list -> dict['timestamp': datetime.datetime,
                        'is_sale': bool,
                        'rate': Decimal,
                        'amount': Decimal,
                        'trade_id': any]
        '''
        raise NotImplementedError

    @abc.abstractmethod
    def get_market_orders(self, pair, limit):
        '''
        :params:
            pair: str, limit: int
        :return:
            dict['bids': list, 'asks': list]
        '''
        raise NotImplementedError

    @abc.abstractmethod
    def get_market_depth(self, pair):
        '''
        :params:
            pair: str
        :return:
            dict['bids': Decimal, 'asks': Decimal]
        '''
        raise NotImplementedError

    @abc.abstractmethod
    def get_market_spread(self, pair):
        '''
        :params:
            pair: str
        :return:
            Decimal
        '''
        raise NotImplementedError

    @abc.abstractmethod
    def get_market_volume(self, pair):
        '''
        :params:
            pair: str
        :return:
            float
        '''
        raise NotImplementedError

    @abc.abstractmethod
    def get_balances(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_deposit_address(self):
        raise NotImplementedError

    @abc.abstractmethod
    def buy_limit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def sell_limit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def cancel_order(self):
        raise NotImplementedError

    @abc.abstractmethod
    def cancel_all_orders(self):
        '''Cancel all active orders.'''
        raise NotImplementedError

    @abc.abstractmethod
    def get_order(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_open_orders(self):
        raise NotImplementedError

    @abc.abstractmethod
    def withdraw(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_deposit_history(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_withdraw_history(self):
        raise NotImplementedError
