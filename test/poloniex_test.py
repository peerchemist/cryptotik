import pytest
from cryptotik import Poloniex
from decimal import Decimal

private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)


def test_format_pair():
    '''test string formating to match API expectations'''

    assert Poloniex.format_pair("btc-ppc") == "BTC_PPC"


def test_get_markets():
    '''test get_markets'''

    assert isinstance(Poloniex.get_markets(), list)
    assert "BTC_LTC" in Poloniex.get_markets()


def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = Poloniex.get_market_ticker("btc-ltc")

    assert isinstance(ticker, dict)
    assert list(ticker.keys()) == ['id', 'last', 'lowestAsk',
                                   'highestBid', 'percentChange',
                                   'baseVolume', 'quoteVolume',
                                   'isFrozen', 'high24hr', 'low24hr']


@pytest.mark.parametrize("depth", [10, 20, 50])
def test_get_market_orders(depth):
    '''test get_market_orderbook'''

    market_orders = Poloniex.get_market_orders("btc-ppc", depth)

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["asks"], list)
    assert isinstance(market_orders["bids"], list)


def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = Poloniex.get_market_trade_history("btc-ppc")

    assert isinstance(trade_history, list)
    assert list(trade_history[0].keys()) == ['globalTradeID', 'tradeID',
                                             'date', 'type', 'rate', 'amount',
                                             'total']


def test_get_full_market_trade_history():
    '''test get_full_market_trade_history'''

    trade_history = Poloniex.get_full_market_trade_history("btc-ppc")

    assert isinstance(trade_history, list)
    assert list(trade_history[0].keys()) == ['globalTradeID', 'tradeID',
                                             'date', 'type', 'rate', 'amount',
                                             'total']


def test_get_market_depth():
    '''test get_market_depth'''

    market_depth = Poloniex.get_market_depth("btc-ppc")

    assert isinstance(market_depth, dict)
    assert isinstance(market_depth["asks"], Decimal)


def test_get_market_spread():
    '''test get_market spread'''

    assert isinstance(Poloniex.get_market_spread("btc-vtc"), Decimal)


def test_get_loans():
    '''test get_loans'''

    assert isinstance(Poloniex.get_loans("eth"), dict)


def test_get_loans_depth():
    '''test get_loans_depth'''

    assert isinstance(Poloniex.get_loans_depth("eth"), dict)


def test_get_market_volume():
    '''test get_market_volume'''

    assert isinstance(Poloniex.get_market_volume("btc_eth"), dict)


@private
def test_get_balances(apikey, secret):
    '''test get_balances'''

    polo = Poloniex(apikey, secret, 130)

    assert isinstance(polo.get_balances("btc"), str)


@private
@pytest.mark.xfail
def test_get_order_history(apikey, secret):
    '''test get_order_history'''

    polo = Poloniex(apikey, secret, 130)
    order_history = polo.get_order_history("btc_eth")

    assert isinstance(order_history, list)
    assert list(order_history[0].keys()) == ['globalTradeID',
                                             'tradeID', 'date',
                                             'rate', 'amount', 'total',
                                             'fee', 'orderNumber', 'type',
                                             'category']


@private
def test_get_avaliable_balances(apikey, secret):
    '''test get_avaliable_balances'''

    polo = Poloniex(apikey, secret, 130)
    avaliable_balances = polo.get_available_balances()

    assert isinstance(avaliable_balances, dict)
    assert list(avaliable_balances.keys()) == ['exchange', 'margin']


@private
@pytest.mark.xfail
def test_get_margin_account_summary(apikey, secret):

    polo = Poloniex(apikey, secret, 130)
    margin_account_summary = polo.get_margin_account_summary()

    assert isinstance(margin_account_summary, dict)
    assert list(margin_account_summary.keys()) == ['currentMargin',
                                                   'lendingFees',
                                                   'netValue', 'pl',
                                                   'totalBorrowedValue',
                                                   'totalValue']


@private
def test_get_deposit_address(apikey, secret):
    '''test get_deposit_address'''

    polo = Poloniex(apikey, secret, 130)
    deposit_addr = polo.get_deposit_address("btc")

    assert isinstance(deposit_addr, str)
    assert deposit_addr.startswith("1")


@private
@pytest.mark.xfail
def test_generate_new_address(apikey, secret):
    '''test generate_new_address'''

    polo = Poloniex(apikey, secret, 130)

    assert polo.generate_new_address("eth")["success"] == 1


@private
def test_get_open_orders(apikey, secret):
    '''test get_open_orders'''

    polo = Poloniex(apikey, secret, 130)
    open_orders = polo.get_open_orders()

    assert isinstance(open_orders, dict)


@private
def test_get_fee_info(apikey, secret):
    '''test get_fee_info'''

    polo = Poloniex(apikey, secret, 130)
    fee_info = polo.get_fee_info()

    assert isinstance(fee_info, dict)
    assert list(fee_info.keys()) == ['makerFee', 'takerFee',
                                     'thirtyDayVolume', 'nextTier']


@private
def test_active_loans(apikey, secret):
    '''test get_active_loans'''

    polo = Poloniex(apikey, secret, 130)
    active_loans = polo.get_active_loans()

    assert isinstance(active_loans, dict)
    assert list(active_loans.keys()) == ['provided', 'used']


@private
def test_get_open_loan_offers(apikey, secret):
    '''test get_open_loan_offers'''

    polo = Poloniex(apikey, secret, 130)

    assert isinstance(polo.get_open_loan_offers(), list)


@private
def test_get_deposit_history(apikey, secret):
    '''test get_deposit_history'''

    polo = Poloniex(apikey, secret, 130)
    deposit_history = polo.get_deposit_history()

    assert isinstance(deposit_history, list)
    assert list(deposit_history[0].keys()) == ['currency', 'address',
                                               'amount', 'confirmations',
                                               'txid', 'timestamp', 'status']


@private
def test_get_withdrawal_history(apikey, secret):
    '''test get_deposit_history'''

    polo = Poloniex(apikey, secret, 130)
    withdrawal_history = polo.get_withdrawal_history()

    assert isinstance(withdrawal_history, list)
    assert list(withdrawal_history[0].keys()) == ['withdrawalNumber',
                                                  'currency', 'address',
                                                  'amount', 'fee', 'timestamp',
                                                  'status', 'ipAddress']


@private
def test_buy(apikey, secret):
    '''test buy'''

    polo = Poloniex(apikey, secret, 130)

    assert polo.buy("btc-ppc", 0.000001, 0.001) == "{'error': 'Total must be at least 0.0001.'}"


@private
def test_sell(apikey, secret):
    '''test sell'''

    polo = Poloniex(apikey, secret, 130)

    assert polo.sell("btc-ppc", 0.000001, 0.001) == "{'error': 'Total must be at least 0.0001.'}"


@private
def test_margin_buy(apikey, secret):
    '''test buy'''

    polo = Poloniex(apikey, secret, 130)

    assert polo.margin_buy("btc-eth", 0.000001, 0.001) == "{'error': 'Total must be at least 0.0001.'}"


@private
def test_margin_sell(apikey, secret):
    '''test buy'''

    polo = Poloniex(apikey, secret, 130)

    assert polo.margin_sell("btc-ppc", 0.000001, 0.001) == "{'error': 'Total must be at least 0.0001.'}"

