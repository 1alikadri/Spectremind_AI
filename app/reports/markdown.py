from pathlib import Path


def save_markdown_report(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")