from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QThread, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.models import Track
from app.services import MetadataService
from app.utils.time_utils import format_duration
from .render_worker import RenderWorker
from .track_dialog import TrackDialog


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.tracks: list[Track] = []
        self.metadata = MetadataService()
        self.thread: QThread | None = None
        self.setWindowTitle("Playlist Visual Video Maker")
        self.resize(1120, 760)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        heading = QLabel("Playlist Visual Video Maker")
        heading.setStyleSheet("font-size: 28px; font-weight: 700; color: #7046e8; margin: 12px 0;")
        layout.addWidget(heading)
        controls = QHBoxLayout()
        for text, handler in [
            ("＋ 트랙 추가", self.add_track), ("수정", self.edit_track), ("삭제", self.delete_track),
            ("↑ 위로", lambda: self.move_track(-1)), ("↓ 아래로", lambda: self.move_track(1)),
        ]:
            button = QPushButton(text)
            button.clicked.connect(handler)
            controls.addWidget(button)
        controls.addStretch()
        layout.addLayout(controls)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["순서", "곡 제목", "아티스트", "오디오", "이미지", "재생시간"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setDragDropMode(QTableWidget.InternalMove)
        layout.addWidget(self.table)
        self.summary = QLabel("총 0곡 · 총 재생시간 00:00")
        layout.addWidget(self.summary)
        options = QHBoxLayout()
        self.save_individual = QCheckBox("개별 곡 영상도 저장")
        self.make_playlist = QCheckBox("최종 플레이리스트 영상 생성")
        self.make_playlist.setChecked(True)
        options.addWidget(self.save_individual)
        options.addWidget(self.make_playlist)
        options.addStretch()
        layout.addLayout(options)
        output = QHBoxLayout()
        self.output_edit = QLineEdit(str(Path.home() / "Videos" / "Playlist"))
        choose = QPushButton("출력 폴더 선택")
        choose.clicked.connect(self.choose_output)
        self.name_edit = QLineEdit("playlist_final.mp4")
        output.addWidget(QLabel("출력 폴더"))
        output.addWidget(self.output_edit, 2)
        output.addWidget(choose)
        output.addWidget(QLabel("최종 파일명"))
        output.addWidget(self.name_edit)
        layout.addLayout(output)
        self.status = QLabel("트랙을 추가해주세요.")
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        self.render_button = QPushButton("영상 만들기")
        self.render_button.setMinimumHeight(52)
        self.render_button.setStyleSheet("background: #7046e8; color: white; font-size: 16px; font-weight: 700; border-radius: 10px;")
        self.render_button.clicked.connect(self.start_render)
        layout.addWidget(self.render_button)

    def refresh(self) -> None:
        self.table.setRowCount(len(self.tracks))
        for row, track in enumerate(self.tracks):
            track.order = row + 1
            values = [f"{row + 1:02d}", track.title, track.artist, track.audio_path.name, track.image_path.name, format_duration(track.duration)]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.summary.setText(f"총 {len(self.tracks)}곡 · 총 재생시간 {format_duration(sum(t.duration for t in self.tracks))}")

    def add_track(self) -> None:
        dialog = TrackDialog(self.metadata, parent=self)
        if dialog.exec() and dialog.track:
            self.tracks.append(dialog.track)
            self.refresh()

    def edit_track(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        dialog = TrackDialog(self.metadata, self.tracks[row], self)
        if dialog.exec() and dialog.track:
            self.tracks[row] = dialog.track
            self.refresh()

    def delete_track(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.tracks.pop(row)
            self.refresh()

    def move_track(self, direction: int) -> None:
        row = self.table.currentRow()
        target = row + direction
        if row < 0 or target < 0 or target >= len(self.tracks):
            return
        self.tracks[row], self.tracks[target] = self.tracks[target], self.tracks[row]
        self.refresh()
        self.table.selectRow(target)

    def choose_output(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "출력 폴더 선택", self.output_edit.text())
        if selected:
            self.output_edit.setText(selected)

    def start_render(self) -> None:
        if not self.tracks:
            QMessageBox.information(self, "트랙 필요", "한 곡 이상 추가해주세요.")
            return
        if not self.save_individual.isChecked() and not self.make_playlist.isChecked():
            QMessageBox.information(self, "저장 옵션 필요", "저장할 영상 옵션을 선택해주세요.")
            return
        output = Path(self.output_edit.text())
        output.mkdir(parents=True, exist_ok=True)
        self.render_button.setEnabled(False)
        self.thread = QThread(self)
        worker = RenderWorker(self.tracks.copy(), output, self.name_edit.text(), self.save_individual.isChecked(), self.make_playlist.isChecked())
        worker.moveToThread(self.thread)
        self.thread.started.connect(worker.run)
        worker.progress.connect(lambda value, stage, detail: (self.progress.setValue(value), self.status.setText(f"{stage} · {detail}")))
        worker.finished.connect(self.render_done)
        worker.failed.connect(self.render_failed)
        worker.finished.connect(self.thread.quit)
        worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(worker.deleteLater)
        self.thread.start()
        self._worker = worker

    def render_done(self, path: str) -> None:
        self.render_button.setEnabled(True)
        QMessageBox.information(self, "영상 완성", f"영상이 완성되었습니다.\n\n{path}")

    def render_failed(self, message: str) -> None:
        self.render_button.setEnabled(True)
        QMessageBox.critical(self, "영상 생성 실패", f"{message}\n\n출력 폴더의 logs 폴더를 확인해주세요.")


def run_app() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Highlight, QColor("#7046e8"))
    app.setPalette(palette)
    window = MainWindow()
    window.show()
    return app.exec()
