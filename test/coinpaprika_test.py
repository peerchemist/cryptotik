import pytest
import time
from cryptotik.coinpaprika import CoinPaprika, CoinPaprikaNormalized

paprika = CoinPaprika()


def test_get_coins():

    assert isinstance(paprika.get_coins(), list)


def test_get_global():

    assert isinstance(paprika.get_global(), dict)


@pytest.mark.parametrize("coin_id", ["ppc-peercoin", "btc-bitcoin"])
def test_get_coin_by_id(coin_id):

    assert isinstance(paprika.get_coin_by_id(coin_id), dict)


@pytest.mark.parametrize("coin_id", ["ppc-peercoin", "btc-bitcoin"])
def test_get_coin_twitter(coin_id):

    assert isinstance(paprika.get_coin_twitter(coin_id), list)


@pytest.mark.parametrize("coin_id", ["ppc-peercoin", "btc-bitcoin"])
def test_get_coin_events(coin_id):

    assert isinstance(paprika.get_coin_events(coin_id), list)


@pytest.mark.parametrize("coin_id", ["ppc-peercoin", "btc-bitcoin"])
def test_get_coin_exchanges(coin_id):

    assert isinstance(paprika.get_coin_exchanges(coin_id), list)


@pytest.mark.parametrize("quote", ["KRW", "GBP", "CAD"])
def test_get_coin_exchanges(quote):

    assert isinstance(paprika.get_coin_markets("ppc-peercoin", quote), list)


@pytest.mark.parametrize("coin_id", ["ppc-peercoin", "btc-bitcoin"])
def test_get_coin_ohlcv(coin_id):

    assert isinstance(paprika.get_coin_ohlcv(coin_id, "USD"), list)


@pytest.mark.parametrize("coin_id", ["ppc-peercoin", "btc-bitcoin"])
def test_get_coin_ohlcv_data(coin_id, since=time.time() - 604800):

    assert isinstance(
        paprika.get_coin_ohlcv_data(
            coin_id=coin_id, quote="USD", since=int(since), limit=1
        ),
        list,
    )


@pytest.mark.parametrize("coin_id", ["ppc-peercoin", "btc-bitcoin"])
def test_get_normalized_market_ticker(coin_id):

    assert isinstance(CoinPaprikaNormalized().get_market_ohlcv_data_actual(coin_id, "BTC"), dict)


@pytest.mark.parametrize("coin_id", ["ppc-peercoin", "btc-bitcoin"])
def test_get_market_ohlcv_data(coin_id, since=time.time() - 604800):

    assert isinstance(
        CoinPaprikaNormalized().get_market_ohlcv_data(
            coin_id=coin_id, quote="btc", since=int(since), limit=1
        ),
        list,
    )
