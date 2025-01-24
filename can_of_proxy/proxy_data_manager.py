import random
from pathlib import Path

from utils import read_json, write_json


class ProxyDataManager:
    def __init__(self, store: Path | False = False):
        """Just there to add get and remove proxies in a special format with the option to store them in a file."""
        self.store = store
        self.proxies = []

        self._validate_params()

    def _update_data(self):
        if self.store:
            write_json(self.store, self.proxies)

    def __len__(self):
        return len(self.proxies)

    def _validate_params(self):
        Path.mkdir(self.store, exist_ok=True)
        data = read_json(self.store)
        if data: self.proxies = data

    def add_proxy(self, ip: str | list, port, protocol: str, country: str, anonymity: str, url: str = None):
        """Use pure """
        if url:
            proxy = {
                "ip": ip,
                "port": port,
                "https": False,
                "protocol": protocol
            }

            self._update_data()

        def rm_duplicate_proxies(self):
            self.proxies = list(set(self.proxies))
            self._update_data()

        def rm_proxy(self, number: int):
            try:
                removed_proxy = self.proxies.pop(number - 1)
                print(f"Removed proxy: {removed_proxy}")
            except IndexError:
                raise IndexError("Proxy does not exist")
            self._update_data()

        def rm_all_proxies(self):
            self.proxies = []
            self._update_data()

        def get_proxy(self, number: int):
            try:
                return self.proxies[number - 1]
            except IndexError:
                raise IndexError("Proxy does not exist")

        def get_random_proxy(self):
            return random.choice(self.proxies)
