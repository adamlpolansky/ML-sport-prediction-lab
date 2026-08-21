from __future__ import annotations

import re
from pathlib import Path


def test_local_markdown_links_resolve() -> None:
    root = Path(__file__).resolve().parents[1]
    missing = []
    for document in root.rglob("*.md"):
        if any(part in {".venv", "build", "dist"} for part in document.parts):
            continue
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            resolved = (document.parent / target.split("#", 1)[0]).resolve()
            if not resolved.exists():
                missing.append(f"{document.relative_to(root)} -> {target}")
    assert missing == []
