from __future__ import annotations

from pathlib import Path

from .ffmpeg_service import FFmpegService


class MetadataService:
    def __init__(self, ffmpeg: FFmpegService | None = None) -> None:
        self.ffmpeg = ffmpeg or FFmpegService()

    def duration(self, audio_path: Path) -> float:
        data = self.ffmpeg.probe(audio_path)
        try:
            duration = float(data["format"]["duration"])
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError(f"오디오 재생시간을 읽을 수 없습니다: {audio_path}") from error
        if duration <= 0:
            raise RuntimeError(f"오디오 재생시간이 올바르지 않습니다: {audio_path}")
        return duration
