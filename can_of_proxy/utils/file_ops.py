from pathlib import Path
import json
from typing import Any


def read_file(file_path: Path) -> list[str]:
    with open(file_path, "r") as f:
        return f.read().splitlines()


def write_file(file_path: Path, data: list[str]) -> None:
    with open(file_path, "w") as f:
        f.write("\n".join(data))


def read_json(file_path: Path) -> Any:
    with open(file_path, "r") as f:
        return json.load(f)


def write_json(file_path: Path, data: Any) -> None:
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
