from functools import partial
from typing import List, Union, Callable
from data_manager import DataManager
from utils import ProxyDict
from pathlib import Path
from test_proxies import get_valid_proxies


class Manager:
    def __init__(self, fetching_method: List[Callable[[], List[ProxyDict]]],
                 data_file: Path | None = "proxy_data",
                 preferred_protocol: list[str] | str | None = None,
                 preferred_country: list[str] | str | None = None,
                 preferred_anonymity: list[str] | str | None = None,
                 allowed_fails_in_row: int = 3,
                 fails_without_check: int = 2,
                 percent_failed_to_remove: float = 0.5,
                 max_proxies: Union[int, False] = False,
                 min_proxies: Union[int, False] = False):
        """
        The main class to control pretty much everything.

        :param fetching_method: List of functions that return a list of ProxyDict.
        :param data_file: Path to a store file with proxy data.
        Highly recommended to use it.
        :param preferred_protocol: It can later be changed when getting a proxy.
        :param preferred_country: It can later be changed when getting a proxy.
        :param preferred_anonymity: It can later be changed when getting a proxy.
        :param allowed_fails_in_row: How many times a proxy can fail in a row before being removed.
        :param fails_without_check: How many times a proxy can fail before being checked for percentage of fails to remove.
        :param percent_failed_to_remove: Percentage of fails to remove a proxy.
        Example: 0.5 means 50% of tries are fails, if higher than that it gets removed.
        :param max_proxies: Maximum number of proxies to be fetched.
        Saves time when testing proxies.
        :param min_proxies: When len(proxies) < min_proxies, fetch more proxies.
        """
        self.fetching_method = fetching_method
        self.max_proxies = max_proxies
        self.min_proxies = min_proxies

        if data_file is not None:
            data_file = Path(data_file)

        self.preferred_protocol = preferred_protocol
        self.preferred_country = preferred_country
        self.preferred_anonymity = preferred_anonymity

        self.data_manager = DataManager(msgpack=data_file, allowed_fails_in_row=allowed_fails_in_row,
                                        fails_without_check=fails_without_check,
                                        percent_failed_to_remove=percent_failed_to_remove)

    async def fetch_proxies(self, test_proxies: bool = True,
                            fetching_method: List[Callable[[], List[ProxyDict]]] = None) -> None:
        """
        Fetch proxies from the internet.
        :param test_proxies: Test proxies before adding them.
        :param fetching_method: List of functions that return a list of ProxyDict.
        Change will be temp.
        """
        if fetching_method is None:
            fetching_method = self.fetching_method

        all_proxies = []
        for method in fetching_method:
            proxies = await method()
            all_proxies.extend(proxies)

        if test_proxies:
            all_proxies = await get_valid_proxies(all_proxies, max_working_proxies=self.max_proxies)

        self.data_manager.add_proxy(all_proxies)


if __name__ == '__main__':
    import asyncio
    from icecream import ic
    from __init__ import Fetch


    async def main():
        proxy_url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"

        manager = Manager(data_file=None, fetching_method=[partial(Fetch.custom, proxy_url)])
        await manager.fetch_proxies(test_proxies=False)
        ic(len(manager.data_manager))


    asyncio.run(main())
