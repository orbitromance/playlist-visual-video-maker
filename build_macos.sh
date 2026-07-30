#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")" && pwd)"
cd "$project_root"

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt pyinstaller

npm_dir="${RUNNER_TEMP:-/tmp}/playwave-npm"
mkdir -p "$npm_dir"
cd "$npm_dir"
npm init -y >/dev/null 2>&1
npm install --no-save ffmpeg-static ffprobe-static

ffmpeg_path="$(node -p "require('ffmpeg-static')")"
ffprobe_path="$(node -p "require('ffprobe-static').path")"
chmod +x "$ffmpeg_path" "$ffprobe_path"

cd "$project_root"
python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "PlayWave" \
  --add-binary "${ffmpeg_path}:." \
  --add-binary "${ffprobe_path}:." \
  main.py

codesign --force --deep --sign - "dist/PlayWave.app"
ditto -c -k --sequesterRsrc --keepParent \
  "dist/PlayWave.app" \
  "dist/PlayWave-macOS-${RUNNER_ARCH:-unknown}.zip"
