import unittest
from cryptotik.okcoin import OKcoin
from decimal import Decimal

class OKcoinTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('''Starting OKcoin API wrapper test.''')

    def test_format_pair(self):
        '''test string formating to match API expectations'''

        self.assertEqual(OKcoin.format_pair("btc-usd"), "btc_usd")

    def test_get_market_ticker(self):
        '''tests get_market_ticker>'''

        self.assertIsInstance(OKcoin.get_market_ticker("btc-usd"), dict)
        self.assertIn("buy", OKcoin.get_market_ticker("btc-cny"))

    def test_get_market_order_book(self):
        '''test getting the market orders'''

        self.assertIsInstance(OKcoin.get_market_order_book("btc-usd"), dict)
        self.assertIn("asks", OKcoin.get_market_depth("ltc-cny"))

    def test_get_market_depth(self):
        '''test getting the market depth'''

        self.assertIsInstance(OKcoin.get_market_depth("ltc-usd"), dict)
        self.assertIn("asks", OKcoin.get_market_depth("ltc-cny"))

    def test_get_market_spread(self):
        '''test get market spread'''

        self.assertIsInstance(OKcoin.get_market_spread("btc-usd"), Decimal)

    def test_get_market_trade_history(self):
        '''test getting the market history'''

        self.assertIsInstance(OKcoin.get_market_trade_history("ltc-usd"), list)

    def test_get_futures_ticker(self):
        '''test getting the futures market ticker'''

        self.assertIsInstance(OKcoin.get_futures_market_ticker("btc-usd"), dict)
        self.assertIn("contract_id", OKcoin.get_futures_market_ticker("btc-usd"))

    def test_get_futures_market_order_book(self):
        '''test getting the future market orders'''

        self.assertIsInstance(OKcoin.get_futures_market_order_book("btc-usd"), dict)
        self.assertIn("asks", OKcoin.get_futures_market_order_book("ltc-cny",))

    def test_get_futures_market_depth(self):
        '''test getting the futures market depth'''

        self.assertIsInstance(OKcoin.get_futures_market_depth("ltc-usd"), dict)
        self.assertIn("asks", OKcoin.get_futures_market_depth("ltc-cny"))

    def test_futures_get_market_spread(self):
        '''test get futures market spread'''

        self.assertIsInstance(OKcoin.get_futures_market_spread("btc-usd"), Decimal)

    def test_get_futures_market_trade_history(self):
        '''test getting the futures market history'''

        self.assertIsInstance(OKcoin.get_futures_market_trade_history("ltc-usd"), list)

    def test_get_futures_market_index(self):
        '''test getting the futures index'''

        self.assertIsInstance(OKcoin.get_futures_market_index("btc-usd"), dict)

if __name__ == '__main__':
    unittest.main()

