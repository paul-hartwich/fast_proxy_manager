import unittest
from pathlib import Path
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'can_of_proxy'))

from can_of_proxy.proxy_data_manager import ProxyDataManager
from can_of_proxy.utils.file_ops import read_msgpack, write_msgpack
from yarl import URL
import random


def _get_proxy_data():
    random_port = random.randint(1, 65535)
    return {
        "protocol": "http",
        "ip": "123.123.123.123",
        "port": random_port,
        "url": f"http://123.123.123.123:{random_port}",
        "country": None,
        "anonymity": None,
        "times_failed": 0,
        "times_succeed": 0,
        "times_failed_in_row": 0
    }


def _get_test_file_data():
    data = []
    for i in range(10000):
        data.append(_get_proxy_data())
    return data


class TestProxyDataManager(unittest.TestCase):
    def setUp(self):
        self.test_file = Path("test.json")
        self.manager = ProxyDataManager(json_file=self.test_file)
        data = _get_test_file_data()
        for d in data:
            self.manager.add_proxy(URL(d["url"]))
        self.manager.update_data(remove_duplicates=False)
        print(len(self.manager.proxies))  # This should print 10000

    def test_add_proxy(self):
        initial_count = len(self.manager.proxies)
        self.manager.add_proxy(URL("http://192.168.0.4:8080"))
        self.assertEqual(len(self.manager.proxies), 1001)
        self.assertEqual(self.manager.proxies[-1]["ip"], "192.168.0.4")

    def test_rm_all_proxies(self):
        self.manager.rm_all_proxies()
        self.assertEqual(len(self.manager.proxies), 0)

    def test_rm_proxy(self):
        self.manager.rm_proxy(1)
        self.assertEqual(len(self.manager.proxies), 999)
        self.assertEqual(self.manager.proxies[1]["ip"], "192.168.0.3")

    def test_get_proxy(self):
        proxy = self.manager.get_proxy()
        self.assertIn(proxy, [p["url"] for p in self.manager.proxies])

    def test_rm_duplicate_proxies(self):
        self.manager.add_proxy(URL("http://192.168.0.1:8080"))
        self.manager.update_data(remove_duplicates=True)
        self.assertEqual(len(self.manager.proxies), 3)

    def test_feedback_proxy_remove_on_failure(self):
        self.manager.get_proxy()
        for _ in range(self.manager.allowed_fails_in_row + 1):
            self.manager.feedback_proxy(False)
        self.assertEqual(len(self.manager.proxies), 2)

    def test_feedback_proxy_remove_on_high_failure_rate(self):
        self.manager.get_proxy()
        for _ in range(self.manager.fails_without_check + 1):
            self.manager.feedback_proxy(False)
        self.assertEqual(len(self.manager.proxies), 2)

    def test_get_proxy_empty_list(self):
        self.manager.rm_all_proxies()
        proxy = self.manager.get_proxy()
        self.assertIsNone(proxy)

    def test_feedback_proxy_no_proxies(self):
        self.manager.rm_all_proxies()
        self.manager.feedback_proxy(True)  # Should not raise an error

    def test_feedback_proxy_invalid_index(self):
        self.manager.last_proxy_index = 10  # Invalid index
        self.manager.feedback_proxy(False)  # Should not raise an error

    def test_rm_proxy_invalid_index(self):
        with self.assertRaises(IndexError):
            self.manager.rm_proxy(10)  # Invalid index

    def test_feedback_proxy_success(self):
        self.manager.get_proxy()
        initial_index = self.manager.last_proxy_index
        self.manager.feedback_proxy(True)
        self.assertEqual(self.manager.proxies[initial_index]["times_succeed"], 1)
        self.assertEqual(self.manager.proxies[initial_index]["times_failed_in_row"], 0)

    def test_feedback_proxy_failure(self):
        self.manager.get_proxy()
        initial_index = self.manager.last_proxy_index
        self.manager.feedback_proxy(False)
        self.assertEqual(self.manager.proxies[initial_index]["times_failed"], 1)
        self.assertEqual(self.manager.proxies[initial_index]["times_failed_in_row"], 1)


if __name__ == "__main__":
    unittest.main()
