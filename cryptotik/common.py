import abc
import six

class APIError(Exception):
    "Raise exception when the remote API returned an error."
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

    @abc.abstractmethod
    def get_nonce(self):
        raise NotImplementedError

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
        raise NotImplementedError

    @abc.abstractmethod
    def get_market_ticker(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_market_trade_history(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_market_orders(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_market_depth(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_market_spread(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_market_volume(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_balances(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_deposit_address(self):
        raise NotImplementedError

    @abc.abstractmethod
    def buy(self):
        raise NotImplementedError

    @abc.abstractmethod
    def sell(self):
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
