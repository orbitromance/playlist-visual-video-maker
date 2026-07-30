from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models import Track
from app.utils.time_utils import format_duration

from .ffmpeg_service import FFmpegService, ProgressCallback
from .text_overlay import create_title_overlay, find_font


@dataclass(slots=True)
class RenderConfig:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    video_bitrate: str = "6M"
    audio_bitrate: str = "192k"
    preset: str = "veryfast"


class VideoRenderer:
    def __init__(self, service: FFmpegService | None = None, config: RenderConfig | None = None) -> None:
        self.service = service or FFmpegService()
        self.config = config or RenderConfig()

    def render(
        self,
        track: Track,
        output: Path,
        work_dir: Path,
        callback: ProgressCallback | None = None,
        log_path: Path | None = None,
    ) -> Path:
        track.validate()
        cfg = self.config
        overlay = work_dir / f"title_{track.order:03d}.png"
        create_title_overlay(overlay, track.title, track.artist, cfg.width, cfg.height)
        total = format_duration(track.duration).replace(":", r"\:")
        font = str(find_font(False)).replace("\\", "/").replace(":", r"\:")
        wave_w = int(cfg.width * 0.64)
        wave_h = max(60, int(cfg.height * 0.12))
        wave_y = int(cfg.height * 0.72)
        bar_x = int(cfg.width * 0.18)
        bar_y = int(cfg.height * 0.89)
        bar_w = int(cfg.width * 0.64)
        bar_h = max(5, int(cfg.height * 0.008))
        time_size = max(18, int(cfg.height * 0.025))
        progress_segments = 80
        segment_width = bar_w / progress_segments
        progress_filters = "".join(
            f"drawbox=x={bar_x + int(index * segment_width)}:y={bar_y}:"
            f"w={max(2, int(segment_width + 1))}:h={bar_h}:color=0xB99CFFFF:t=fill:"
            f"enable='gte(t,{track.duration * index / progress_segments:.6f})',"
            for index in range(progress_segments)
        )
        filter_graph = (
            f"[1:v]scale={cfg.width}:{cfg.height}:force_original_aspect_ratio=increase,"
            f"crop={cfg.width}:{cfg.height},gblur=sigma=28,eq=brightness=-0.28[bg];"
            f"[1:v]scale={int(cfg.width*0.72)}:{int(cfg.height*0.48)}:force_original_aspect_ratio=decrease[cover];"
            f"[bg][cover]overlay=(W-w)/2:{int(cfg.height*0.04)}[art];"
            f"[art][2:v]overlay=0:0[base];"
            f"[0:a]asplit=2[aout][wavesrc];"
            f"[wavesrc]showwaves=s={wave_w}x{wave_h}:mode=line:colors=0xA987FFFF:rate={cfg.fps},format=rgba[wave];"
            f"[base][wave]overlay=(W-w)/2:{wave_y}[v0];"
            f"[v0]drawbox=x={bar_x}:y={bar_y}:w={bar_w}:h={bar_h}:color=white@0.22:t=fill,"
            f"{progress_filters}"
            f"drawtext=fontfile='{font}':text='%{{eif\\:floor(t/60)\\:d\\:2}}\\:%{{eif\\:mod(t,60)\\:d\\:2}}':"
            f"x={bar_x}:y={bar_y+18}:fontsize={time_size}:fontcolor=white@0.88,"
            f"drawtext=fontfile='{font}':text='{total}':x={bar_x+bar_w}-text_w:y={bar_y+18}:fontsize={time_size}:fontcolor=white@0.88,"
            "format=yuv420p[vout]"
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        args = [
            "-i", str(track.audio_path),
            "-loop", "1", "-framerate", str(cfg.fps), "-i", str(track.image_path),
            "-loop", "1", "-framerate", str(cfg.fps), "-i", str(overlay),
            "-filter_complex", filter_graph,
            "-map", "[vout]", "-map", "[aout]",
            "-t", f"{track.duration:.6f}",
            "-r", str(cfg.fps),
            "-c:v", "libx264", "-preset", cfg.preset, "-b:v", cfg.video_bitrate,
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", cfg.audio_bitrate,
            "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
            str(output),
        ]
        self.service.run_with_progress(args, track.duration, callback, log_path)
        return output
