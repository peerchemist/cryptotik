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

        self.assertIsInstance(OKcoin.get_market_ticker("usd-btc"), dict)

    def test_get_market_orders(self):
        '''test getting the market orders'''

        self.assertIsInstance(OKcoin.get_market_order_book("usd-btc"), dict)

    def test_get_market_depth(self):
        '''test getting the market depth'''

        self.assertIsInstance(OKcoin.get_market_depth("usd-ltc"), dict)

    def test_get_market_spread(self):
        '''test get market spread'''

        self.assertIsInstance(OKcoin.get_market_spread("usd-btc"), Decimal)

    def test_get_market_trade_history(self):
        '''test getting the market history'''

        self.assertIsInstance(OKcoin.get_market_trade_history("usd-ltc"), list)

if __name__ == '__main__':
    unittest.main()

