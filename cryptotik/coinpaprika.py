# -*- coding: utf-8 -*-

from cryptotik.common import headers
from cryptotik.exceptions import APIError
import requests
import time
from typing import Union


class CoinPaprika:

    """coinpaprika.com wrapper"""

    url = "https://api.coinpaprika.com/v1/"
    name = "coinmarketcap"
    headers = headers

    def __init__(self, timeout=None, proxy=None):
        """initialize class"""

        if proxy:
            assert proxy.startswith("https"), {"Error": "Only https proxies supported."}
        self.proxy = {"https": proxy}

        if not timeout:
            self.timeout = (8, 15)
        else:
            self.timeout = timeout

        self.api_session = requests.Session()

    def _verify_response(self, response):
        raise NotImplementedError

    def fetch(self, path: str, params: dict = {}) -> Union[dict, list]:
        try:
            result = self.api_session.get(
                self.url + path,
                headers=self.headers,
                params=params,
                timeout=self.timeout,
                proxies=self.proxy,
            )
            result.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(e)

        return result.json()

    def get_coins(self) -> list:
        """list of all avaliable coins"""

        return self.fetch(path="/coins")

    def get_global(self) -> dict:
        """Get market overview data"""

        return self.fetch(path="/global")

    def get_coin_by_id(self, coin_id: str) -> dict:

        return self.fetch(path="/coins/{}".format(coin_id))

    def get_coin_twitter(self, coin_id: str) -> list:

        return self.fetch(path="/coins/{}/twitter".format(coin_id))

    def get_coin_events(self, coin_id: str) -> list:

        return self.fetch(path="/coins/{}/events".format(coin_id))

    def get_coin_exchanges(self, coin_id: str) -> list:

        return self.fetch(path="/coins/{}/exchanges".format(coin_id))

    def get_coin_markets(self, coin_id: str, quote: str = None) -> list:

        assert (
            quote
            in """BTC,ETH,USD,EUR,PLN,KRW,GBP,CAD,JPY,RUB,TRY,NZD,AUD,CHF,UAH,HKD,SGD,NGN,PHP,MXN,BRL,THB,CLP,CNY,CZK,DKK,HUF,IDR,ILS,INR,MYR,NOK,PKR,SEK,TWD,ZAR,VND,BOB,COP,PEN,ARS,ISK""".split(
                ","
            )
        )

        return self.fetch(
            path="/coins/{}/markets".format(coin_id), params={"quote": quote}
        )

    def get_market_ticker(self, coin_id: str, quote: str) -> dict:
        """Open/High/Low/Close values with volume and market_cap"""

        return self.fetch(
            path="/coins/{}/ohlcv/today".format(coin_id), params={"quote": quote}
        )

    def get_market_ohlcv_data(
        self,
        coin_id: str,
        quote: str,
        since: int,
        until: int = int(time.time()),
        limit: int = 366,
    ) -> list:

        assert quote in "USD,BTC".split(",")

        return self.fetch(
            path="/coins/{}/ohlcv/historical".format(coin_id),
            params={"quote": quote, "start": since, "end": until, "limit": limit},
        )
