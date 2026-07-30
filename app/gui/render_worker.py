from __future__ import annotations

import shutil
import tempfile
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from app.models import Track
from app.services import PlaylistBuilder, VideoRenderer
from app.utils.file_utils import safe_filename


class RenderWorker(QObject):
    progress = Signal(int, str, str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, tracks: list[Track], output_dir: Path, final_name: str, save_individual: bool, make_playlist: bool) -> None:
        super().__init__()
        self.tracks = tracks
        self.output_dir = output_dir
        self.final_name = final_name
        self.save_individual = save_individual
        self.make_playlist = make_playlist

    @Slot()
    def run(self) -> None:
        work_dir = Path(tempfile.mkdtemp(prefix="playlist_visual_"))
        logs = self.output_dir / "logs"
        try:
            renderer = VideoRenderer()
            clips: list[Path] = []
            total = sum(track.duration for track in self.tracks)
            elapsed_before = 0.0
            for index, track in enumerate(self.tracks, 1):
                track.order = index
                destination = (
                    self.output_dir / f"{index:02d}_{safe_filename(track.title)}.mp4"
                    if self.save_individual
                    else work_dir / f"track_{index:03d}.mp4"
                )
                def update(current: float, duration: float, base=elapsed_before, title=track.title, number=index) -> None:
                    percent = int(((base + current) / max(total, 0.01)) * 92)
                    self.progress.emit(percent, f"Track {number} / {len(self.tracks)}", f"{title} 렌더링 중")
                renderer.render(track, destination, work_dir, update, logs / f"track_{index:03d}.log")
                clips.append(destination)
                elapsed_before += track.duration
            result = clips[-1]
            if self.make_playlist:
                self.progress.emit(94, "플레이리스트 생성", "트랙 영상 연결 중")
                name = safe_filename(Path(self.final_name).stem, "playlist_final") + ".mp4"
                result = PlaylistBuilder().concatenate(
                    clips, self.output_dir / name, work_dir,
                    lambda current, duration: self.progress.emit(94 + int(current / max(duration, .01) * 6), "플레이리스트 생성", "트랙 영상 연결 중"),
                    total, logs / "concat.log",
                )
            self.progress.emit(100, "완료", result.name)
            if not self.save_individual:
                shutil.rmtree(work_dir, ignore_errors=True)
            self.finished.emit(str(result))
        except Exception as error:
            logs.mkdir(parents=True, exist_ok=True)
            (logs / "error.log").write_text(traceback.format_exc(), encoding="utf-8")
            self.failed.emit(str(error))
