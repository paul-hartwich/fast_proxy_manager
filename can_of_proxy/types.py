from typing import TypedDict
from yarl import URL


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
