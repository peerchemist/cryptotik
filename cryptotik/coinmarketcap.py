from cryptotik.common import headers, ExchangeWrapper
from cryptotik.exceptions import APIError
import requests


class CoinMarketCap():

    url = 'https://api.coinmarketcap.com/v1/'
    name = 'coinmarketcap'
    headers = headers

    def __init__(self, timeout=None, proxy=None):
        '''initialize class'''

        if proxy:
            assert proxy.startswith('https'), {'Error': 'Only https proxies supported.'}
        self.proxy = {'https': proxy}

        if not timeout:
            self.timeout = (8, 15)
        else:
            self.timeout = timeout

        self.api_session = requests.Session()

    def _verify_response(self, response):
        raise NotImplementedError

    def api(self, url, params=None):
        '''call api'''

        try:
            result = self.api_session.get(url, headers=self.headers, 
                                          params=params, timeout=self.timeout,
                                          proxies=self.proxy)
            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        return result.json()

    def get_ticker(self, coin=None, convert_currency=None):
        ''' Get ticker for <currency>, convert price to <convert_currency> if needed
            Important: currency name is used instead of symbol'''

        if not convert_currency:
            l = self.api(self.url + "/ticker/?limit=0")
            if coin:
                l = [i for i in l if i['symbol'] == coin.upper()]
            return l

        if convert_currency:
            l = self.api(self.url + "ticker/" +
                            "?convert=" + convert_currency.upper() +
                            "&limit=0")
            if coin:
                l = [i for i in l if i['symbol'] == coin.upper()]
            return l

    def get_global(self, convert_currency=None):
        ''' Get global data, convert to <convert_currency> if needed'''

        if not convert_currency:
            return self.api(self.url + "global/")
        else:
            return self.api(self.url + "global/?convert=" +
                            convert_currency.upper())
