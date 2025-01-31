import msgpack
from pathlib import Path


def read_msgpack(file: Path) -> list[dict]:
    with open(file, "rb") as f:
        return msgpack.unpackb(f.read(), raw=False)  # raw=False ensures string keys


def write_msgpack(file: Path, data: list[dict]):
    with open(file, "wb") as f:
        f.write(msgpack.packb(data, use_bin_type=True))  # use_bin_type=True for compatibility
