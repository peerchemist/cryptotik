import pytest
from cryptotik import Bittrex
from decimal import Decimal

private = pytest.mark.skipif(
    not pytest.config.getoption("--apikey"),
    reason="needs --apikey option to run."
)

btrx = Bittrex()


def test_format_pair():
    '''test string formating to match API expectations'''

    assert btrx.format_pair("btc_ppc") == "btc-ppc"


def test_get_markets():
    '''test get_markets'''

    assert isinstance(btrx.get_markets(), list)
    assert "btc-ltc" in btrx.get_markets()


def test_get_summaries():

    assert isinstance(btrx.get_summaries(), list)
    assert isinstance(btrx.get_summaries()[0], dict)


def test_get_market_ticker():
    '''test get_market_ticker'''

    ticker = btrx.get_market_ticker("btc-ltc")

    assert isinstance(ticker, dict)
    assert sorted(ticker.keys()) == ['Ask', 'Bid', 'Last']


@pytest.mark.parametrize("depth", [10, 20, 50])
def test_get_market_orders(depth):
    '''test get_market_orderbook'''

    market_orders = btrx.get_market_orders("btc-ppc", depth)

    assert isinstance(market_orders, dict)
    assert isinstance(market_orders["buy"], list)
    assert isinstance(market_orders["sell"], list)


def test_get_market_trade_history():
    '''test get_market_trade_history'''

    trade_history = btrx.get_market_trade_history("btc-ppc", 10)

    assert isinstance(trade_history, list)
    assert len(trade_history) == 10
    assert sorted(trade_history[0].keys()) == ['FillType', 'Id',
                                               'OrderType', 'Price',
                                               'Quantity', 'TimeStamp',
                                               'Total']


def test_get_market_depth():
    '''test get_market_depth'''

    market_depth = btrx.get_market_depth("btc-ppc")

    assert isinstance(market_depth, dict)
    assert isinstance(market_depth["asks"], Decimal)


def test_get_market_spread():
    '''test get_market spread'''

    assert isinstance(btrx.get_market_spread("btc-vtc"), Decimal)


@private
def test_get_balances(apikey, secret):
    '''test get_balances'''

    btrx = Bittrex(apikey, secret)
    balances = btrx.get_balances()

    assert isinstance(balances, list)
    assert sorted(balances[0].keys()) == sorted(['Available',
                                                 'Balance',
                                                 'CryptoAddress',
                                                 'Currency',
                                                 'Pending'])


@private
def test_get_open_orders(apikey, secret):
    '''test get_balances'''

    btrx = Bittrex(apikey, secret)
    orders = btrx.get_open_orders()

    if orders:
        assert isinstance(orders, list)
        assert sorted(orders[0].keys()) == sorted(['CancelInitiated',
                                                   'Closed',
                                                   'CommissionPaid',
                                                   'Condition',
                                                   'ConditionTarget',
                                                   'Exchange',
                                                   'ImmediateOrCancel',
                                                   'IsConditional',
                                                   'Limit',
                                                   'Opened',
                                                   'OrderType',
                                                   'OrderUuid',
                                                   'Price',
                                                   'PricePerUnit',
                                                   'Quantity',
                                                   'QuantityRemaining',
                                                   'Uuid'])


@private
@pytest.mark.xfail
def test_get_deposit_address(apikey, secret):
    '''test get_deposit_address'''

    btrx = Bittrex(apikey, secret)

    assert isinstance(btrx.get_deposit_address("btc"), str)


@private
def test_buy(apikey, secret):
    '''test buy'''

    btrx = Bittrex(apikey, secret)
    buy = btrx.buy("btc_ppc", 0.0000001, 0.0001)

    assert buy == {'message': 'DUST_TRADE_DISALLOWED_MIN_VALUE_50K_SAT',
                   'result': None,
                   'success': False
                   }


@private
def test_sell(apikey, secret):
    '''test buy'''

    btrx = Bittrex(apikey, secret)
    sell = btrx.sell("btc_ppc", 0.0000001, 0.0001)

    assert sell == {'message': 'DUST_TRADE_DISALLOWED_MIN_VALUE_50K_SAT',
                    'result': None,
                    'success': False
                    }


@private
@pytest.mark.xfail
def test_get_order_history(apikey, secret):
    '''test get_order_history'''

    btrx = Bittrex(apikey, secret)
    order_history = btrx.get_order_history()

    assert isinstance(order_history, list)
    assert sorted(order_history[0].keys()) == sorted(['Closed',
                                                      'Commission',
                                                      'Condition',
                                                      'ConditionTarget',
                                                      'Exchange',
                                                      'ImmediateOrCancel',
                                                      'IsConditional',
                                                      'Limit',
                                                      'OrderType',
                                                      'OrderUuid',
                                                      'Price',
                                                      'PricePerUnit',
                                                      'Quantity',
                                                      'QuantityRemaining',
                                                      'TimeStamp'])


@private
@pytest.mark.xfail
def test_get_withdrawal_history(apikey, secret):
    '''test get_withdrawal_history'''

    btrx = Bittrex(apikey, secret)
    withdrawal_history = btrx.get_withdrawal_history()

    assert isinstance(withdrawal_history, list)
    assert sorted(withdrawal_history[0].keys()) == sorted(['PaymentUuid',
                                                           'Currency',
                                                           'Amount',
                                                           'Address',
                                                           'Opened',
                                                           'Authorized',
                                                           'PendingPayment',
                                                           'TxCost',
                                                           'TxId',
                                                           'Canceled',
                                                           'InvalidAddress'])


@private
@pytest.mark.xfail
def test_get_deposit_history(apikey, secret):
    '''test get_withdrawal_history'''

    btrx = Bittrex(apikey, secret)
    deposit_history = btrx.get_deposit_history()

    assert isinstance(deposit_history, list)
    assert sorted(deposit_history[0].keys()) == sorted(['Id', 'Amount',
                                                        'Currency',
                                                        'Confirmations',
                                                        'LastUpdated',
                                                        'TxId',
                                                        'CryptoAddress'])

