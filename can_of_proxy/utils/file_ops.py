import json
from pathlib import Path


def read_json(file: Path):
    with open(file, "r") as f:
        return json.load(f)


def write_json(file: Path, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)
