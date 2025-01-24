class IP:
    def __init__(self, protocol: str, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.protocol = protocol

    def url(self):
        return f"{self.protocol}://{self.ip}:{self.port}"

    def get_protocol(self):
        return self.protocol

    def get_ip(self):
        return self.ip

    def get_port(self):
        return self.port

    def __repr__(self):
        """Optional: Define how the object is represented."""
        return f"CustomType({self.data})"
