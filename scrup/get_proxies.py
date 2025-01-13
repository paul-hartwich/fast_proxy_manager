import asyncio
import logging
import random
from typing import List, Tuple, Dict, Any

import aiohttp
import requests


async def is_proxy_valid(proxy_complete_url: str) -> Tuple[bool, Any]:
    """
    Check if a proxy is valid by checking if the IP is reachable through the proxy.
    :param proxy_complete_url: example: http://ip:port
    """
    if ':' not in proxy_complete_url.split('//')[-1]:
        return False, None

    proxy_formatted = {"http": proxy_complete_url, "https": proxy_complete_url}
    url = 'https://httpbin.org/ip'

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, proxy=proxy_complete_url, timeout=15) as response:
                if response.status != 200:
                    return False, None
                logging.debug(f'Proxy {proxy_complete_url} is working.')
                return True, proxy_formatted
        except (
                asyncio.TimeoutError, aiohttp.ClientError, AssertionError, OSError, RuntimeError,
                ConnectionResetError) as e:
            logging.debug(f'Error in is_proxy_valid: {e}')
            return False, None


def download_proxies(full_list: bool = False) -> List[str]:
    """
    proxy sources: https://api.proxyscrape.com/ and https://github.com/proxifly/free-proxy-list
    :return: list in format: ["http://ip:port", "http://ip:port", ...]
    """
    proxies = set()

    def fetch_proxies_from_proxyscrape():
        try:
            logging.debug('Fetching proxies from proxyscrape API')
            response = requests.get(
                "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"
            )
            response.raise_for_status()
            proxy_data = response.json()
            for proxy_dict in proxy_data.get("proxies", []):
                proxies.add(proxy_dict.get("proxy"))
        except requests.RequestException as e:
            logging.debug(f'Error fetching proxies: {e}')

    def fetch_github_free_proxy_list():
        try:
            logging.debug('Fetching proxies from GitHub free proxy list')
            response = requests.get(
                "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.json"
            )
            response.raise_for_status()
            proxy_data = response.json()
            for proxy in proxy_data:
                proxies.add(proxy['proxy'])
        except requests.RequestException as e:
            logging.debug(f'Error fetching proxies from GitHub repository: {e}')

    fetch_proxies_from_proxyscrape()
    if full_list:
        fetch_github_free_proxy_list()

    logging.debug(f'Fetched {len(proxies)} proxies')
    proxy_list = list(proxies)
    random.shuffle(proxy_list)
    return proxy_list


async def fetch_proxies(simultaneous_proxy_requests: int, min_max: Tuple[int, int], full_list: bool = False) -> Tuple[
    List[Dict[str, str]], Dict[str, int]]:
    failed_proxies_while_fetch = 0
    working_proxies = []
    proxy_data = {'fetched_proxy': 0, 'working_proxy': 0, 'failed_proxies': 0}

    min_working_proxies, max_working_proxies = min_max
    if not min_working_proxies <= max_working_proxies:
        raise ValueError('min_working_proxies must be less than max_working_proxies')

    retry_limit = 1
    tri = -1
    while tri < retry_limit:
        logging.debug(f'Try: {tri}')
        downloaded_proxies = download_proxies(full_list)
        proxy_data['fetched_proxy'] = len(downloaded_proxies)

        semaphore = asyncio.Semaphore(simultaneous_proxy_requests)
        logging.debug('Simultaneous allowed proxy requests: %s', simultaneous_proxy_requests)

        async def limited_is_proxy_valid(proxy: str) -> Tuple[bool, Any]:
            async with semaphore:
                return await is_proxy_valid(proxy)

        tasks = [limited_is_proxy_valid(proxy) for proxy in downloaded_proxies]
        for task in asyncio.as_completed(tasks):
            valid, formatted_proxy = await task
            if valid:
                working_proxies.append(formatted_proxy)
                if len(working_proxies) >= max_working_proxies:
                    logging.debug('Reached maximum working proxies')
                    proxy_data['working_proxy'] = len(working_proxies)
                    proxy_data['failed_proxies'] = failed_proxies_while_fetch
                    return working_proxies, proxy_data
            else:
                failed_proxies_while_fetch += 1

        logging.debug('Finished checking proxies. Working proxies: %s', working_proxies)
        proxy_data['working_proxy'] = len(working_proxies)

        if len(working_proxies) >= min_working_proxies:
            proxy_data['failed_proxies'] = failed_proxies_while_fetch
            return working_proxies, proxy_data

        tri += 1
        if tri < retry_limit:
            logging.info(f'Less than {min_working_proxies} proxies found. Doing full list scan.')
        full_list = True

    proxy_data['failed_proxies'] = failed_proxies_while_fetch
    return working_proxies, proxy_data


if __name__ == '__main__':
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] "%(message)s"',
        datefmt='%d/%b/%Y %H:%M:%S'
    )
    logging.debug(asyncio.run(fetch_proxies(5, (2200, 2000000))))
