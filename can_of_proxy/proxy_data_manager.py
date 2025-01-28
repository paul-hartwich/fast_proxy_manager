import random
from pathlib import Path
from utils import read_json, write_json

data_structure = [
    {
        "protocol": "protocol",
        "ip": "ip",
        "port": "port",
        "country": "country",  # can be any
        "anonymity": "anonymity",  # can be any
        "times_failed": 0,
        "times_tested": 0,
        "times_succeed": 0,
    }
]


def _validate_protocol(protocol: str):
    if protocol not in ["http", "https", "socks4", "socks5"]:
        raise ValueError("Invalid preferred protocol used for proxy data manager")
    return protocol


class ProxyDataManager:
    def __init__(self, store: Path | bool = True, preferred_protocol: str = "http"):
        """Just there to add get and remove proxies in a special format with the option to store them in a file."""
        self.preferred_protocol = _validate_protocol(preferred_protocol)
        self.json = JSONFile(store if isinstance(store, Path) else Path("proxies.json"))

    def _update_data(self):
        self.json.write(self.proxies)

    def add_proxy(self, ip: str | list, port, protocol: str, country: str, anonymity: str, url: str = None):
        """add a proxy to the list with the right format"""
        if url:
            proxy = {
                "ip": ip,
                "port": port,
                "https": False,
                "protocol": protocol,
                "country": country,  # can be any
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
