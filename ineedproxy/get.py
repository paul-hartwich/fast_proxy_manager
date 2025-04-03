from typing import List, Optional
import asyncio

from .utils import URL, ProxyDict, convert_to_proxy_dict_format
from .logger import logger

import orjson
import aiohttp


async def get_request(url: str, retries: int = 1, timeout: int = 10,
                      proxy: Optional[str] = None, session: Optional[aiohttp.ClientSession] = None,
                      ) -> Optional[aiohttp.ClientResponse]:
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
    created_session = False

    for attempt in range(retries):
        try:
            if session is None:
                session = aiohttp.ClientSession()
                created_session = True

            async with session.get(url, headers=headers, proxy=proxy, timeout=timeout) as response:
                return await response.text()

        except aiohttp.ClientConnectionError as e:
            logger.error(f"Connection error (Attempt {attempt + 1}/{retries}): {e}")

        if attempt < retries - 1:
            await asyncio.sleep(1)

    if created_session:
        await session.close()

    return None  # If all retries fail, return None


async def fetch_json_proxy_list(url: str) -> List[ProxyDict]:
    """Fetches a list of proxies from a website"""
    response = await get_request(url, retries=3, timeout=15)

    try:
        proxies = orjson.loads(response)
        proxy_list = convert_to_proxy_dict_format(proxies)
        logger.debug("Fetched %d proxies", len(proxy_list))
        return proxy_list
    except orjson.JSONDecodeError:
        logger.error("Failed to parse JSON")
        return []
