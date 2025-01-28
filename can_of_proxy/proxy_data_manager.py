from random import choice
from pathlib import Path
from utils import read_json, write_json, IP
from json import JSONDecodeError


def _validate_protocol(protocol: str) -> str:
    if protocol not in ("http", "https", "socks4", "socks5"):
        raise ValueError("Invalid protocol used to create ProxyDataManager")
    return protocol


class ProxyDataManager:
    def __init__(self, json_file: Path = True, preferred_protocol: str = "http", preferred_country: str = None,
                 preferred_anonymity: str = None, allowed_fails_in_row: int = 3, fails_without_check: int = 2):
        """Just there to add get and remove proxies in a special format with the option to json_file them in a file."""

        self.allowed_fails_in_row = allowed_fails_in_row
        self.fails_without_check = fails_without_check

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
        write_json(self.json_file, self.proxies)

    def feedback_proxy(self, success: bool):
        # Check if the proxy request was successful or not
        if success is True:
            # Increment the success count and reset the consecutive failure count
            self.proxies[self.last_proxy_index]["times_succeed"] += 1
            self.proxies[self.last_proxy_index]["times_failed_in_row"] = 0
        else:
            # Increment the failure count and the consecutive failure count
            self.proxies[self.last_proxy_index]["times_failed"] += 1
            self.proxies[self.last_proxy_index]["times_failed_in_row"] += 1
            # Check if the consecutive failure count exceeds the allowed limit
            if self.proxies[self.last_proxy_index]["times_failed_in_row"] > self.allowed_fails_in_row:
                # Remove the proxy if it has failed too many times consecutively
                self.rm_proxy(self.last_proxy_index + 1)
            # Check if the total failure count exceeds the allowed limit without a check
            elif self.proxies[self.last_proxy_index][
                "times_failed"] > self.fails_without_check:
                total = self.proxies[self.last_proxy_index]["times_failed"] + self.proxies[self.last_proxy_index][
                    "times_succeed"]
                # Remove the proxy if the failure rate is more than 50%
                if self.proxies[self.last_proxy_index]["times_failed"] / total > 0.5:
                    self.rm_proxy(self.last_proxy_index + 1)
        # Update the JSON file with the current state of proxies
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
            "times_failed_in_row": 0
        }
        self.proxies.append(proxy_data)

    def rm_duplicate_proxies(self):
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

    def get_random_proxy(self, return_type: str = "url") -> str | None:
        """Won't return the same proxy twice in a row, except when there is only one proxy. Will return None if there are None."""
        if len(self.proxies) == 1:
            self.last_proxy_index = 0
            return self.proxies[0][return_type]

        # check if there are any proxies left with the preferred protocol, country and anonymity
        preferred_proxies = [
            proxy for proxy in self.proxies
            if (not self.preferred_protocol or proxy["protocol"] == self.preferred_protocol) and
               (not self.preferred_country or proxy["country"] == self.preferred_country) and
               (not self.preferred_anonymity or proxy["anonymity"] == self.preferred_anonymity)
        ]

        if not preferred_proxies:
            return None

        selected_proxy = choice(preferred_proxies)
        self.last_proxy_index = self.proxies.index(selected_proxy)
        return selected_proxy[return_type]


if __name__ == '__main__':
    manager = ProxyDataManager(allowed_fails_in_row=3, fails_without_check=2)
    manager.add_proxy(IP(url="http://123.123.123.123:5020"))
    manager.rm_duplicate_proxies()
    manager.update_data()

    print(manager.get_random_proxy())
    manager.feedback_proxy(False)
