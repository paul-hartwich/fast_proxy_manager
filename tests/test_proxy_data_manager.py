import unittest
from pathlib import Path
import sys

sys.path.append('C:/Users/pauln/PycharmProjects/can-of-proxy/can_of_proxy')

from can_of_proxy.proxy_data_manager import ProxyDataManager
from can_of_proxy.utils import read_json, write_json


class TestProxyDataManager(unittest.TestCase):
    def setUp(self):
        self.test_file = Path("test.json")
        self.manager = ProxyDataManager(store=self.test_file)
        print("Initial state:", self._read_file())

    def tearDown(self):
        if self.test_file.exists():
            self.test_file.unlink()

    def _read_file(self):
        if self.test_file.exists() and self.test_file.stat().st_size > 0:
            return read_json(self.test_file)
        return "File does not exist or is empty"

    def test_add_proxy(self):
        self.manager.add_proxy("192.168.0.1", 8080, "http", "US", "high")
        print("After adding proxy:", self._read_file())
        self.assertEqual(len(self.manager.proxies), 1)
        self.assertEqual(self.manager.proxies[0]["ip"], "192.168.0.1")

    def test_rm_proxy(self):
        self.manager.add_proxy("192.168.0.1", 8080, "http", "US", "high")
        self.manager.rm_proxy(1)
        print("After removing proxy:", self._read_file())
        self.assertEqual(len(self.manager.proxies), 0)

    def test_rm_all_proxies(self):
        self.manager.add_proxy("192.168.0.1", 8080, "http", "US", "high")
        self.manager.add_proxy("192.168.0.2", 8080, "http", "US", "high")
        self.manager.rm_all_proxies()
        print("After removing all proxies:", self._read_file())
        self.assertEqual(len(self.manager.proxies), 0)

    def test_get_proxy(self):
        self.manager.add_proxy("192.168.0.1", 8080, "http", "US", "high")
        proxy = self.manager.get_proxy(1)
        print("After getting proxy:", self._read_file())
        self.assertEqual(proxy["ip"], "192.168.0.1")

    def test_get_random_proxy(self):
        self.manager.add_proxy("192.168.0.1", 8080, "http", "US", "high")
        proxy = self.manager.get_random_proxy()
        print("After getting random proxy:", self._read_file())
        self.assertEqual(proxy["ip"], "192.168.0.1")

    def test_rm_duplicate_proxies(self):
        self.manager.add_proxy("192.168.0.1", 8080, "http", "US", "high")
        self.manager.add_proxy("192.168.0.1", 8080, "http", "US", "high")
        self.manager.rm_duplicate_proxies()
        print("After removing duplicate proxies:", self._read_file())
        self.assertEqual(len(self.manager.proxies), 1)


if __name__ == "__main__":
    unittest.main()
