import unittest
import fast_proxy_manager


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.can = fast_proxy_manager.Manager(data_file=None, fetching_method=[fast_proxy_manager.Fetch.proxifly()])

    def fetch(self):
        self.can.fetch_proxies()


if __name__ == '__main__':
    unittest.main()
