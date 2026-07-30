from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def find_font(bold: bool = False) -> Path:
    env_font = os.environ.get("PVM_FONT")
    candidates = [
        env_font,
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "malgunbd.ttf" if bold else "malgun.ttf"),
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise RuntimeError("사용 가능한 글꼴을 찾지 못했습니다. PVM_FONT 환경변수로 폰트 경로를 지정해주세요.")


def _fit_font(draw: ImageDraw.ImageDraw, text: str, font_path: Path, max_size: int, max_width: int) -> ImageFont.FreeTypeFont:
    for size in range(max_size, 23, -2):
        font = ImageFont.truetype(str(font_path), size)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
    return ImageFont.truetype(str(font_path), 24)


def create_title_overlay(path: Path, title: str, artist: str, width: int, height: int) -> None:
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    title_font = _fit_font(draw, title, find_font(True), max(36, int(height * 0.065)), int(width * 0.78))
    artist_font = _fit_font(draw, artist, find_font(False), max(22, int(height * 0.032)), int(width * 0.72))
    title_box = draw.textbbox((0, 0), title, font=title_font)
    artist_box = draw.textbbox((0, 0), artist, font=artist_font)
    draw.text(((width - (title_box[2] - title_box[0])) / 2, height * 0.53), title, font=title_font, fill=(255, 255, 255, 255))
    draw.text(((width - (artist_box[2] - artist_box[0])) / 2, height * 0.61), artist, font=artist_font, fill=(220, 216, 229, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
