from pathlib import Path
from typing import List, Dict, Any
import msgpack


def read_msgpack(file: Path) -> List[Dict[str, Any]]:
    """Reads and unpacks data from a msgpack file.

    Args:
        file: Path to the msgpack file.

    Returns:
        Unpacked data as a list of dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        msgpack.UnpackException: If the file is corrupted.
    """
    try:
        with open(file, "rb") as f:
            return msgpack.unpackb(f.read(), raw=False)
    except FileNotFoundError:
        raise FileNotFoundError(f"Msgpack file not found: {file}")
    except msgpack.UnpackException as e:
        raise msgpack.UnpackException(f"Failed to unpack msgpack file {file}: {e}")


def write_msgpack(file: Path, data: List[Dict[str, Any]]) -> None:
    """Writes data to a msgpack file.

    Args:
        file: Path where the msgpack file will be saved.
        data: Data to be packed and written (list of dictionaries).

    Raises:
        PermissionError: If the file cannot be written.
    """
    try:
        file.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        with open(file, "wb") as f:
            f.write(msgpack.packb(data, use_bin_type=True))
    except PermissionError:
        raise PermissionError(f"No permission to write to {file}")
