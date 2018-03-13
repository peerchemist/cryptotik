import pytest
from cryptotik.binance import Binance
from decimal import Decimal
from cryptotik.exceptions import APIError

private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)

bnb = Binance(pytest.config.getoption("--apikey"), 
            pytest.config.getoption("--secret"))


def test_format_pair():
    '''test string formating to match API expectations'''

    assert bnb.format_pair("eth-btc") == "ETHBTC"


def test_get_markets():
    '''test get_markets'''

    assert isinstance(bnb.get_markets(), list)
    assert "ethbtc" in bnb.get_markets()


@pytest.mark.parametrize("interval", ["15m", "30m", "1h"])
def test_get_market_ohlcv_data(interval):

    ohlcv = bnb.get_market_ohlcv_data('dash-eth', interval, limit=1)

    assert isinstance(ohlcv, list)


def test_get_summaries():

    assert isinstance(bnb.get_summaries(), list)
    assert isinstance(bnb.get_summaries()[0], dict)


def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = bnb.get_market_ticker("ETH-BTC")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == ['askPrice', 'askQty', 'bidPrice', 'bidQty',
                                     'closeTime', 'count', 'firstId', 'highPrice',
                                     'lastId', 'lastPrice', 'lastQty', 'lowPrice', 
                                     'openPrice', 'openTime', 'prevClosePrice', 
                                     'priceChange', 'priceChangePercent', 'quoteVolume',
                                      'symbol', 'volume', 'weightedAvgPrice']


def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = bnb.get_market_orders("eth-btc")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["asks"], list)
    assert isinstance(market_orders["bids"], list)


def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = bnb.get_market_trade_history("eth-btc", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert sorted(trade_history[0].keys()) == sorted(['id', 'isBestMatch', 'isBuyerMaker', 'price', 'qty', 'time'])


@private
def test_get_balances(apikey, secret):

    balances = bnb.get_balances()

    assert isinstance(balances, list)


@private
def test_get_deposit_address(apikey, secret):

    assert isinstance(bnb.get_deposit_address("eth"), dict)


@private
def test_get_withdraw_history(apikey, secret):

    assert isinstance(bnb.get_withdraw_history("eth"), list)


@private
def test_withdraw(apikey, secret):

    assert bnb.withdraw("eth", 1, 'PpcEaT3Rd0NTsendftMKDAKr331DXgHe3L')['msg'] == 'Insufficient balance.'


@private
@pytest.mark.parametrize("pair", ['salt-eth', 'zec-btc'])
def test_buy_market(apikey, secret, pair):

    assert isinstance(bnb.buy_market(pair, 1, test=True), dict)


@private
@pytest.mark.parametrize("pair", ['trx-btc', 'omg-eth'])
def test_sell_market(apikey, secret, pair):

    assert isinstance(bnb.sell_market(pair, 1, test=True), dict)


@private
def test_cancel_order(apikey, secret):

    with pytest.raises(APIError):
        bnb.cancel_order('invalid', 'btc')