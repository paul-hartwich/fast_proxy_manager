from typing import Optional, List

from can_of_proxy.proxy_data_manager import ProxyDataManager, NoProxyAvailable, ProxyDict
from yarl import URL
from pathlib import Path
from can_of_proxy.utils import get
import aiohttp


class Can:
    def __init__(self, data_file: Path | None = None,
                 preferred_protocol: list[str] | str | None = None,
                 preferred_country: list[str] | str | None = None,
                 preferred_anonymity: list[str] | str | None = None,
                 allowed_fails_in_row: int = 3,
                 fails_without_check: int = 2,
                 percent_failed_to_remove: float = 0.5):
        """

        :param data_file: Path to a store file with proxy data.
        Highly recommended to use it.
        :param preferred_protocol: It can later be changed when getting a proxy.
        :param preferred_country: It can later be changed when getting a proxy.
        :param preferred_anonymity: It can later be changed when getting a proxy.
        :param allowed_fails_in_row: How many times a proxy can fail in a row before being removed.
        :param fails_without_check: How many times a proxy can fail before being checked for percentage of fails to remove.
        :param percent_failed_to_remove: Percentage of fails to remove a proxy.
        Example: 0.5 means 50% of tries are fails, if higher than that it gets removed.
        """

        self.preferred_protocol = preferred_protocol
        self.preferred_country = preferred_country
        self.preferred_anonymity = preferred_anonymity

        self.manager = ProxyDataManager(msgpack=data_file, allowed_fails_in_row=allowed_fails_in_row,
                                        fails_without_check=fails_without_check,
                                        percent_failed_to_remove=percent_failed_to_remove)

    async def get_request(self, url: URL, session: Optional[aiohttp.ClientSession]) -> aiohttp.ClientResponse:
        """
        New session if Session not provided.
        Gives automatic feedback to the proxy manager.
        :param url: Url to send request to
        :param session: aiohttp.ClientSession
        """
        proxy = self.manager.get_proxy()
        if proxy is None:
            raise NoProxyAvailable("Request stopped because no proxy was available.")

        response = await get.get_request(url, proxy, session)
        if response.status == 200:
            self.manager.feedback_proxy(True)
        else:
            self.manager.feedback_proxy(False)
        return response

    def get_proxy(self) -> URL:
        return self.manager.get_proxy()

    def feedback(self, success: bool) -> None:
        """
        Feedback the proxy manager about the success of the proxy.
        :param success: True if the proxy was successful, False otherwise.
        """
        self.manager.feedback_proxy(success)

    def add_proxy(self,
                  proxies: URL | list[URL] | list[ProxyDict],
                  country: str | None = None,
                  anonymity: str | None = None) -> None:
        """
        Add a proxy to the list.
        You can add a list of proxies at once, but all of them will have the same country and anonymity.
        If a list of dictionaries is used, other params will be ignored and the data will be used from the dictionary.
        """
        self.manager.add_proxy(proxies, country, anonymity)

    def fetch_proxies(self, max_proxies: int | None = None) -> List[URL] | List[ProxyDict]:
        """
        Fetch proxies from the sources.
        """

        return

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Handle any cleanup if necessary
        pass
