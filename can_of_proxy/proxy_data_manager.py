from random import choice
from pathlib import Path
from utils import read_json, write_json, IP
from json import JSONDecodeError


def _validate_protocol(protocol: str | None) -> str | None:
    if protocol is not None and protocol not in ("http", "https", "socks4", "socks5"):
        raise ValueError("Invalid protocol used to create ProxyDataManager")
    return protocol


class ProxyDataManager:
    def __init__(self, json_file: Path | None = None, preferred_protocol: str | None = None,
                 preferred_country: str | None = None,
                 preferred_anonymity: str | None = None, allowed_fails_in_row: int = 3, fails_without_check: int = 2,
                 dont_store_data: bool = False, percent_failed_to_remove: float = 0.5):
        self.dont_store_data = dont_store_data
        self.allowed_fails_in_row = allowed_fails_in_row
        self.fails_without_check = fails_without_check
        self.percent_failed_to_remove = percent_failed_to_remove
        self.preferred_protocol = _validate_protocol(preferred_protocol)
        self.preferred_country = preferred_country
        self.preferred_anonymity = preferred_anonymity
        self.json_file = Path(json_file) if json_file else Path("proxies.json")
        self.proxies = self._load_proxies()
        self.last_proxy_index = None

    def _load_proxies(self):
        if not self.dont_store_data:
            if self.json_file.exists() and self.json_file.stat().st_size > 0:
                try:
                    return read_json(self.json_file)
                except JSONDecodeError:
                    return []
            self.json_file.touch(exist_ok=True)
        return []

    def _write_data(self):
        if not self.dont_store_data:
            write_json(self.json_file, self.proxies)

    def _rm_duplicate_proxies(self):
        """
        Remove duplicate proxies from the list which have the same URL,
        prefers to keep the one with the most data.
        """
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

    def update_data(self, remove_duplicates: bool = True):
        if remove_duplicates:
            self._rm_duplicate_proxies()
        self._write_data()

    def force_rm_last_proxy(self):
        """
        LAST USED PROXY WILL BE REMOVED! Good for sorting out all the bad proxies.

        Check len(manager) before and after to see if it worked.
        If no proxy left, you should try other sources for proxy.
        """
        if self.last_proxy_index is not None:
            self.rm_proxy(self.last_proxy_index)

    def feedback_proxy(self, success: bool):
        if self.last_proxy_index is None or self.last_proxy_index >= len(self.proxies):
            return

        proxy = self.proxies[self.last_proxy_index]
        if success:
            proxy["times_succeed"] += 1
            proxy["times_failed_in_row"] = 0
        else:
            proxy["times_failed"] += 1
            proxy["times_failed_in_row"] += 1
            if proxy["times_failed_in_row"] > self.allowed_fails_in_row or \
                    proxy["times_failed"] > self.fails_without_check and \
                    proxy["times_failed"] / (
                    proxy["times_failed"] + proxy["times_succeed"]) > self.percent_failed_to_remove:
                self.rm_proxy(self.last_proxy_index)
        self._write_data()

    def add_proxy(self, proxy: IP, country: str | None = None, anonymity: str | int | None = None):
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

    def rm_proxy(self, index: int):
        if 0 <= index < len(self.proxies):
            self.proxies.pop(index)
            if self.last_proxy_index is not None and index < self.last_proxy_index:
                self.last_proxy_index -= 1
            self._write_data()
        else:
            raise IndexError("Proxy does not exist")

    def rm_all_proxies(self):
        self.proxies = []
        self._write_data()

    def get_random_proxy(self, return_type: str = "url") -> str | None:
        if len(self.proxies) == 1:
            self.last_proxy_index = 0
            return self.proxies[0][return_type]

        preferred_proxies = [
            proxy for proxy in self.proxies
            if (not self.preferred_protocol or proxy["protocol"] == self.preferred_protocol) and
               (not self.preferred_country or proxy["country"] == self.preferred_country) and
               (not self.preferred_anonymity or proxy["anonymity"] == self.preferred_anonymity)
        ]

        if not preferred_proxies:
            return None

        if len(preferred_proxies) > 1 and self.last_proxy_index is not None:
            preferred_proxies = [
                proxy for proxy in preferred_proxies
                if self.proxies.index(proxy) != self.last_proxy_index
            ]

        selected_proxy = choice(preferred_proxies)
        self.last_proxy_index = self.proxies.index(selected_proxy)
        return selected_proxy[return_type]

    def __len__(self):
        return len(self.proxies)
