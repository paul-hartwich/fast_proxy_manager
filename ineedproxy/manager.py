from typing import List, Union, Callable
from pathlib import Path
import aiohttp

from .data_manager import DataManager
from .utils import ProxyDict, ProxyPreferences, NoProxyAvailable
from .test_proxies import get_valid_proxies
from .logger import logger
from .get import get_request as _get_request


class Manager:
    def __init__(self, fetching_method: List[Callable[[], List[ProxyDict]]],
                 data_file: Path | None = "proxy_data",
                 proxy_preferences: ProxyPreferences = None,
                 force_preferences: bool = False,
                 auto_fetch_proxies: bool = True,
                 allowed_fails_in_row: int = 3,
                 fails_without_check: int = 2,
                 percent_failed_to_remove: float = 0.5,
                 max_proxies: Union[int, False] = 10,
                 min_proxies: Union[int, False] = 2,
                 simultaneous_proxy_requests: int = 300) -> None:
        """
        The main class to control pretty much everything.

        :param fetching_method: List of functions that return a list of ProxyDict.
        :param data_file: Path to a store file with proxy data.
        :param proxy_preferences: ProxyPreferences object to filter proxies.
        :param force_preferences: If True, will only return proxies that match the preferences.
        When no proxies are available, it will fetch more (potential loop).
        If False and no proxies are available,
        it will fetch more, and when no proxies are available again, it ignores the preferences.
        :param auto_fetch_proxies: If True, it will fetch when too few proxies are available.Has to be awaited (also on int).
        :param allowed_fails_in_row: How many times a proxy can fail in a row before being removed.
        :param fails_without_check: How many times a proxy can fail before being checked for percentage of fails to remove.
        :param percent_failed_to_remove: Percentage of fails to remove a proxy.
        Example: 0.5 means 50% of tries are fails, if higher than that it gets removed.
        :param max_proxies: Maximum number of proxies to be fetched.
        Saves time when testing proxies.
        :param min_proxies: When len(proxies) < min_proxies, fetch more proxies.
        :param simultaneous_proxy_requests: Number of simultaneous requests to test proxies.
        """
        self.simultaneous_proxy_requests = simultaneous_proxy_requests
        self.auto_fetch_proxies = auto_fetch_proxies

        self.fetching_method = fetching_method
        self.max_proxies = max_proxies
        self.min_proxies = min_proxies

        if proxy_preferences is None:
            self.proxy_preferences = ProxyPreferences()
        else:
            self.proxy_preferences = proxy_preferences
        self.force_preferences = force_preferences

        self.failed_get_proxies_in_row: int = 0

        self.data_manager = DataManager(msgpack=data_file,
                                        allowed_fails_in_row=allowed_fails_in_row,
                                        fails_without_check=fails_without_check,
                                        percent_failed_to_remove=percent_failed_to_remove,
                                        min_proxies=min_proxies)

    async def _async_init(self):
        if len(self.data_manager) < self.min_proxies and self.auto_fetch_proxies:
            await self.fetch_proxies()
            logger.debug("Finished fetching proxies on init")
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
            all_proxies = await get_valid_proxies(all_proxies, max_working_proxies=self.max_proxies,
                                                  simultaneous_proxy_requests=self.simultaneous_proxy_requests)

        logger.debug("Fetched %d proxies", len(all_proxies))

        self.data_manager.add_proxy(all_proxies, remove_duplicates=True if len(fetching_method) > 1 else False)

    async def get_proxy(self, ignore_preferences=False, **preferences_kwargs) -> str:
        """Returns a proxy from the data manager."""
        if not ignore_preferences:
            try:
                proxy = self.data_manager.get_proxy(**preferences_kwargs)
                self.failed_get_proxies_in_row = 0
                return proxy
            except NoProxyAvailable:
                self.failed_get_proxies_in_row += 1
                return await self._handle_no_proxy_available(preferences_kwargs)
        else:
            return self.data_manager.get_proxy()

    async def _handle_no_proxy_available(self, preferences_kwargs):
        """Helper method to handle NoProxyAvailable exceptions."""
        if not self.auto_fetch_proxies:
            raise NoProxyAvailable("No proxy available")

        if self.force_preferences:
            logger.debug("No proxy available, fetching more proxies")
            await self.fetch_proxies()
            return await self.get_proxy(ignore_preferences=False, **preferences_kwargs)

        if self.failed_get_proxies_in_row == 1:
            logger.debug("Failed with preferences. Trying without preferences.")
            return await self.get_proxy(ignore_preferences=True)
        if self.failed_get_proxies_in_row == 2:
            logger.debug("Failed without preferences. Fetching more proxies.")
            await self.fetch_proxies()
            return await self.get_proxy(ignore_preferences=True)

        logger.critical("Failed to get proxy %d times in a row.",
                        self.failed_get_proxies_in_row)
        await self.fetch_proxies()
        return await self.get_proxy(ignore_preferences=True)

    def feedback_proxy(self, success: bool) -> None:
        """Just feedback to the DataManager if the last proxy was successful or not."""
        logger.debug("Feedback: Proxy %s was %s.", self.data_manager.proxies[self.data_manager.last_proxy_index]["url"],
                     "successful" if success else "unsuccessful")
        self.data_manager.feedback_proxy(success)

    async def get_request(self, url: str, timeout: int = 10,
                          session: aiohttp.ClientSession = None) -> aiohttp.ClientResponse | None:
        """
        Sends a GET request using a proxy.
        Will keep trying indefinitely until successful.

        :param url: The URL to request.
        :param timeout: Timeout for the request.
        :param session: Optionally, an existing aiohttp.ClientSession.
        :return: The full aiohttp.ClientResponse object or None if all attempts fail.
        """

        if session is None:
            session = aiohttp.ClientSession()

        while True:  # Infinite retry loop
            proxy = await self.get_proxy()

            try:
                response = await _get_request(url=url, timeout=timeout, proxy=proxy, session=session)

                self.feedback_proxy(success=True)
                return response

            except Exception:
                self.feedback_proxy(success=False)

    def __len__(self):
        return len(self.data_manager)
