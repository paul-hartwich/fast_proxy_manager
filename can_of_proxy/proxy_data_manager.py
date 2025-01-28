from random import randint
from pathlib import Path
from utils import read_json, write_json, IP
from json import JSONDecodeError


def _validate_protocol(protocol: str) -> str:
    if protocol not in ("http", "https", "socks4", "socks5"):
        raise ValueError("Invalid protocol used to create ProxyDataManager")
    return protocol


class ProxyDataManager:
    def __init__(self, json_file: Path | bool = True, preferred_protocol: str = "http", preferred_country: str = None,
                 preferred_anonymity: str = None):
        """Just there to add get and remove proxies in a special format with the option to json_file them in a file."""

        self.preferred_protocol = _validate_protocol(preferred_protocol)
        self.preferred_country = preferred_country
        self.preferred_anonymity = preferred_anonymity

        self.json_file = json_file if isinstance(json_file, Path) else Path("proxies.json")
        self.proxies = self._load_proxies()
        self.last_proxy_index = None

    def _load_proxies(self):
        if self.json_file.exists() and self.json_file.stat().st_size > 0:
            try:
                return read_json(self.json_file)
            except JSONDecodeError:
                return []
        self.json_file.touch(exist_ok=True)
        return []

    def update_data(self):
        """Updates the storage file of the proxies and also cleans it up al little."""
        self._rm_duplicate_proxies()
        write_json(self.json_file, self.proxies)

    def feedback_proxy(self, success: bool):
        if success is True:
            self.proxies[self.last_proxy_index]["times_succeed"] += 1
        else:
            self.proxies[self.last_proxy_index]["times_failed"] += 1
            if self.proxies[self.last_proxy_index]["times_failed"] > 2:  # True if out of try-phase
                # check how high the percentage of fails there are
                total = self.proxies[self.last_proxy_index]["times_failed"] + self.proxies[self.last_proxy_index][
                    "times_succeed"]
                if self.proxies[self.last_proxy_index]["times_failed"] / total > 0.5:
                    self.rm_proxy(self.last_proxy_index + 1)
        write_json(self.json_file, self.proxies)

    def add_proxy(self, proxy: IP, country: str | None = None, anonymity: str | None = None):
        """Add a proxy to the list with the right format"""
        proxy_data = {
            "protocol": proxy.protocol,
            "ip": proxy.ip,
            "port": proxy.port,
            "url": proxy.url(),
            "country": country,
            "anonymity": anonymity,
            "times_failed": 0,
            "times_succeed": 0,
        }
        self.proxies.append(proxy_data)

    def _rm_duplicate_proxies(self):
        """Remove duplicate proxies from the list which have the same URL,
        keeping the one with the most data."""
        seen = {}
        for proxy in self.proxies:
            url = proxy['url']
            if url in seen:
                existing_proxy = seen[url]
                if (proxy['times_failed'] + proxy['times_succeed']) > (
                        existing_proxy['times_failed'] + existing_proxy['times_succeed']):
                    seen[url] = proxy
            else:
                seen[url] = proxy
        self.proxies = list(seen.values())

    def rm_proxy(self, number: int):
        try:
            self.proxies.pop(number - 1)
        except IndexError:
            raise IndexError("Proxy does not exist")
        if self.last_proxy_index is not None and number - 1 < self.last_proxy_index:
            self.last_proxy_index -= 1
        write_json(self.json_file, self.proxies)

    def rm_all_proxies(self):
        self.proxies = []
        write_json(self.json_file, self.proxies)

    def get_proxy(self, number: int):
        try:
            return self.proxies[number - 1]
        except IndexError:
            raise IndexError("Proxy does not exist")

    def get_random_proxy(self, return_type: str = "url") -> str:
        """Won't return the same proxy twice in a row, except when there is only one proxy."""
        if len(self.proxies) == 1:
            self.last_proxy_index = 0
            return self.proxies[0][return_type]

        new_index = self.last_proxy_index
        while new_index == self.last_proxy_index:
            new_index = randint(0, len(self.proxies) - 1)

        self.last_proxy_index = new_index
        return self.proxies[new_index][return_type]


if __name__ == '__main__':
    manager = ProxyDataManager()
    manager.add_proxy(IP(url="http://123.123.123.123:5050"))
    manager.update_data()

    print(manager.get_random_proxy())
    manager.feedback_proxy(False)
