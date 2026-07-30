# Playlist Visual Video Maker

여러 곡의 오디오와 이미지를 등록해 개별 visualizer MP4와 하나의 긴 플레이리스트 MP4를 만드는 Windows 우선 데스크톱 앱입니다.

## Windows 무설치판 실행법

1. GitHub Actions에서 생성된 `PlaylistVisualMaker-Windows.zip`을 내려받습니다.
2. ZIP을 원하는 폴더에 **전체 압축 해제**합니다.
3. `PlaylistVisualMaker.exe`를 더블클릭합니다.

Python, PySide6, FFmpeg를 따로 설치할 필요가 없습니다. EXE 하나만 다른 곳으로
옮기지 말고 압축 해제된 폴더를 통째로 유지하세요.

## 사용법

1. `＋ 트랙 추가`를 눌러 오디오, 이미지, 제목, 아티스트를 입력합니다.
2. 필요한 곡을 모두 추가하고 위/아래 버튼으로 순서를 정합니다.
3. 개별 곡 영상과 최종 플레이리스트 영상 중 원하는 항목을 체크합니다.
4. 출력 폴더와 최종 파일명을 지정하고 `영상 만들기`를 누릅니다.

기본 출력은 1920×1080, 30fps, H.264, AAC MP4입니다. waveform은 FFmpeg `showwaves`가 실제 음원 신호에서 생성하며 progress bar와 별개입니다. 한글 제목은 Windows 기본 맑은 고딕을 Pillow로 이미지화해 합성합니다.

## 지원 파일

- 오디오: MP3, WAV, M4A, AAC
- 이미지: JPG, JPEG, PNG

## 오류 확인

렌더링 실패 시 출력 폴더 아래 `logs` 폴더에 FFmpeg 명령과 오류 내용이 저장됩니다. 원본 오디오와 이미지는 읽기만 하며 수정하거나 삭제하지 않습니다.

## 개발자용 테스트

```bash
python -m pip install Pillow pytest
python tests/create_test_data.py
pytest -q
```

## Windows 배포판 빌드

저장소의 Actions 탭에서 `Build Windows EXE`를 실행하면 Windows 환경에서
PyInstaller onedir 배포판을 만들고 `PlaylistVisualMaker-Windows` artifact로
업로드합니다. 배포판에는 FFmpeg와 ffprobe가 포함됩니다.
