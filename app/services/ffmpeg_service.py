from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterable

ProgressCallback = Callable[[float, float], None]


class FFmpegService:
    def __init__(self, ffmpeg: str | None = None, ffprobe: str | None = None) -> None:
        bundled_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        bundled_ffmpeg = bundled_root / "ffmpeg.exe"
        bundled_ffprobe = bundled_root / "ffprobe.exe"
        self.ffmpeg = (
            ffmpeg
            or os.environ.get("PVM_FFMPEG")
            or (str(bundled_ffmpeg) if bundled_ffmpeg.is_file() else None)
            or shutil.which("ffmpeg")
        )
        self.ffprobe = (
            ffprobe
            or os.environ.get("PVM_FFPROBE")
            or (str(bundled_ffprobe) if bundled_ffprobe.is_file() else None)
            or shutil.which("ffprobe")
        )

    def ensure_available(self) -> None:
        if not self.ffmpeg:
            raise RuntimeError("프로그램에 포함된 FFmpeg를 찾을 수 없습니다. ZIP을 다시 내려받아 전체 압축을 풀어주세요.")
        if not self.ffprobe:
            raise RuntimeError("프로그램에 포함된 ffprobe를 찾을 수 없습니다. ZIP을 다시 내려받아 전체 압축을 풀어주세요.")

    def probe(self, path: Path) -> dict:
        self.ensure_available()
        result = subprocess.run(
            [self.ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or f"파일을 읽을 수 없습니다: {path}")
        return json.loads(result.stdout)

    def run_with_progress(
        self,
        args: Iterable[str],
        duration: float,
        callback: ProgressCallback | None = None,
        log_path: Path | None = None,
    ) -> None:
        self.ensure_available()
        command = [self.ffmpeg, "-hide_banner", "-y", *map(str, args), "-progress", "pipe:1", "-nostats"]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert process.stdout is not None
        for line in process.stdout:
            key, _, value = line.strip().partition("=")
            if key in {"out_time_us", "out_time_ms"}:
                current = float(value) / 1_000_000
                if callback:
                    callback(min(current, duration), duration)
        stderr = process.stderr.read() if process.stderr else ""
        return_code = process.wait()
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("COMMAND:\n" + subprocess.list2cmdline(command) + "\n\nSTDERR:\n" + stderr, encoding="utf-8")
        if return_code:
            raise RuntimeError(stderr.strip() or f"FFmpeg가 종료 코드 {return_code}로 실패했습니다.")
