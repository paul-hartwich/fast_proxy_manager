import unittest
from pathlib import Path
import sys
import os
import random

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'can_of_proxy'))

from can_of_proxy.utils.file_ops import read_msgpack, write_msgpack


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
    """Get data like from proxy_data_manager"""
    data = []

    for i in range(10000):
        data.append(_get_proxy_data())

    return data


class TestProxyDataManager(unittest.TestCase):
    def setUp(self):
        self.test_file = Path("test.json")
        self.data = _get_test_file_data()
        self.populate_test_file()

    def tearDown(self):
        if self.test_file.exists():
            self.test_file.unlink()

    def populate_test_file(self):
        write_msgpack(self.test_file, self.data)

    def test_write_and_read_json(self):
        write_msgpack(self.test_file, self.data)

        read_data = read_msgpack(self.test_file)

        self.assertEqual(self.data, read_data)


if __name__ == '__main__':
    unittest.main()
