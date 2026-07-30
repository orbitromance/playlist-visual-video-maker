$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

$VendorDir = Join-Path $ProjectRoot "vendor\ffmpeg"
New-Item -ItemType Directory -Force -Path $VendorDir | Out-Null

$Archive = Join-Path $env:RUNNER_TEMP "ffmpeg.zip"
$Extracted = Join-Path $env:RUNNER_TEMP "ffmpeg"
Invoke-WebRequest `
  -Uri "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip" `
  -OutFile $Archive
Expand-Archive -Path $Archive -DestinationPath $Extracted -Force

$Ffmpeg = Get-ChildItem $Extracted -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
$Ffprobe = Get-ChildItem $Extracted -Recurse -Filter "ffprobe.exe" | Select-Object -First 1
if (-not $Ffmpeg -or -not $Ffprobe) {
  throw "FFmpeg archive did not contain ffmpeg.exe and ffprobe.exe."
}

Copy-Item $Ffmpeg.FullName (Join-Path $VendorDir "ffmpeg.exe") -Force
Copy-Item $Ffprobe.FullName (Join-Path $VendorDir "ffprobe.exe") -Force

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onedir `
  --windowed `
  --name "PlaylistVisualMaker" `
  --add-binary "$VendorDir\ffmpeg.exe;." `
  --add-binary "$VendorDir\ffprobe.exe;." `
  main.py

$Readme = @"
Playlist Visual Video Maker - Windows Test Build

1. Keep this entire folder together.
2. Double-click PlaylistVisualMaker.exe.
3. No Python or FFmpeg installation is required.

Windows may show a SmartScreen warning because this test build is not
code-signed. Check the publisher and file source before choosing to run it.
"@
Set-Content -Path "dist\PlaylistVisualMaker\README_FIRST.txt" -Value $Readme -Encoding UTF8
