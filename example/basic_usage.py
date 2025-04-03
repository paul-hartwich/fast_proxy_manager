import ineedproxy as inp
from pathlib import Path
import asyncio
import logging
from ineedproxy.get import fetch_json_proxy_list  # Import der Funktion
from ineedproxy.get import get_request as _get_request

proxy_data = Path("proxy_data")
logging.getLogger("ineedproxy").setLevel(logging.DEBUG)  # default level for the logger is INFO


# also supported, but in my testing only very few proxies were working
# https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.json
# proxyscrape.com worked best for me

async def fetch_proxies():
    return await fetch_json_proxy_list(
        "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"
    )  # the only restriction is that this method should return a list of ProxyDict


fetching_method = [fetch_proxies]

if __name__ == '__main__':
    async def main():
        # Create a proxy manager and instantly start fetching some proxies if missing
        manager = await inp.Manager(fetching_method=fetching_method, data_file=proxy_data, auto_fetch_proxies=True)
        proxy_response = await manager.get_request(url="https://httpbin.org/ip")  # test the proxies
        print("Proxies:", len(manager))
        print("Proxy_response:\n", proxy_response)


    asyncio.run(main())
