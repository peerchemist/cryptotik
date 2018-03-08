import pytest
from cryptotik import Poloniex
from cryptotik.exceptions import APIError
from decimal import Decimal

private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)


polo = Poloniex()


def test_format_pair():
    '''test string formating to match API expectations'''

    assert polo.format_pair("btc-ppc") == "BTC_PPC"


def test_get_base_currencies():

    polo.get_base_currencies()


def test_get_markets():
    '''test get_markets'''

    assert isinstance(polo.get_markets(), list)
    assert "BTC_LTC" in polo.get_markets()


def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = polo.get_market_ticker("btc-ltc")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == sorted(['id', 'last', 'lowestAsk',
                                   'highestBid', 'percentChange',
                                   'baseVolume', 'quoteVolume',
                                   'isFrozen', 'high24hr', 'low24hr'])


@pytest.mark.parametrize("depth", [10, 20, 50])
def test_get_market_orders(depth):
    '''test get_market_orderbook'''

    market_orders = polo.get_market_orders("btc-ppc", depth)

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["asks"], list)
    assert isinstance(market_orders["bids"], list)


@pytest.mark.parametrize("depth", [1, 201])
def test_get_market_trade_history(depth):
    '''test get_market_trade_history'''

    if depth < 200:

        trade_history = polo.get_market_trade_history("btc-ppc", depth)

        assert isinstance(trade_history, list)
        assert sorted(trade_history[0].keys()) == sorted(['globalTradeID', 'tradeID',
                                                'date', 'type', 'rate', 'amount',
                                                'total'])

    if depth > 200:

        try:
            trade_history = polo.get_market_trade_history("btc-ppc", depth)
        except APIError:
            assert True


def test_get_full_market_trade_history():
    '''test get_full_market_trade_history'''

    trade_history = polo.get_full_market_trade_history("btc-ppc")

    assert isinstance(trade_history, list)
    assert sorted(trade_history[0].keys()) == sorted(['globalTradeID', 'tradeID',
                                             'date', 'type', 'rate', 'amount',
                                             'total'])

def test_get_loans():
    '''test get_loans'''

    assert isinstance(polo.get_loans("eth"), dict)


def test_get_loans_depth():
    '''test get_loans_depth'''

    assert isinstance(polo.get_loans_depth("eth"), dict)


def test_get_market_volume():
    '''test get_market_volume'''

    assert isinstance(polo.get_market_volume("btc_eth"), dict)


@private
def test_get_balances(apikey, secret):
    '''test get_balances'''

    polo = Poloniex(apikey, secret, 20)

    assert isinstance(polo.get_balances("btc"), str)


@private
@pytest.mark.xfail
def test_get_order_history(apikey, secret):
    '''test get_order_history'''

    polo = Poloniex(apikey, secret, 20)
    order_history = polo.get_order_history("btc_eth")

    assert isinstance(order_history, list)
    assert sorted(order_history[0].keys()) == sorted(['globalTradeID',
                                             'tradeID', 'date',
                                             'rate', 'amount', 'total',
                                             'fee', 'orderNumber', 'type',
                                             'category'])


@private
def test_get_avaliable_balances(apikey, secret):
    '''test get_avaliable_balances'''

    polo = Poloniex(apikey, secret, 20)
    avaliable_balances = polo.get_available_balances()

    assert isinstance(avaliable_balances, dict)
    assert sorted(avaliable_balances.keys()) == sorted(['exchange', 'margin'])


@private
@pytest.mark.xfail
def test_get_margin_account_summary(apikey, secret):

    polo = Poloniex(apikey, secret, 20)
    margin_account_summary = polo.get_margin_account_summary()

    assert isinstance(margin_account_summary, dict)
    assert sorted(margin_account_summary.keys()) == sorted(['currentMargin',
                                                            'lendingFees',
                                                            'netValue', 'pl',
                                                            'totalBorrowedValue',
                                                            'totalValue'])


@private
def test_get_deposit_address(apikey, secret):
    '''test get_deposit_address'''

    polo = Poloniex(apikey, secret, 20)
    deposit_addr = polo.get_deposit_address("btc")

    assert isinstance(deposit_addr, str)
    assert deposit_addr.startswith("1")


@private
@pytest.mark.xfail
def test_generate_new_address(apikey, secret):
    '''test generate_new_address'''

    polo = Poloniex(apikey, secret, 20)

    assert polo.get_new_deposit_address("eth")["success"] == 1


@private
def test_get_open_orders(apikey, secret):
    '''test get_open_orders'''

    polo = Poloniex(apikey, secret, 20)
    open_orders = polo.get_open_orders()

    assert isinstance(open_orders, dict)


@private
def test_get_fee_info(apikey, secret):
    '''test get_fee_info'''

    polo = Poloniex(apikey, secret, 20)
    fee_info = polo.get_fee_info()

    assert isinstance(fee_info, dict)
    assert sorted(fee_info.keys()) == sorted(['makerFee', 'takerFee',
                                     'thirtyDayVolume', 'nextTier'])


@private
def test_active_loans(apikey, secret):
    '''test get_active_loans'''

    polo = Poloniex(apikey, secret, 20)
    active_loans = polo.get_active_loans()

    assert isinstance(active_loans, dict)
    assert sorted(active_loans.keys()) == sorted(['provided', 'used'])


@private
def test_get_open_loan_offers(apikey, secret):
    '''test get_open_loan_offers'''

    polo = Poloniex(apikey, secret, 20)
    
    assert isinstance(polo.get_open_loan_offers(), list)


@private
def test_get_deposit_history(apikey, secret):
    '''test get_deposit_history'''

    polo = Poloniex(apikey, secret, 20)
    with pytest.raises(APIError):
        deposit_history = polo.get_deposit_history()

        assert isinstance(deposit_history, list)
        assert sorted(deposit_history[0].keys()) == sorted(['currency', 'address',
                                                'amount', 'confirmations',
                                                'txid', 'timestamp', 'status'])


@private
def test_get_withdrawal_history(apikey, secret):
    '''test get_deposit_history'''

    polo = Poloniex(apikey, secret, 20)
    with pytest.raises(APIError):
        withdrawal_history = polo.get_withdraw_history()

        assert isinstance(withdrawal_history, list)
        assert sorted(withdrawal_history[0].keys()) == sorted(['withdrawalNumber',
                                                    'currency', 'address',
                                                    'amount', 'fee', 'timestamp',
                                                    'status', 'ipAddress'])


@private
def test_buy_limit(apikey, secret):
    '''test buy'''

    polo = Poloniex(apikey, secret, 20)
    with pytest.raises(APIError):
        assert polo.buy_limit("btc-ppc", 0.000001, 0.001) == {'error': 'Total must be at least 0.0001.'}


@private
def test_sell_limit(apikey, secret):
    '''test sell'''

    polo = Poloniex(apikey, secret, 20)
    with pytest.raises(APIError):
        assert polo.sell_limit("btc-ppc", 0.000001, 0.001) == {'error': 'Total must be at least 0.0001.'}


@private
def test_buy_margin(apikey, secret):
    '''test buy'''

    polo = Poloniex(apikey, secret, 20)
    with pytest.raises(APIError):
        assert polo.buy_margin("btc-eth", 0.000001, 0.001) == {'error': 'Total must be at least 0.0001.'}


@private
def test_sell_margin(apikey, secret):
    '''test sell'''

    polo = Poloniex(apikey, secret, 20)
    with pytest.raises(APIError):
        assert polo.sell_margin("btc-ltc", 0.000001, 0.001) == {'error': 'Total must be at least 0.0001.'}
