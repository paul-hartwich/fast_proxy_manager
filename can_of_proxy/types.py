import re
from typing import Union, TypedDict


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
        return f"URL(protocol={self.protocol}, ip={self.ip}, port={self.port})"

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


if __name__ == '__main__':
    url = URL("https://123.123.123.123:8080")
    print(url)
    print(url.is_absolute())
    print("Protocol:", url.protocol, "IP:", url.ip, "Port:", url.port)
