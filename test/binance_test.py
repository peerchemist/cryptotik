import pytest
from cryptotik.binance import Binance
from decimal import Decimal

private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)


def test_format_pair():
    '''test string formating to match API expectations'''

    assert Binance.format_pair("eth-btc") == "ETHBTC"


def test_get_markets():
    '''test get_markets'''

    assert isinstance(Binance.get_markets(), list)
    assert "ethbtc" in Binance.get_markets()


def test_get_summaries():

    assert isinstance(Bittrex.get_summaries(), list)
    assert isinstance(Bittrex.get_summaries()[0], dict)


def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = Binance.get_market_ticker("ETH-BTC")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == ['askPrice', 'askQty', 'bidPrice', 'bidQty',
                                     'closeTime', 'count', 'firstId', 'highPrice',
                                     'lastId', 'lastPrice', 'lastQty', 'lowPrice', 
                                     'openPrice', 'openTime', 'prevClosePrice', 
                                     'priceChange', 'priceChangePercent', 'quoteVolume',
                                      'symbol', 'volume', 'weightedAvgPrice']

def test_get_market_orders():
    '''test get_market_orderbook'''

    market_orders = Binance.get_market_orders("eth-btc")

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["asks"], list)
    assert isinstance(market_orders["bids"], list)

def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = Binance.get_market_trade_history("eth-btc", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert sorted(trade_history[0].keys()) == sorted(['a', 'p', 'q', 'f', 'l', 'T', 'm', 'M'])

def test_get_market_depth():
    '''test get_market_depth'''

    market_depth = Binance.get_market_depth("eth-btc")

    assert isinstance(market_depth, dict)
    assert isinstance(market_depth["asks"], Decimal)

def test_get_market_spread():
    '''test get_market spread'''

    assert isinstance(Binance.get_market_spread("eth-btc"), Decimal)

@private
def test_get_balances(apikey, secret):

    bin = Binance(apikey, secret)
    balances = bin.get_balances()

    assert isinstance(balances, list)

@private
def test_get_deposit_address(apikey, secret):

    bin = Binance(apikey, secret)

    assert isinstance(bin.get_deposit_address("eth"), dict)

@private
def test_get_withdraw_history(apikey, secret):

    bin = Binance(apikey, secret)

    assert isinstance(bin.get_withdraw_history("eth"), list)

@pytest.mark.xfail
@private
def test_withdraw(apikey, secret):

    print('This is made to fail because of lack of permissions' + 
            ', so make sure your testing API key does not allow that.')
    bin = Binance(apikey, secret)

    with pytest.raises(AssertionError):
        bin.withdraw("eth", 1, 'PpcEaT3Rd0NTsendftMKDAKr331DXgHe3L')

@private
def test_buy(apikey, secret):

    bin = Binance(apikey, secret)

    with pytest.raises(AssertionError):
        bin.buy("eth_btc", 0.05, 1)


@private
def test_sell(apikey, secret):

    bin = Binance(apikey, secret)

    with pytest.raises(AssertionError):
        bin.sell("ltc_btc", 1, 0.25)

@private
def test_cancel_order(apikey, secret):

    bin = Binance(apikey, secret)

    with pytest.raises(AssertionError):
        bin.cancel_order('invalid', 'btc')