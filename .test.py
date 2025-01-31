import can_of_proxy as cop
from pprint import pprint

manager = cop.Can(data_file="proxy_data.msgpack")

try:
    proxy = manager.get_proxy()
    pprint(proxy)
except cop.NoProxyAvailable:
    manager.fetch_proxies()

proxy = manager.get_proxy()
pprint(proxy)
