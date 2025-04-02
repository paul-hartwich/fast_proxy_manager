import ineedproxy as inp
from pathlib import Path
import asyncio
import logging
from ineedproxy.get import fetch_json_proxy_list  # Import der Funktion

proxy_data = Path("proxy_data")
logging.getLogger("ineedproxy").setLevel(logging.DEBUG)  # default level for the logger is INFO


# also supported, but in my testing only very few proxies were working
# https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.json
# proxyscrape.com worked best for me

async def fetch_proxies():
    return await fetch_json_proxy_list(
        "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"
    )


fetching_method = [fetch_proxies]


async def main():
    # Create a proxy manager and instantly start fetching some proxies
    manager = await inp.Manager(fetching_method=fetching_method, data_file=proxy_data, auto_fetch_proxies=True)


asyncio.run(main())
