from multiprocessing.util import debug

import pandas as pd
from random import choice
from pathlib import Path
from file_ops import read_msgpack, write_msgpack
from json import JSONDecodeError
from typing import Optional, List, Union
from utils import ProxyDict, NoProxyAvailable, URL
from icecream import ic


def _validate_protocol(protocols: list[str] | str | None) -> list[str] | None:
    if protocols is None:
        return None
    if isinstance(protocols, str):
        protocols = [protocols]
    for protocol in protocols:
        if protocol not in ("http", "https", "socks4", "socks5"):
            raise ValueError(f"You can't use this protocol: {protocol}")
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

    def _load_proxies(self):
        columns = ["url", "protocol", "country", "anonymity", "times_failed", "times_succeed", "times_failed_in_row"]
        if self.msgpack:
            if self.msgpack.exists() and self.msgpack.stat().st_size > 0:
                try:
                    proxies = read_msgpack(self.msgpack)
                    return pd.DataFrame(proxies, columns=columns)
                except JSONDecodeError:
                    return pd.DataFrame(columns=columns)
            self.msgpack.touch(exist_ok=True)
        return pd.DataFrame(columns=columns)

    def _write_data(self):
        if self.msgpack:
            write_msgpack(self.msgpack, self.proxies.to_dict(orient="records"))

    def _rm_duplicate_proxies(self):
        self.proxies.drop_duplicates(subset="url", keep="last", inplace=True)

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

        proxy = self.proxies.iloc[self.last_proxy_index]
        if success:
            self.proxies.at[self.last_proxy_index, "times_succeed"] += 1
            self.proxies.at[self.last_proxy_index, "times_failed_in_row"] = 0
        else:
            self.proxies.at[self.last_proxy_index, "times_failed"] += 1
            self.proxies.at[self.last_proxy_index, "times_failed_in_row"] += 1
            if self.proxies.at[self.last_proxy_index, "times_failed_in_row"] > self.allowed_fails_in_row:
                if self.debug:
                    print(
                        f"Removing proxy {proxy['url']} due to too many failures in a row. f:{self.proxies.at[self.last_proxy_index, "times_failed"]} s:{self.proxies.at[self.last_proxy_index, "times_succeed"]} f_in_row:{self.proxies.at[self.last_proxy_index, "times_failed_in_row"]}")
                self.rm_proxy(self.last_proxy_index)
            elif (self.proxies.at[self.last_proxy_index, "times_failed"] > self.fails_without_check and
                  self.proxies.at[self.last_proxy_index, "times_failed"] /
                  (self.proxies.at[self.last_proxy_index, "times_failed"] + self.proxies.at[
                      self.last_proxy_index, "times_succeed"]) > self.percent_failed_to_remove):
                if self.debug:
                    print(
                        f"Removing proxy {proxy['url']} due to bad success-failure ratio. f:{self.proxies.at[self.last_proxy_index, "times_failed"]} s:{self.proxies.at[self.last_proxy_index, "times_succeed"]} f_in_row:{self.proxies.at[self.last_proxy_index, "times_failed_in_row"]}")
                self.rm_proxy(self.last_proxy_index)
        self._write_data()

    def add_proxy(self, proxies: List[ProxyDict]):
        new_proxies = pd.DataFrame(proxies)
        new_proxies = new_proxies.reindex(columns=self.proxies.columns, fill_value=0)
        self.proxies = pd.concat([self.proxies, new_proxies], ignore_index=True)
        self.update_data(remove_duplicates=True)

    def rm_proxy(self, index: int):
        if 0 <= index < len(self.proxies):
            self.proxies.drop(index, inplace=True)
            self.proxies.reset_index(drop=True, inplace=True)
            if self.last_proxy_index is not None and index < self.last_proxy_index:
                self.last_proxy_index -= 1
            self._write_data()
        else:
            raise IndexError("Proxy does not exist")

    def rm_all_proxies(self):
        self.proxies = pd.DataFrame(
            columns=["url", "protocol", "country", "anonymity", "times_failed", "times_succeed", "times_failed_in_row"])
        self._write_data()

    def get_proxy(self, return_type: str = "url", protocol: Union[list[str], str, None] = None,
                  country: Union[list[str], str, None] = None,
                  anonymity: Union[list[str], str, None] = None,
                  exclude_protocol: Union[list[str], str, None] = None,
                  exclude_country: Union[list[str], str, None] = None,
                  exclude_anonymity: Union[list[str], str, None] = None) -> URL | None:
        if self.min_proxies and len(self.proxies) < self.min_proxies:
            raise NoProxyAvailable("Not enough proxies available. Fetch more proxies.")

        query = []
        if protocol:
            protocol = _validate_protocol(protocol)
            if isinstance(protocol, str):
                protocol = [protocol]
            query.append(self.proxies["protocol"].isin(protocol))
        if country:
            if isinstance(country, str):
                country = [country]
            query.append(self.proxies["country"].isin(country))
        if anonymity:
            if isinstance(anonymity, str):
                anonymity = [anonymity]
            query.append(self.proxies["anonymity"].isin(anonymity))
        if exclude_protocol:
            exclude_protocol = _validate_protocol(exclude_protocol)
            if isinstance(exclude_protocol, str):
                exclude_protocol = [exclude_protocol]
            query.append(~self.proxies["protocol"].isin(exclude_protocol))
        if exclude_country:
            if isinstance(exclude_country, str):
                exclude_country = [exclude_country]
            query.append(~self.proxies["country"].isin(exclude_country))
        if exclude_anonymity:
            if isinstance(exclude_anonymity, str):
                exclude_anonymity = [exclude_anonymity]
            query.append(~self.proxies["anonymity"].isin(exclude_anonymity))

        if query:
            filtered_proxies = self.proxies.loc[pd.concat(query, axis=1).all(axis=1)]
        else:
            filtered_proxies = self.proxies

        if filtered_proxies.empty:
            raise NoProxyAvailable("No proxy found with the given parameters.")

        selected_proxy = filtered_proxies.sample(1).iloc[0]
        self.last_proxy_index = self.proxies.index[self.proxies["url"] == selected_proxy["url"]].tolist()[0]
        return selected_proxy[return_type]

    def __len__(self):
        return len(self.proxies)


if __name__ == '__main__':
    manager = ProxyDataManager(debug=True)
    manager.rm_all_proxies()
    # Add a proxy
    proxy = [{
        "url": "http://172.67.133.23:80",
        "protocol": "http",
        "country": "US",
        "anonymity": "elite"
    },
        {
            "url": "http://122.67.133.23:80",
            "protocol": "http",
            "country": "US",
            "anonymity": "elite"
        }]
    manager.add_proxy(proxy)
    ic(len(manager))

    # Simulate a success
    manager.get_proxy(protocol="http", country="US", anonymity="elite")

    manager.feedback_proxy(success=False)
    manager.feedback_proxy(success=False)

    ic(len(manager))
    manager.feedback_proxy(success=False)
    ic(len(manager))
    ic(manager.get_proxy(protocol="http", country="US", anonymity="elite"))
