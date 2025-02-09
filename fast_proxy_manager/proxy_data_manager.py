from random import choice
from pathlib import Path
from file_ops import read_msgpack, write_msgpack
from json import JSONDecodeError
from typing import Optional, List, Union, Dict
from utils import ProxyDict, NoProxyAvailable, URL
from icecream import ic


def _validate_protocol(protocols: list[str] | str | None) -> list[str] | None:
    if protocols is None:
        return None
    if isinstance(protocols, str):
        protocols = [protocols]
    if any(protocol not in ("http", "https", "socks4", "socks5") for protocol in protocols):
        invalid_protocol = next(p for p in protocols if p not in ("http", "https", "socks4", "socks5"))
        raise ValueError(f"You can't use this protocol: {invalid_protocol}")
    return protocols


class ProxyDataManager:
    def __init__(self, msgpack: Optional[Path] = Path("proxy_data"),
                 allowed_fails_in_row: int = 2,
                 fails_without_check: int = 2,
                 percent_failed_to_remove: float = 0.5,
                 min_proxies: int = 0,
                 debug: bool = False):
        """
        Get add and remove proxies from a list with some extra features.

        :param msgpack: Highly recommended to use it.
        Path to a store file with proxy data. If set to None, it will not store data in a file.
        :param allowed_fails_in_row: How many times a proxy can fail in a row before being removed.
        :param fails_without_check: How many times a proxy can fail before being checked for percentage of fails to remove.
        :param percent_failed_to_remove: Percentage of fails to remove a proxy.
        Example: 0.5 means 50% of tries are fails, if higher than that it gets removed.
        :param min_proxies: When len(proxies) < min_proxies, fetch more proxies
        """

        self.allowed_fails_in_row = allowed_fails_in_row
        self.fails_without_check = fails_without_check
        self.percent_failed_to_remove = percent_failed_to_remove
        self.min_proxies = min_proxies

        self.debug = debug

        self.msgpack = msgpack if msgpack else None
        self.proxies = self._load_proxies()
        self.last_proxy_index = None

    def _load_proxies(self) -> list[dict]:
        if self.msgpack and self.msgpack.exists() and self.msgpack.stat().st_size > 0:
            try:
                return read_msgpack(self.msgpack)
            except JSONDecodeError:
                return []
        self.msgpack and self.msgpack.touch(exist_ok=True)
        return []

    def _write_data(self):
        self.msgpack and write_msgpack(self.msgpack, self.proxies)

    def _rm_duplicate_proxies(self):
        seen_urls = set()
        self.proxies = [
            proxy for proxy in reversed(self.proxies)
            if not (proxy['url'] in seen_urls or seen_urls.add(proxy['url']))
        ]

    def update_data(self, remove_duplicates: bool = True):
        if remove_duplicates:
            self._rm_duplicate_proxies()
        self._write_data()

    def force_rm_last_proxy(self):
        if self.last_proxy_index is not None:
            self.rm_proxy(self.last_proxy_index)

    def feedback_proxy(self, success: bool):
        if self.last_proxy_index is None or self.last_proxy_index >= len(self.proxies):
            return

        proxy = self.proxies[self.last_proxy_index]
        if success:
            proxy["times_succeed"] = proxy.get("times_succeed", 0) + 1
            proxy["times_failed_in_row"] = 0
        else:
            proxy["times_failed"] = proxy.get("times_failed", 0) + 1
            proxy["times_failed_in_row"] = proxy.get("times_failed_in_row", 0) + 1

            total_attempts = proxy.get("times_failed", 0) + proxy.get("times_succeed", 0)
            failed_ratio = proxy.get("times_failed", 0) / total_attempts if total_attempts > 0 else 0

            should_remove = any([
                proxy.get("times_failed_in_row", 0) > self.allowed_fails_in_row,
                proxy.get("times_failed", 0) > self.fails_without_check and failed_ratio > self.percent_failed_to_remove
            ])

            if should_remove:
                if self.debug:
                    print(f"Removing proxy {proxy['url']} due to "
                          f"{'too many failures in a row' if proxy.get('times_failed_in_row', 0) > self.allowed_fails_in_row else 'bad success-failure ratio'}. "
                          f"f:{proxy.get('times_failed', 0)} s:{proxy.get('times_succeed', 0)} "
                          f"f_in_row:{proxy.get('times_failed_in_row', 0)}")
                self.rm_proxy(self.last_proxy_index)
        self._write_data()

    def add_proxy(self, proxies: List[ProxyDict]):
        new_proxies = [
            {**proxy, "times_failed": 0, "times_succeed": 0, "times_failed_in_row": 0}
            for proxy in proxies
        ]
        self.proxies.extend(new_proxies)
        self.update_data(remove_duplicates=True)

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

    def get_proxy(self, return_type: str = "url", protocol: Union[list[str], str, None] = None,
                  country: Union[list[str], str, None] = None,
                  anonymity: Union[list[str], str, None] = None,
                  exclude_protocol: Union[list[str], str, None] = None,
                  exclude_country: Union[list[str], str, None] = None,
                  exclude_anonymity: Union[list[str], str, None] = None) -> URL | None:

        if self.min_proxies and len(self.proxies) < self.min_proxies:
            raise NoProxyAvailable("Not enough proxies available. Fetch more proxies.")

        protocol = [protocol] if isinstance(protocol, str) else protocol
        country = [country] if isinstance(country, str) else country
        anonymity = [anonymity] if isinstance(anonymity, str) else anonymity
        exclude_protocol = [exclude_protocol] if isinstance(exclude_protocol, str) else exclude_protocol
        exclude_country = [exclude_country] if isinstance(exclude_country, str) else exclude_country
        exclude_anonymity = [exclude_anonymity] if isinstance(exclude_anonymity, str) else exclude_anonymity

        filtered_proxies = [
            proxy for proxy in self.proxies
            if (not protocol or proxy["protocol"] in protocol) and
               (not country or proxy["country"] in country) and
               (not anonymity or proxy["anonymity"] in anonymity) and
               (not exclude_protocol or proxy["protocol"] not in exclude_protocol) and
               (not exclude_country or proxy["country"] not in exclude_country) and
               (not exclude_anonymity or proxy["anonymity"] not in exclude_anonymity)
        ]

        if not filtered_proxies:
            raise NoProxyAvailable("No proxy found with the given parameters.")

        selected_proxy = choice(filtered_proxies)
        self.last_proxy_index = self.proxies.index(selected_proxy)
        return selected_proxy[return_type]

    def __len__(self):
        return len(self.proxies)


if __name__ == '__main__':
    manager = ProxyDataManager(debug=True)
    manager.rm_all_proxies()

    proxy = [
        {"url": "http://172.67.133.23:80", "protocol": "http", "country": "US", "anonymity": "elite"},
        {"url": "http://122.67.133.23:80", "protocol": "http", "country": "US", "anonymity": "elite"}
    ]

    manager.add_proxy(proxy)
    ic(len(manager))

    manager.get_proxy(protocol="http", country="US", anonymity="elite")
    [manager.feedback_proxy(success=False) for _ in range(2)]

    ic(len(manager))
    manager.feedback_proxy(success=False)
    ic(len(manager))
    ic(manager.get_proxy(protocol="http", country="US", anonymity="elite"))
