import json
from pathlib import Path


def clear_dir(directory: Path):
    for file in directory.iterdir():
        if file.is_file():
            file.unlink()
        elif file.is_dir():
            clear_dir(file)
            file.rmdir()


def read_file(file: Path):
    try:
        with open(file, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None


def write_file(file: Path, data):
    try:
        with open(file, "w") as f:
            f.write(data)
    except FileNotFoundError:
        file.parent.mkdir(parents=True, exist_ok=True)
        write_file(file, data)


def read_json(file: Path):
    with open(file, "r") as f:
        return json.load(f)


def write_json(file: Path, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)





def copy_files(file: Path, new_dir: Path):
    new_file = new_dir / file.name
    file_content = read_file(file)
    write_file(new_file, file_content)
