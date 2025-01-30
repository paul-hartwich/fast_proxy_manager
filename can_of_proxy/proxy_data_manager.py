from random import choice
from pathlib import Path
from utils import read_msgpack, write_msgpack
from yarl import URL
from json import JSONDecodeError
from typing import Optional, List, Dict, TypedDict


class ProxyDict(TypedDict):
    """
    {"url": URL, "country": str, "anonymity": str}
    """
    url: URL
    country: str | None
    anonymity: str | None


class NoProxyAvailable(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"NoProxyAvailable: {self.message}"


def _validate_protocol(protocols: list[str] | str | None) -> list[str] | None:
    if protocols is None:
        return None
    if isinstance(protocols, str):
        protocols = [protocols]
    for protocol in protocols:
        if protocol not in ("http", "https", "socks4", "socks5"):
            raise ValueError("Invalid protocol used to create ProxyDataManager")
    return protocols


class ProxyDataManager:
    def __init__(self, msgpack: Optional[Path] = Path("proxies.json"),
                 allowed_fails_in_row: int = 3,
                 fails_without_check: int = 2,
                 percent_failed_to_remove: float = 0.5):
        """
        Get add and remove proxies from a list with some extra features.

        :param msgpack: Highly recommended to use it.
        Path to a store file with proxy data. If set to None, it will not store data in a file.
        :param allowed_fails_in_row: How many times a proxy can fail in a row before being removed.
        :param fails_without_check: How many times a proxy can fail before being checked for percentage of fails to remove.
        :param percent_failed_to_remove: Percentage of fails to remove a proxy.
        Example: 0.5 means 50% of tries are fails, if higher than that it gets removed.
        """

        self.allowed_fails_in_row = allowed_fails_in_row
        self.fails_without_check = fails_without_check
        self.percent_failed_to_remove = percent_failed_to_remove

        self.msgpack = msgpack if msgpack else None
        self.proxies = self._load_proxies()
        self.last_proxy_index = None

    def _load_proxies(self):
        if self.msgpack:
            if self.msgpack.exists() and self.msgpack.stat().st_size > 0:
                try:
                    return read_msgpack(self.msgpack)
                except JSONDecodeError:
                    return []
            self.msgpack.touch(exist_ok=True)
        return []

    def _write_data(self):
        if self.msgpack:
            write_msgpack(self.msgpack, self.proxies)

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
                    # Merge country and anonymity data if they are None in the existing proxy
                    if existing_proxy['country'] is None and proxy['country'] is not None:
                        existing_proxy['country'] = proxy['country']
                    if existing_proxy['anonymity'] is None and proxy['anonymity'] is not None:
                        existing_proxy['anonymity'] = proxy['anonymity']
                    seen[url] = proxy
                else:
                    # Merge country and anonymity data if they are None in the existing proxy
                    if existing_proxy['country'] is None and proxy['country'] is not None:
                        existing_proxy['country'] = proxy['country']
                    if existing_proxy['anonymity'] is None and proxy['anonymity'] is not None:
                        existing_proxy['anonymity'] = proxy['anonymity']
            else:
                seen[url] = proxy
        self.proxies = list(seen.values())

    def update_data(self, remove_duplicates: bool = True):
        """It has to be called after proxies got added. NOT REMOVED! (already handled)"""
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

    def add_proxy(self, proxies: URL | List[URL] | List[ProxyDict],
                  country: str | None = None, anonymity: str | None = None):
        """
        Add a proxy to the list.
        You can add a list of proxies at once, but all of them will have the same country and anonymity.
        If a list of dictionaries is used, other params will be ignored and the data will be used from the dictionary.
        """
        if isinstance(proxies, URL):
            proxy_data = {
                "protocol": proxies.scheme,
                "url": str(proxies),
                "country": country,
                "anonymity": anonymity,
                "times_failed": 0,
                "times_succeed": 0,
                "times_failed_in_row": 0
            }
            self.proxies.append(proxy_data)

        elif isinstance(proxies, list) and all(isinstance(proxy, URL) for proxy in proxies):
            for proxy in proxies:
                proxy_data = {
                    "protocol": proxy.scheme,
                    "url": str(proxy),
                    "country": country,
                    "anonymity": anonymity,
                    "times_failed": 0,
                    "times_succeed": 0,
                    "times_failed_in_row": 0
                }
                self.proxies.append(proxy_data)

        elif isinstance(proxies, list) and all(isinstance(proxy, dict) for proxy in proxies):
            for proxy in proxies:
                self.proxies.append({
                    "protocol": proxy["url"].scheme,
                    "url": str(proxy["url"]),
                    "country": proxy["country"],
                    "anonymity": proxy["anonymity"],
                    "times_failed": 0,
                    "times_succeed": 0,
                    "times_failed_in_row": 0
                })

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

    def get_proxy(self, return_type: str = "url", preferred_protocol: list[str] | str | None = None,
                  preferred_country: list[str] | str | None = None,
                  preferred_anonymity: list[str] | str | None = None) -> str | None:
        """Return a random proxy from the list. If no proxy is found, return None. Never returns the same proxy twice."""

        preferred_protocol = _validate_protocol(preferred_protocol)
        preferred_country = preferred_country if isinstance(preferred_country, list) else [preferred_country]
        preferred_anonymity = preferred_anonymity if isinstance(preferred_anonymity, list) else [
            preferred_anonymity]

        if len(self.proxies) == 1:
            self.last_proxy_index = 0
            return self.proxies[0][return_type]

        preferred_proxies = [
            proxy for proxy in self.proxies
            if (not preferred_protocol or proxy["protocol"] in preferred_protocol) and
               (not preferred_country or proxy["country"] in preferred_country) and
               (not preferred_anonymity or proxy["anonymity"] in preferred_anonymity)
        ]

        if not preferred_proxies:
            raise NoProxyAvailable("No proxy found with the given parameters.")

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
