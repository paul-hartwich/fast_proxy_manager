from proxy_data_manager import ProxyDataManager
from utils import IP
from pathlib import Path


class Can:
    def __init__(self, json_file: Path | None = None,
                 preferred_protocol: list[str] | str | None = None,
                 preferred_country: list[str] | str | None = None,
                 preferred_anonymity: list[str] | str | None = None,
                 allowed_fails_in_row: int = 3,
                 fails_without_check: int = 2,
                 percent_failed_to_remove: float = 0.5):
        """

        :param json_file: Path to a store file with proxy data.
        Highly recommended to use it.
        :param preferred_protocol: It can later be changed when getting a proxy.
        :param preferred_country: It can later be changed when getting a proxy.
        :param preferred_anonymity: It can later be changed when getting a proxy.
        :param allowed_fails_in_row: How many times a proxy can fail in a row before being removed.
        :param fails_without_check: How many times a proxy can fail before being checked for percentage of fails to remove.
        :param dont_store_data:
        :param percent_failed_to_remove:
        """

        self.preferred_protocol = preferred_protocol
        self.preferred_country = preferred_country
        self.preferred_anonymity = preferred_anonymity

        self.manager = ProxyDataManager(json_file=json_file, allowed_fails_in_row=allowed_fails_in_row,
                                        fails_without_check=fails_without_check,
                                        percent_failed_to_remove=percent_failed_to_remove)

    def get_proxy(self) -> IP:
        return self.manager.get_proxy()
