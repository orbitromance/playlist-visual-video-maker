from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout,
    QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)

from app.models import Track
from app.services import MetadataService


class TrackDialog(QDialog):
    def __init__(self, metadata: MetadataService, track: Track | None = None, parent=None) -> None:
        super().__init__(parent)
        self.metadata = metadata
        self.track = track
        self.setWindowTitle("트랙 수정" if track else "새 트랙 추가")
        self.setMinimumWidth(620)
        self.audio_edit = QLineEdit(str(track.audio_path) if track else "")
        self.image_edit = QLineEdit(str(track.image_path) if track else "")
        self.title_edit = QLineEdit(track.title if track else "")
        self.artist_edit = QLineEdit(track.artist if track else "")
        form = QFormLayout()
        form.addRow("오디오 파일", self._picker(self.audio_edit, True))
        form.addRow("이미지 파일", self._picker(self.image_edit, False))
        form.addRow("곡 제목", self.title_edit)
        form.addRow("아티스트", self.artist_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _picker(self, edit: QLineEdit, audio: bool) -> QHBoxLayout:
        button = QPushButton("찾아보기")
        button.clicked.connect(lambda: self._choose(edit, audio))
        layout = QHBoxLayout()
        layout.addWidget(edit)
        layout.addWidget(button)
        return layout

    def _choose(self, edit: QLineEdit, audio: bool) -> None:
        pattern = "오디오 (*.mp3 *.wav *.m4a *.aac)" if audio else "이미지 (*.jpg *.jpeg *.png)"
        path, _ = QFileDialog.getOpenFileName(self, "파일 선택", "", pattern)
        if path:
            edit.setText(path)

    def accept(self) -> None:
        try:
            audio = Path(self.audio_edit.text().strip())
            image = Path(self.image_edit.text().strip())
            candidate = Track(
                audio_path=audio,
                image_path=image,
                title=self.title_edit.text().strip(),
                artist=self.artist_edit.text().strip(),
                duration=self.metadata.duration(audio),
            )
            candidate.validate()
            self.track = candidate
        except Exception as error:
            QMessageBox.warning(self, "트랙을 추가할 수 없습니다", str(error))
            return
        super().accept()
