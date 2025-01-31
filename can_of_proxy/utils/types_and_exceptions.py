from typing import TypedDict
from yarl import URL


class ProxyDict(TypedDict):
    """
    {"url": URL, "country": str, "anonymity": str}
    """
    url: URL
    country: str | None
    anonymity: str | None


class NoProxyAvailable(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"NoProxyAvailable: {self.message}"
