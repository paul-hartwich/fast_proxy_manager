from can_of_proxy.can import Can
import aiohttp
from can_of_proxy.utils import get
from typing import Optional


class AutoCan:
    def __init__(self):
        self.can = Can()

    async def get_request(self, url: str,
                          session: Optional[aiohttp.ClientSession] | False = False) -> aiohttp.ClientResponse:
        return get.get_request(url, session=session, proxy=self.can.get_proxy())
