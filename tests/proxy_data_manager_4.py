import unittest
from pathlib import Path
from yarl import URL

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'can_of_proxy'))

from can_of_proxy.proxy_data_manager import ProxyDataManager


class TestProxyDataManager(unittest.TestCase):
    def setUp(self):
        self.test_file = Path("test.msgpack")
        self.manager = ProxyDataManager(self.test_file)
        self.manager.add_proxy(URL("http://192.168.0.1:8080"))
        self.manager.add_proxy(URL("http://192.168.0.2:8080"))
        self.manager.add_proxy(URL("http://192.168.0.3:8080"))
        self.n = 0

    def tearDown(self):
        if self.test_file.exists():
            self.test_file.unlink()

    def test_rm_proxy(self):
        initial_count = len(self.manager.proxies)
        self.manager.rm_proxy(1)  # Remove the second proxy
        self.assertEqual(len(self.manager.proxies), initial_count - 1)
        self.assertNotIn("http://192.168.0.2:8080", [p["url"] for p in self.manager.proxies])
        self.assertIn("http://192.168.0.1:8080", [p["url"] for p in self.manager.proxies])
        self.assertIn("http://192.168.0.3:8080", [p["url"] for p in self.manager.proxies])

    def test_feedback_proxy_remove_on_failure(self):
        self.manager.rm_all_proxies()
        self.assertEqual(len(self.manager.proxies), 0)
        self.manager.add_proxy(URL("http://123.123.123.123:8080"))
        self.assertEqual(self.manager.proxies[0]["times_failed_in_row"], 0)

        self.manager.get_proxy()  # Get the first proxy
        self.manager.feedback_proxy(False)  # Fail the first proxy
        self.assertEqual(self.manager.proxies[0]["times_failed_in_row"], 1)
        self.assertEqual(len(self.manager.proxies), 1)

        self.manager.get_proxy()  # Get the second proxy
        self.manager.feedback_proxy(False)  # Fail the second proxy
        self.assertEqual(self.manager.proxies[0]["times_failed_in_row"], 2)
        self.assertEqual(len(self.manager.proxies), 1)

        self.manager.get_proxy()  # Get the third proxy
        self.manager.feedback_proxy(False)  # Fail the third proxy
        self.assertEqual(len(self.manager.proxies), 0)

    def test_feedback_proxy_remove_on_failure_2(self):
        self.manager.rm_all_proxies()
        self.assertEqual(len(self.manager.proxies), 0)
        self.manager.add_proxy(URL("http://123.123.123.123:8080"))
        self.manager.proxies[0]["times_succeed"] = 100
        self.manager.proxies[0]["times_failed"] = 5

        self.manager.get_proxy()
        self.manager.feedback_proxy(False)
        self.assertEqual(len(self.manager.proxies), 1)

        self.manager.get_proxy()
        self.manager.feedback_proxy(False)
        self.assertEqual(len(self.manager.proxies), 1)

        self.manager.get_proxy()
        self.manager.feedback_proxy(True)
        self.assertEqual(len(self.manager.proxies), 1)

        self.manager.get_proxy()
        self.manager.feedback_proxy(False)
        self.assertEqual(len(self.manager.proxies), 1)

        self.manager.get_proxy()
        self.manager.feedback_proxy(False)
        self.assertEqual(len(self.manager.proxies), 1)

    def test_feedback_proxy_remove_on_failure_3(self):
        self.manager.rm_all_proxies()
        self.assertEqual(len(self.manager.proxies), 0)
        self.manager.add_proxy(URL("http://123.123.123.123:8080"))
        self.manager.proxies[0]["times_succeed"] = 0
        self.manager.proxies[0]["times_failed"] = 100
        self.assertEqual(len(self.manager.proxies), 1)

        self.manager.get_proxy()
        self.manager.feedback_proxy(False)
        self.assertEqual(len(self.manager.proxies), 0)

    def test_feedback_proxy_remove_on_failure_4(self):
        self.manager.rm_all_proxies()
        self.manager.allowed_fails_in_row = 9999
        self.assertEqual(len(self.manager.proxies), 0)
        self.manager.add_proxy(URL("http://123.123.123.123:8080"))
        self.manager.add_proxy(URL("http://123.123.123.111:8080"))
        self.assertEqual(len(self.manager.proxies), 2)

        self.manager.proxies[0]["times_succeed"] = 0
        self.manager.proxies[0]["times_failed"] = 100

        wrong_proxy = "http://123.123.123.111:8080"

        current = self.manager.get_proxy()
        while wrong_proxy == current:
            current = self.manager.get_proxy()

        self.assertEqual(len(self.manager.proxies), 2)
        self.manager.feedback_proxy(False)
        self.assertEqual(len(self.manager.proxies), 1)
        self.assertEqual(self.manager.proxies[0]["url"], wrong_proxy)

    def test_duplicated_proxy(self):
        self.manager.rm_all_proxies()
        self.manager.add_proxy(URL("http://123.123.123.123:8080"))
        self.manager.add_proxy(URL("http://123.123.123.123:8080"))
        self.assertEqual(len(self.manager.proxies), 2)

        self.manager.proxies[0]["times_succeed"] = 10
        self.manager.proxies[0]["times_failed"] = 5

        self.manager.update_data(remove_duplicates=True)

        self.assertEqual(len(self.manager.proxies), 1)

        self.assertEqual(self.manager.proxies[0]["times_succeed"], 10)

        self.n += 1

        if self.n < 50:
            self.test_duplicated_proxy()



if __name__ == "__main__":
    unittest.main()
