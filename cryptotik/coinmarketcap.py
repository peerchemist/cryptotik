from cryptotik.common import APIError, headers, ExchangeWrapper
import requests


class CoinMarketCap():
    
    url = 'https://api.coinmarketcap.com/v1/'
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

    def api(self, url, params=None):
        '''call api'''

        try:
            result = self.api_session.get(url, headers=self.headers, 
                                    params=params, timeout=self.timeout,
                                    proxies=self.proxy)
            assert result.status_code == 200, {'error: ' + str(result.json())}
            return result.json()
        except requests.exceptions.RequestException as e:
            print("Error!", e)

    def get_ticker(self, coin, convert_currency=None):
        ''' Get ticker for <currency>, convert price to <convert_currency> if needed
            Important: currency name is used instead of symbol'''

        if not convert_currency:
            l = self.api(self.url + "ticker/")
            if coin:
                l = [i for i in l if i['symbol'] == coin.upper()]
            return l

        if convert_currency:
            l = self.api(self.url + "ticker/" +
                            "?convert=" + convert_currency.upper())
            if coin:
                l = [i for i in l if i['symbol'] == coin.upper()]
            return l

    def get_global(self, convert_currency=None):
        ''' Get global data, convert to <convert_currency> if needed'''

        if not convert_currency:
            return self.api(self.url + "global/")
        else:
            return self.api(self.url + "global/?convert=" +
                            convert_currency.upper())ency> if needed'''

        if not convert_currency:
            return self.api(self.url + "global/")
        else:
            return self.api(self.url + "global/?convert=" +
                            convert_currency.upper())
