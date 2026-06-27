import os
import queue
import sys
import threading

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.downloader import download
from core.models import DownloadTask
from core.playlist import probe
from ui.playlist_dialog import PlaylistDialog
from ui.styles import asset_path, load_stylesheet


class Signals(QObject):
    progress = Signal(str, float)
    status = Signal(str)


class DownloadWorker(threading.Thread):
    def __init__(self, tasks, signals):
        super().__init__(daemon=True)
        self.tasks = tasks
        self.signals = signals
        self.stop_flag = False

    def run(self):
        while not self.stop_flag:
            try:
                task = self.tasks.get(timeout=0.2)
            except queue.Empty:
                continue

            def hook(d):
                if d.get("status") == "downloading":
                    percent_str = d.get("_percent_str", "0").strip().replace("%", "")
                    try:
                        percent = float(percent_str)
                    except ValueError:
                        percent = 0.0
                    self.signals.progress.emit(d.get("filename", ""), percent)

            try:
                download(task, hook)
                self.signals.status.emit("done")
            except Exception as e:
                self.signals.status.emit("error:" + str(e))
            finally:
                self.tasks.task_done()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube MP3 Downloader")
        self.setMinimumSize(860, 600)
        self.resize(860, 600)

        icon_file = asset_path("icon.png")
        if icon_file.exists():
            self.setWindowIcon(QIcon(str(icon_file)))

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Paste a YouTube video or playlist URL…")
        self.btn_probe = QPushButton("Detect")
        self.btn_probe.setObjectName("secondaryButton")
        self.btn_probe.setCursor(Qt.PointingHandCursor)

        self.quality = self._make_quality_selector()
        self.outdir_btn = QPushButton("Choose Folder")
        self.outdir_btn.setObjectName("secondaryButton")
        self.outdir_btn.setCursor(Qt.PointingHandCursor)
        self.outdir_label = QLabel("")
        self.outdir_label.setObjectName("statusLabel")

        self.result_label = QLabel("Paste a URL and click Detect to get started.")
        self.result_label.setObjectName("statusLabel")
        self.result_label.setWordWrap(True)

        self.queue_list = QListWidget()
        self.queue_list.setAlternatingRowColors(True)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)

        self.btn_download = QPushButton("Download")
        self.btn_download.setObjectName("primaryButton")
        self.btn_download.setCursor(Qt.PointingHandCursor)

        self.footer_status = QLabel("Ready")
        self.footer_status.setObjectName("statusLabel")

        header = self._build_header()
        source_group = self._build_source_group()
        output_group = self._build_output_group()
        queue_group = self._build_queue_group()
        footer = self._build_footer()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(header)
        layout.addSpacing(8)

        body = QVBoxLayout()
        body.setContentsMargins(24, 16, 24, 16)
        body.setSpacing(16)
        body.addWidget(source_group)
        body.addWidget(output_group)
        body.addWidget(self.result_label)
        body.addWidget(queue_group, 1)
        body.addWidget(self.progress)
        body.addWidget(self.btn_download)
        layout.addLayout(body, 1)
        layout.addWidget(footer)

        self.btn_probe.clicked.connect(self.on_probe)
        self.outdir_btn.clicked.connect(self.on_choose_outdir)
        self.btn_download.clicked.connect(self.on_download)

        self.tasks = queue.Queue()
        self.signals = Signals()
        self.worker = DownloadWorker(self.tasks, self.signals)
        self.worker.start()
        self.signals.progress.connect(self.on_progress)
        self.signals.status.connect(self.on_status)

        self.items_to_download = []
        self.outdir = os.path.expanduser("~/Downloads")
        self.outdir_label.setText(self.outdir)
        self._set_status("Ready - choose an output folder and paste a URL.", "info")

    def _make_quality_selector(self):
        from PySide6.QtWidgets import QComboBox

        combo = QComboBox()
        for kbps in ("128", "192", "256", "320"):
            combo.addItem(f"{kbps} kbps", kbps)
        combo.setCurrentIndex(1)
        combo.setCursor(Qt.PointingHandCursor)
        return combo

    def _build_header(self):
        frame = QFrame()
        frame.setObjectName("headerFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 18, 24, 18)

        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel("YouTube MP3 Downloader")
        title.setObjectName("appTitle")
        subtitle = QLabel("Convert videos and playlists to tagged MP3 files")
        subtitle.setObjectName("appSubtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)

        layout.addLayout(titles)
        layout.addStretch(1)
        return frame

    def _build_source_group(self):
        group = QGroupBox("Source")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        row = QHBoxLayout()
        row.addWidget(self.url_edit, 1)
        row.addWidget(self.btn_probe)
        layout.addLayout(row)
        return group

    def _build_output_group(self):
        group = QGroupBox("Output")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        quality_row = QHBoxLayout()
        quality_label = QLabel("Quality")
        quality_label.setObjectName("sectionLabel")
        quality_row.addWidget(quality_label)
        quality_row.addWidget(self.quality)
        quality_row.addStretch(1)
        layout.addLayout(quality_row)

        folder_row = QHBoxLayout()
        folder_row.addWidget(self.outdir_btn)
        folder_row.addWidget(self.outdir_label, 1)
        layout.addLayout(folder_row)
        return group

    def _build_queue_group(self):
        group = QGroupBox("Download Queue")
        layout = QVBoxLayout(group)
        layout.addWidget(self.queue_list)
        return group

    def _build_footer(self):
        frame = QFrame()
        frame.setObjectName("footerFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 10, 24, 10)
        layout.addWidget(self.footer_status)
        layout.addStretch(1)
        version = QLabel("v2.0 · PySide6 · Pydantic · yt-dlp")
        version.setObjectName("appSubtitle")
        layout.addWidget(version)
        return frame

    def _set_status(self, message, kind="info"):
        self.footer_status.setText(message)
        self.result_label.setProperty("status", kind)
        self.result_label.style().unpolish(self.result_label)
        self.result_label.style().polish(self.result_label)

    def on_choose_outdir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self.outdir
        )
        if directory:
            self.outdir = directory
            self.outdir_label.setText(directory)
            self._set_status(f"Output folder set to {directory}", "info")

    def on_probe(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(
                self, "Missing URL", "Enter a YouTube video or playlist URL."
            )
            return
        self._set_status("Detecting URL…", "info")
        self.btn_probe.setEnabled(False)
        try:
            info = probe(url)
        except Exception as e:
            QMessageBox.critical(self, "Detection Failed", str(e))
            self._set_status("Could not read the URL.", "error")
            self.btn_probe.setEnabled(True)
            return
        finally:
            self.btn_probe.setEnabled(True)

        if info.type == "single":
            title = info.title or "Untitled"
            self.result_label.setText(f"Single video detected: {title}")
            self.items_to_download = [e.model_dump() for e in info.entries]
            self._set_status("Ready to download 1 track.", "success")
        elif info.type == "playlist":
            entries = [e.model_dump() for e in info.entries]
            dialog = PlaylistDialog(self, entries)
            if dialog.exec() == dialog.Accepted:
                self.items_to_download = dialog.selected_items()
                count = len(self.items_to_download)
                self.result_label.setText(f"Playlist - {count} track(s) selected")
                self._set_status(f"{count} track(s) queued from playlist.", "success")
            else:
                self.items_to_download = []
                self.result_label.setText("Playlist selection cancelled.")
                self._set_status("Selection cancelled.", "info")
        else:
            self.result_label.setText("Unsupported URL type.")
            self.items_to_download = []
            self._set_status("Unsupported URL.", "error")

        self.queue_list.clear()
        for item in self.items_to_download:
            label = item.get("title") or item.get("url") or "Untitled"
            self.queue_list.addItem(QListWidgetItem(label))
        self.progress.setValue(0)

    def on_download(self):
        if not self.items_to_download:
            QMessageBox.information(self, "Nothing to Download", "Detect a URL first.")
            return
        if not self.outdir:
            QMessageBox.information(
                self, "No Output Folder", "Choose an output folder."
            )
            return

        kbps = int(self.quality.currentData())
        queued = 0
        for item in self.items_to_download:
            url = item.get("url")
            if not url:
                continue
            task = DownloadTask(url=url, bitrate_kbps=kbps, outdir=self.outdir)
            self.tasks.put(task)
            queued += 1

        self.progress.setValue(0)
        self._set_status(f"Downloading {queued} track(s)…", "info")
        self.btn_download.setEnabled(False)

    def on_progress(self, filename, percent):
        self.progress.setValue(int(percent))
        if filename:
            name = os.path.basename(filename)
            self._set_status(f"Downloading {name} - {int(percent)}%", "info")

    def on_status(self, status):
        if status == "done":
            if self.tasks.empty():
                self.progress.setValue(100)
                self._set_status("All downloads complete.", "success")
                self.btn_download.setEnabled(True)
        elif status.startswith("error:"):
            QMessageBox.critical(self, "Download Error", status[6:])
            self._set_status("A download failed. See error dialog.", "error")
            self.btn_download.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(load_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
