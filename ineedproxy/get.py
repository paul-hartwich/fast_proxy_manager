from typing import List, Optional, Dict
import asyncio

from .utils import ProxyDict, convert_to_proxy_dict_format
from .logger import logger

import orjson
import aiohttp


async def get_request(
        url: str,
        retries: int = 1,
        timeout: int = 10,
        proxy: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None,
        headers: Optional[Dict[str, str]] = None,
) -> str:
    """
    Performs a GET request with retry logic and proper error handling.

    Args:
        url: The URL to request
        retries: Number of retry attempts
        timeout: Request timeout in seconds
        proxy: Optional proxy URL
        session: Optional aiohttp session to reuse
        headers: Optional custom headers

    Returns:
        Response text content

    Raises:
        Exception: If all retry attempts fail
    """
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Brave/124.0.0.0",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Sec-CH-UA": "\"Brave\";v=\"124\", \"Chromium\";v=\"124\", \"Not A;Brand\";v=\"99\"",
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": "\"Windows\""
    }

    if headers:
        default_headers.update(headers)

    created_session = False
    last_exception = None

    try:
        if session is None:
            session = aiohttp.ClientSession()
            created_session = True

        for attempt in range(retries):
            try:
                async with session.get(
                        url,
                        headers=default_headers,
                        proxy=proxy,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status >= 400:
                        error_msg = f"HTTP error: {response.status}"
                        logger.warning(f"{error_msg} (Attempt {attempt + 1}/{retries})")
                        response.raise_for_status()  # This will raise an exception for 4xx/5xx status codes

                    return await response.text()

            except (
                    aiohttp.ClientError,
                    aiohttp.ClientResponseError,
                    asyncio.TimeoutError
            ) as e:
                last_exception = e
                logger.warning(f"Request failed (Attempt {attempt + 1}/{retries}): {str(e)}")

                if attempt < retries - 1:
                    # Exponential backoff for retries
                    await asyncio.sleep(2 ** attempt)
                    continue
                break

        # If we got here, all retries failed
        logger.error(f"All {retries} attempts failed for URL: {url}")
        if last_exception:
            raise last_exception
        raise Exception(f"Failed to fetch {url} after {retries} attempts")

    finally:
        # Ensure the session is closed if we created it
        if created_session and session is not None:
            await session.close()


async def fetch_json_proxy_list(url: str) -> List[ProxyDict]:
    """
    Fetches a list of proxies from a website and parses the JSON response.

    Args:
        url: URL to fetch a proxy list from

    Returns:
        List of proxy dictionaries

    Raises:
        Exception: If the request fails or JSON parsing fails
    """
    try:
        response = await get_request(url, retries=3, timeout=15)

        try:
            proxies = orjson.loads(response)
            proxy_list = convert_to_proxy_dict_format(proxies)
            return proxy_list

        except orjson.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            raise Exception(f"Invalid JSON response from {url}: {str(e)}")

    except Exception as e:
        logger.error(f"Failed to fetch proxy list from {url}: {str(e)}")
        raise
