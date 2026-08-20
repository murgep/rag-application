from pathlib import Path


def load_text_file(file_path: str) -> str:
    """
    Load a text file and return its contents as a string.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    return path.read_text(encoding="utf-8")