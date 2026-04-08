from pathlib import Path


def save_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")