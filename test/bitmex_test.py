import pytest
from cryptotik.bitmex import Bitmex
from decimal import Decimal
import time
from cryptotik.exceptions import APIError


private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)

bitmex = Bitmex(testnet=True)


def test_format_pair():
    '''test string formating to match API expectations'''

    assert bitmex.format_pair("xbt-usd") == "XBTUSD"


def test_get_markets():
    '''test get_markets'''

    assert isinstance(bitmex.get_markets(), list)
    assert "XBTUSD" in bitmex.get_markets()


def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = bitmex.get_market_ticker('xbtusd')

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == sorted(['lastPrice', 'lastChangePcnt',
                                            'lastTickDirection', 'lowPrice',
                                            'prevClosePrice', 'timestamp',
                                            'volume24h', 'vwap'])


def test_get_market_volume():

    vol = bitmex.get_market_volume('xbtusd')

    assert isinstance(vol, int)


def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = bitmex.get_market_orders("xbtusd", 25)

    assert isinstance(market_orders, list)
    assert isinstance(market_orders[0], dict)
    assert sorted(market_orders[0].keys()) == sorted(['symbol', 'id', 'side',
                                                     'size', 'price'])


def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = bitmex.get_market_trade_history("xbtusd", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert isinstance(trade_history[0], dict)


def test_get_funding_history():

    history = bitmex.get_funding_history("xbtusd", 10)

    assert isinstance(history, list)
    assert len(history) == 10
    assert isinstance(history[0], dict)


def test_generate_signature():

    bitmex.secret = "chNOOS4KvNXR_Xq4k4c9qsfoKWvnDecLATCRlcBwyKDYnWgO"
    bitmex.apikey = "LAqUlngMIQkIUjXMUreyu3qn"

    url = "/order"
    params = {"symbol": "XBTM15", "price": 219.0,
              "clOrdID": "mm_bitmex_1a/oemUeQ4CAJZgP3fjHsA",
              "orderQty": 98}
    expires = 1518064238

    sig = bitmex._generate_signature(url, params, expires)

    assert sig == "1749cd2ccae4aa49048ae09f0b95110cee706e0944e6a14ad0b3a8cb45bd336b"


@private
def test_get_balances(apikey, secret):

    balances = bitmex.get_balances()

    assert isinstance(balances, dict)


@private
def test_get_deposit_address(apikey, secret):

    assert isinstance(bitmex.get_deposit_address("xbt"), str)


@private
def test_get_withdraw_history(apikey, secret):

    assert isinstance(bitmex.get_withdraw_history("xbt"), list)


@private
def test_withdraw(apikey, secret):

    print('This is made to fail because of fake address')

    with pytest.raises(APIError):
        response = bitmex.withdraw("eur", 0.01, 'fake_address')
        assert response['error'][0] == 'Funding: Unknown withdraw key'


@private
def test_buy(apikey, secret):

    with pytest.raises(APIError):
        bitmex.buy_limit("bch-eur", 0.0005, 0.0005)


@private
def test_sell_limit(apikey, secret):

    with pytest.raises(APIError):
        bitmex.sell_limit("bch-eur", 0.0005, 0.0005)


@private
def test_cancel_order(apikey, secret):

    with pytest.raises(APIError):
        bitmex.cancel_order('invalid')
