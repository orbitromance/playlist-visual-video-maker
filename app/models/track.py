from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Track:
    audio_path: Path
    image_path: Path
    title: str
    artist: str
    duration: float
    order: int = 0

    def validate(self) -> None:
        if not self.title.strip():
            raise ValueError("곡 제목이 비어 있습니다.")
        if not self.artist.strip():
            raise ValueError("아티스트명이 비어 있습니다.")
        if not self.audio_path.is_file():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {self.audio_path}")
        if not self.image_path.is_file():
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {self.image_path}")
