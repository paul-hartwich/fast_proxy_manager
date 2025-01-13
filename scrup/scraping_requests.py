import asyncio
import logging
import time
from random import randint
from typing import Dict, Any, Tuple

import requests

from .get_proxies import fetch_proxies
from .utils import read_json, write_json


def check_internet() -> bool:
    try:
        requests.get('https://httpbin.org/ip', timeout=15)
        return True
    except requests.exceptions.RequestException:
        return False


def _ensure_internet_connection():
    while not check_internet():
        logging.error('No internet connection. Please check your connection. Waiting 10 seconds then trying again.')
        time.sleep(10)


def _validate_min_proxies(min_proxies: int):
    if min_proxies < 1:
        raise ValueError('min_proxies must be at least 1.')


class CreateRequestSession:
    def __init__(self, min_proxies: int = 1, max_proxies: int = 8, timeout: int = 10,
                 user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0',
                 simultaneous_proxy_requests: int = 100, proxy_file: str = 'proxies.json'):
        """
        Made to do not get IP banned and be anonymous.


        Uses logging for debug messages.

        :param min_proxies: when proxies are less than this number, it will refresh the proxies potentially causing an infinite loop
        :param max_proxies: maximum number of proxies to fetch will stop fetching when reached
        :param timeout: timeout for manual requests not the proxy timeout
        :param user_agent: user agent to use for the requests
        :param simultaneous_proxy_requests: number of simultaneous requests to make, default should work fine
        """
        _ensure_internet_connection()
        _validate_min_proxies(min_proxies)

        self.min_proxies = min_proxies
        self.max_proxies = max_proxies
        self.current_proxy_file = proxy_file
        self.simultaneous_proxy_requests = simultaneous_proxy_requests
        self.proxies = []
        self.last_proxy = None
        self.timeout = timeout
        self.user_agent = {'User-Agent': user_agent}

        logging.debug('Starting setup script for CreateRequestSession.')
        self._initialize_proxies()

    def _initialize_proxies(self):
        read_proxies = read_json(self.current_proxy_file)
        if read_proxies is None:
            logging.debug('Read data is None.')
            self.refresh_proxies()
        else:
            logging.debug(f'Read {self.current_proxy_file} and data exists.')
            self.proxies = read_proxies
            logging.debug(f'Proxies found: {len(self.proxies)}')

    def refresh_proxies(self):
        self.last_proxy = None
        while True:
            logging.info('Refreshing proxies. This may take a while.')
            self.proxies, proxy_data = asyncio.run(
                fetch_proxies(self.simultaneous_proxy_requests, (self.min_proxies, self.max_proxies)))
            logging.info(proxy_data)
            if not self.proxies:
                logging.error('NO PROXIES FOUND!!! Waiting for 1 minute then trying again.')
                time.sleep(60)
            elif len(self.proxies) < self.min_proxies:
                logging.error(f'Less than {self.min_proxies} proxies found. Waiting 2 minutes then trying again.')
                time.sleep(120)
            else:
                write_json(self.current_proxy_file, self.proxies)
                logging.debug(f'Proxies refreshed and saved to {self.current_proxy_file}.')
                asyncio.run(asyncio.sleep(1))
                break

    def _handle_proxy_error(self, random_proxy_index: int):
        self.proxies.pop(random_proxy_index)
        write_json(self.current_proxy_file, self.proxies)
        if self.last_proxy is not None and random_proxy_index < self.last_proxy:
            self.last_proxy -= 1

    def _make_request(self, url: str, method: str = 'GET', **kwargs: Any) -> requests.Response:
        """ Makes a request with a random proxy. If the request fails, it will try again with a different proxy. """
        while True:
            if not self.proxies or len(self.proxies) < self.min_proxies:
                self.refresh_proxies()

            proxy, random_proxy_index = self._select_random_proxy()
            try:
                logging.debug(f'Trying to {method} with proxy {proxy} from {url}.')
                response = requests.request(method, url, proxies=proxy, timeout=self.timeout, headers=self.user_agent,
                                            **kwargs)
                response.raise_for_status()
                self.last_proxy = random_proxy_index
                logging.info(f'{method} request successful.')
                return response
            except (
                    requests.exceptions.ProxyError, requests.exceptions.ConnectionError,
                    requests.exceptions.RequestException,
                    ConnectionResetError) as e:
                logging.error(f'Request error: {e}.')
                self._handle_proxy_error(random_proxy_index)

    def _select_random_proxy(self) -> Tuple[Dict[str, str], int]:
        if len(self.proxies) > 1:
            while True:
                random_proxy_index = randint(0, len(self.proxies) - 1)
                if random_proxy_index != self.last_proxy:
                    break
        else:
            random_proxy_index = 0
        return self.proxies[random_proxy_index], random_proxy_index

    def download_file(self, url: str, file: str):
        response = self._make_request(url)
        with open(file, 'wb') as f:
            f.write(response.content)

    def scrape_html(self, url: str) -> Any:
        from bs4 import BeautifulSoup
        response = self._make_request(url)
        return BeautifulSoup(response.text, 'html.parser')
