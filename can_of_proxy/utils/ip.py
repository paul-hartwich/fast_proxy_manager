def _split_url(ip_string):
    protocol, ip, port = None, None, None  # Defaults for missing parts

    # Check for protocol
    if "://" in ip_string:
        protocol, rest = ip_string.split("://", 1)
    else:
        rest = ip_string

    # Check for port
    if ":" in rest:
        ip, port = rest.rsplit(":", 1)
    else:
        ip = rest

    # Raise exception if IP is missing
    if not ip.strip():  # Check for empty or whitespace-only IP
        raise ValueError("Input must contain at least an IP address.")

    return protocol, ip, int(port)


def _validate_port(port):
    try:
        port = int(port)
    except ValueError:
        raise ValueError("Port must be an integer.")

    if port < 1 or port > 65535:
        raise ValueError("Port must be between 1 and 65535.")

    return port


def _validate_ip(ip):
    parts = ip.split(".")
    if len(parts) != 4:
        raise ValueError("IP must contain 4 parts separated by dots.")

    for part in parts:
        try:
            part = int(part)
        except ValueError:
            raise ValueError("IP parts must be integers.")

        if part < 0 or part > 255:
            raise ValueError("IP parts must be between 0 and 255.")

    return ip


def _validate_protocol(protocol):
    if protocol not in ("http", "https", "socks4", "socks5"):
        raise ValueError("Invalid protocol. Must be one of: http, https, socks4, socks5.")

    return protocol


class IP:
    def __init__(self, protocol: str = None, ip: str = None, port: int | str = None, url: str = None):
        """
        Simple class to handle IP addresses with protocols and ports.

        When returning the URL, it will return url in format **protocol://ip:port** as str.

        :param protocol: Like http, https, socks4, socks5
        :param ip: has to be in format 255.255.255.255
        :param port: has to be an integer between 1 and 65535
        :param url: can be missing protocol, port or both
        """
        self.protocol = None
        self.ip = None
        self.port = None

        if url and (protocol or ip or port):
            raise ValueError("You cannot provide both URL and protocol, ip, port")

        if url:
            self.protocol, self.ip, self.port = _split_url(url)
        else:
            if ip:
                self.ip = str(ip)
            else:
                raise ValueError("No IP provided")

            if port:
                self.port = int(port)
            if protocol:
                self.protocol = str(protocol)

        self._validate_everything()

    def url(self, get_protocol: bool = True):
        if get_protocol and self.protocol:
            if self.port:
                return f"{self.protocol}://{self.ip}:{self.port}"
            else:
                return f"{self.protocol}://{self.ip}"
        elif self.port:
            return f"{self.ip}:{self.port}"
        else:
            return self.ip

    def _validate_everything(self):
        if self.protocol:
            self.protocol = _validate_protocol(self.protocol)
        if self.ip:
            self.ip = _validate_ip(self.ip)
        if self.port:
            self.port = _validate_port(self.port)

    def __str__(self):
        return self.url()


if __name__ == '__main__':
    # Test the IP class
    ip = IP(ip="123.123.123.123", port=8080, protocol="socks5")
    print(ip.url())
