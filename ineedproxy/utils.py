import re
from collections import defaultdict
from typing import Union, TypedDict, List, Dict, Set, Optional


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
    def __init__(self, url: Union[str, 'URL']):
        if isinstance(url, URL):
            self.url = url.url
            self.protocol = url.protocol
            self.ip = url.ip
            self.port = url.port
        else:
            self.url = url
            self.protocol, self.ip, self.port = self._parse_url()

    def _parse_url(self):
        protocol, ip, port = None, None, None
        if '://' in self.url:
            protocol, rest = self.url.split('://', 1)
            protocol = _get_protocol(protocol)
        else:
            rest = self.url

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


class ProxyPreferences(TypedDict, total=False):
    protocol: Optional[Union[str, List[str]]]
    country: Optional[Union[str, List[str]]]
    anonymity: Optional[Union[str, List[str]]]
    exclude_protocol: Optional[Union[str, List[str]]]
    exclude_country: Optional[Union[str, List[str]]]
    exclude_anonymity: Optional[Union[str, List[str]]]


class ProxyIndex:
    """An indexing system for efficient proxy lookup and filtering operations."""

    def __init__(self):
        self.protocol_index: Dict[str, Set[int]] = defaultdict(set)
        self.country_index: Dict[str, Set[int]] = defaultdict(set)
        self.anonymity_index: Dict[str, Set[int]] = defaultdict(set)

    def add_proxy(self, index: int, proxy: dict) -> None:
        self.protocol_index[proxy["protocol"]].add(index)
        self.country_index[proxy["country"]].add(index)
        self.anonymity_index[proxy["anonymity"]].add(index)

    def remove_proxy(self, index: int, proxy: dict) -> None:
        self.protocol_index[proxy["protocol"]].discard(index)
        self.country_index[proxy["country"]].discard(index)
        self.anonymity_index[proxy["anonymity"]].discard(index)

    def clear(self) -> None:
        self.protocol_index.clear()
        self.country_index.clear()
        self.anonymity_index.clear()

    def rebuild_index(self, proxies: List[dict]) -> None:
        """Rebuild the entire index from a list of proxies."""
        self.clear()
        for i, proxy in enumerate(proxies):
            self.add_proxy(i, proxy)

    def __str__(self):
        return f"protocol_index: {self.protocol_index}, country_index: {self.country_index}, anonymity_index: {self.anonymity_index}"


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

    # Search for country code
    country = proxy_store_dict.get("countryCode")
    if not country:
        for value in proxy_store_dict.values():
            if isinstance(value, dict):
                country = value.get("countryCode")
                if country:
                    break

    # Search for country in the base dict first, then in all other dicts
    if not country:
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


__all__ = ['URL', 'ProxyDict', 'ProxyPreferences', 'ProxyIndex', 'convert_to_proxy_dict_format', 'NoProxyAvailable',
           'NoValidProxyAvailable']
