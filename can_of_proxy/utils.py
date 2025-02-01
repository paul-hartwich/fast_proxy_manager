import re
from typing import Union, TypedDict, List


def _get_port(port: str) -> Union[int, None]:
    try:
        port = int(port)
        if 0 < port < 65536:
            return port
    except ValueError:
        pass
    return None


def _get_protocol(protocol: str) -> Union[str, None]:
    if protocol in ['http', 'https', 'socks4', 'socks5']:
        return protocol
    return None


def _get_ip(ip: str) -> Union[str, None]:
    if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', ip):
        parts = ip.split('.')
        if all(0 <= int(part) <= 255 for part in parts):
            return ip
    return None


class URL:
    def __init__(self, url: str):
        self.url = url
        self.protocol, self.ip, self.port = self._parse_url(url)

    def _parse_url(self, url: str):
        protocol, ip, port = None, None, None
        if '://' in url:
            protocol, rest = url.split('://', 1)
            protocol = _get_protocol(protocol)
            if '/' in rest:
                ip_port, _ = rest.split('/', 1)
            else:
                ip_port = rest
            if ':' in ip_port:
                ip, port = ip_port.split(':', 1)
                port = _get_port(port)
            else:
                ip = ip_port
            ip = _get_ip(ip)
        return protocol, ip, port

    def __str__(self):
        return f"URL(protocol={self.protocol:<6}, ip={self.ip:<15}, port={self.port:<5})"

    def __repr__(self):
        return self.url

    def __eq__(self, other):
        return self.url == other.url

    def is_absolute(self) -> bool:
        return self.protocol is not None and self.ip is not None and self.port is not None


class ProxyDict(TypedDict):
    """
    {"url": URL, "country": str, "anonymity": str}
    """
    url: URL
    country: str | None
    anonymity: str | None


class GeolocationDict(TypedDict):
    """
    {"country": str, "city": str}
    """
    country: str
    city: str


class ProxiflyDict(TypedDict):
    """
    {"proxy": str, "anonymity": str, "geolocation": dict}
    """
    proxy: str
    anonymity: str
    geolocation: GeolocationDict


def proxifly_to_proxy_dict(proxifly_dict: ProxiflyDict) -> ProxyDict:
    url = URL(proxifly_dict["proxy"])
    return {"url": url, "country": proxifly_dict["geolocation"]["country"], "anonymity": proxifly_dict["anonymity"]}


def _convert_to_proxy_dict(proxy_store_dict: dict) -> ProxyDict:
    # Search for protocol, ip, and port first in the base dict
    protocol = proxy_store_dict.get("protocol")
    ip = proxy_store_dict.get("ip")
    port = proxy_store_dict.get("port")

    # If protocol, ip, and port are not available, search for url or proxy
    if not (protocol and ip and port):
        url_str = proxy_store_dict.get("url") or proxy_store_dict.get("proxy")
        if url_str:
            url = URL(url_str)
        else:
            raise ValueError("Proxy dictionary must contain 'url' or 'proxy' key or 'ip', 'port', 'protocol' keys")
    else:
        url = URL(f"{protocol}://{ip}:{port}")

    # Search for country in the base dict first, then in all other dicts
    country = proxy_store_dict.get("country")
    if not country:
        for value in proxy_store_dict.values():
            if isinstance(value, dict):
                country = value.get("country")
                if country:
                    break

    # Search for anonymity in the base dict first, then in all other dicts
    anonymity = proxy_store_dict.get("anonymity")
    if not anonymity:
        for value in proxy_store_dict.values():
            if isinstance(value, dict):
                anonymity = value.get("anonymity")
                if anonymity:
                    break

    return ProxyDict(url=url, country=country, anonymity=anonymity)


def convert_to_proxy_dict_format(proxy_dict_list: List[dict]) -> List[ProxyDict]:
    if isinstance(proxy_dict_list, dict) and "proxies" in proxy_dict_list:
        proxy_dict_list = proxy_dict_list['proxies']
    return [_convert_to_proxy_dict(proxy_dict) for proxy_dict in proxy_dict_list]


class NoProxyAvailable(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"NoProxyAvailable: {self.message}"


class NoValidProxyAvailable(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"NoValidProxyAvailable: {self.message}"
