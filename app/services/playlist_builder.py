from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

from .ffmpeg_service import FFmpegService


class PlaylistBuilder:
    def __init__(self, service: FFmpegService | None = None) -> None:
        self.service = service or FFmpegService()

    def concatenate(
        self,
        clips: list[Path],
        output: Path,
        work_dir: Path,
        callback: Callable[[float, float], None] | None = None,
        total_duration: float = 1.0,
        log_path: Path | None = None,
    ) -> Path:
        if not clips:
            raise ValueError("연결할 트랙 영상이 없습니다.")
        concat_file = work_dir / "concat.txt"
        concat_file.write_text(
            "\n".join("file '" + str(path.resolve()).replace("'", r"'\''") + "'" for path in clips),
            encoding="utf-8",
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        args = [
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c", "copy", "-movflags", "+faststart", str(output),
        ]
        try:
            self.service.run_with_progress(args, total_duration, callback, log_path)
        except RuntimeError:
            fallback = [
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(output),
            ]
            self.service.run_with_progress(fallback, total_duration, callback, log_path)
        return output
