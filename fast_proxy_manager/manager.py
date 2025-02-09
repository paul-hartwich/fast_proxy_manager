from functools import partial
from typing import List, Union, Callable
from pathlib import Path

from data_manager import DataManager
from utils import ProxyDict
from test_proxies import get_valid_proxies
from logger import logger


class Manager:
    def __init__(self, fetching_method: List[Callable[[], List[ProxyDict]]],
                 data_file: Path | None = "proxy_data",
                 preferred_protocol: list[str] | str | None = None,
                 preferred_country: list[str] | str | None = None,
                 preferred_anonymity: list[str] | str | None = None,
                 allowed_fails_in_row: int = 3,
                 fails_without_check: int = 2,
                 percent_failed_to_remove: float = 0.5,
                 max_proxies: Union[int, False] = 10,
                 min_proxies: Union[int, False] = 1,
                 fetch_proxies_on_init: bool = True):
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
        :param fetch_proxies_on_init: Fetch proxies on initialization.
        HAS TO BE AWAITED!
        """
        self.fetch_proxies_on_init = fetch_proxies_on_init

        self.fetching_method = fetching_method
        self.max_proxies = max_proxies
        self.min_proxies = min_proxies

        if data_file is not None:
            self.data_file = Path(data_file)
        else:
            self.data_file = None

        self.preferred_protocol = preferred_protocol
        self.preferred_country = preferred_country
        self.preferred_anonymity = preferred_anonymity

        self.data_manager = DataManager(msgpack=self.data_file, allowed_fails_in_row=allowed_fails_in_row,
                                        fails_without_check=fails_without_check,
                                        percent_failed_to_remove=percent_failed_to_remove)

    async def _async_init(self):
        if len(self.data_manager) < self.min_proxies:
            await self.fetch_proxies()
            logger.debug(f"Finished fetching proxies on init")
        return self

    def __await__(self):
        return self._async_init().__await__()

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

        logger.debug(f"Fetched {len(all_proxies)} proxies")

        self.data_manager.add_proxy(all_proxies)
        if self.data_file is not None:
            self.data_manager.update_data()


if __name__ == '__main__':
    import asyncio
    from __init__ import Fetch


    async def main():
        proxy_url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"

        manager = await Manager(fetching_method=[partial(Fetch.custom, proxy_url)], max_proxies=10, min_proxies=11)
        print(len(manager.data_manager))


    asyncio.run(main())
