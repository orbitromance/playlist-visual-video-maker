from __future__ import annotations

import re
from pathlib import Path


INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_filename(value: str, fallback: str = "track") -> str:
    cleaned = INVALID_FILENAME.sub("_", value).strip(" .")
    return cleaned[:120] or fallback


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 10_000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"사용 가능한 파일명을 만들 수 없습니다: {path}")
