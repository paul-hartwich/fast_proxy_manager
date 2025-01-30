import orjson
from pathlib import Path

def read_json(file: Path):
    with open(file, "rb") as f:
        return orjson.loads(f.read())

def write_json(file: Path, data):
    with open(file, "wb") as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))