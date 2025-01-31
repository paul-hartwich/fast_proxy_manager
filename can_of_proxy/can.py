from typing import Optional, List, Union
from can_of_proxy.proxy_data_manager import ProxyDataManager
from utils import NoProxyAvailable, ProxyDict, ProxiflyDict, URL
from pathlib import Path
import get
from test_proxies import test_proxies
import aiohttp


def _extract_from_url(url: URL) -> [URL.scheme, URL.host, URL.port]:
    return url.scheme, url.host, url.port


def _convert_data_from_proxifly(data: ProxiflyDict) -> ProxyDict:
    return ProxyDict(
        url=URL(data["proxy"]),
        country=data["geolocation"]["country"],
        anonymity=data["anonymity"]
    )


def _convert_list_to_dicts(proxies: List[URL]) -> List[ProxyDict]:
    return [ProxyDict(url=proxy, anonymity=None, country=None) for proxy in proxies]


def _check_case(proxies: Union[List[URL], List[ProxyDict]]) -> str:
    if proxies and isinstance(proxies[0], URL):
        return "List[URL]"
    elif proxies and isinstance(proxies[0], dict) and "url" in proxies[0]:
        return "List[ProxyDict]"
    else:
        return "Unknown"


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

        if data_file is not None:
            data_file = Path(data_file)

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
                  proxies: Union[List[URL], List[ProxyDict], None],
                  country: str | None = None,
                  anonymity: str | None = None) -> None:
        """
        Add a proxy to the list.
        You can add a list of proxies at once, but all of them will have the same country and anonymity.
        If a list of dictionaries is used, other params will be ignored and the data will be used from the dictionary.
        """
        self.manager.add_proxy(proxies, country, anonymity)

    async def fetch_proxies(self, test_proxies: bool = True, fetch_from_proxifly: bool = True,
                            proxies: Union[List[URL], List[ProxyDict]] = None) -> Union[List[URL], List[ProxyDict]]:
        """
        Fetch proxies from the sources and add them to the proxy manager.
        """
        formated_proxifly_dicts = []
        custom_proxy_dicts = []

        if proxies is None and not fetch_from_proxifly:
            raise ValueError("You need to provide proxies or set fetch_from_proxifly to True.")

        if fetch_from_proxifly:
            proxifly_dicts = await get.github_proxifly()
            formated_proxifly_dicts = [_convert_data_from_proxifly(proxy) for proxy in proxifly_dicts]

        if proxies is not None:
            case = _check_case(proxies)
            if case == "List[URL]":
                custom_proxy_dicts = _convert_list_to_dicts(proxies)
            elif case == "List[ProxyDict]":
                custom_proxy_dicts = proxies
            else:
                raise ValueError(f"Unknown case: {case}")

        if fetch_from_proxifly:
            proxies = formated_proxifly_dicts + custom_proxy_dicts
        else:
            proxies = custom_proxy_dicts

        if test_proxies:
            proxies = await get.test_proxies(proxies)

        self.manager.add_proxy(proxies)
        self.manager.update_data(remove_duplicates=True)


if __name__ == '__main__':
    import asyncio


    async def main():
        mgr = Can(data_file="proxies.msgpack")
        mgr.manager.rm_all_proxies()
        await mgr.fetch_proxies(test_proxies=True)
        print(len(mgr.manager))


    asyncio.run(main())
