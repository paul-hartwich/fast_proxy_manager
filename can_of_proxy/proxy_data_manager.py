from utils import get_request
from pathlib import Path


class ProxyDataManager:
    def __init__(self, store: Path | False = False):
        self.store = store
        self.proxies = []

        self.validate_params()

    def validate_params(self):
        Path.mkdir(self.store, exist_ok=True)

    def add_proxy(self, proxy: str):
        pass

    def rm_duplicate_proxies(self):
        pass

    def rm_proxy(self, number: int):
        pass

    def get_proxy(self, number: int):
        pass

    def get_random_proxy(self):
        pass

    def fetch_proxies(self):
        pass
   