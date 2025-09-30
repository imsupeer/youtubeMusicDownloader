import sys, os, threading, queue
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QComboBox,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QObject
from core.playlist import probe
from core.downloader import DownloadTask, download
from ui.playlist_dialog import PlaylistDialog


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
                t = self.tasks.get(timeout=0.2)
            except queue.Empty:
                continue

            def hook(d):
                if d.get("status") == "downloading":
                    p = d.get("_percent_str", "0").strip().replace("%", "")
                    try:
                        pv = float(p)
                    except:
                        pv = 0.0
                    self.signals.progress.emit(d.get("filename", ""), pv)

            try:
                download(t, hook)
                self.signals.status.emit("done")
            except Exception as e:
                self.signals.status.emit("error:" + str(e))
            finally:
                self.tasks.task_done()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube MP3 Downloader")
        self.resize(800, 520)
        self.url_edit = QLineEdit()
        self.btn_probe = QPushButton("Detect")
        self.quality = QComboBox()
        for q in ["128", "192", "256", "320"]:
            self.quality.addItem(q)
        self.outdir_btn = QPushButton("Choose Folder")
        self.outdir_label = QLabel("")
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.queue_list = QListWidget()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.btn_download = QPushButton("Download")
        top = QHBoxLayout()
        top.addWidget(QLabel("URL"))
        top.addWidget(self.url_edit, 1)
        top.addWidget(self.btn_probe)
        ql = QHBoxLayout()
        ql.addWidget(QLabel("MP3 kbps"))
        ql.addWidget(self.quality)
        ql.addStretch(1)
        outl = QHBoxLayout()
        outl.addWidget(self.outdir_btn)
        outl.addWidget(self.outdir_label, 1)
        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addLayout(ql)
        lay.addLayout(outl)
        lay.addWidget(self.result_label)
        lay.addWidget(QLabel("Queue"))
        lay.addWidget(self.queue_list, 1)
        lay.addWidget(self.progress)
        lay.addWidget(self.btn_download)
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

    def on_choose_outdir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.outdir)
        if d:
            self.outdir = d
            self.outdir_label.setText(d)

    def on_probe(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Enter a URL")
            return
        try:
            info = probe(url)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        if info["type"] == "single":
            self.result_label.setText(
                "Single video detected: " + (info.get("title") or "")
            )
            self.items_to_download = info["entries"]
        elif info["type"] == "playlist":
            dlg = PlaylistDialog(self, info["entries"])
            if dlg.exec() == dlg.Accepted:
                self.items_to_download = dlg.selected_items()
                self.result_label.setText(
                    "Playlist items selected: " + str(len(self.items_to_download))
                )
            else:
                self.items_to_download = []
                self.result_label.setText("Selection cancelled")
        else:
            self.result_label.setText("Unsupported URL")
            self.items_to_download = []
        self.queue_list.clear()
        for it in self.items_to_download:
            item = QListWidgetItem(it.get("title") or it.get("url") or "")
            self.queue_list.addItem(item)

    def on_download(self):
        if not self.items_to_download:
            QMessageBox.information(self, "Info", "No items to download")
            return
        if not self.outdir:
            QMessageBox.information(self, "Info", "Choose output folder")
            return
        kbps = int(self.quality.currentText())
        for it in self.items_to_download:
            url = it.get("url")
            if not url:
                continue
            t = DownloadTask(url=url, bitrate_kbps=kbps, outdir=self.outdir)
            self.tasks.put(t)
        self.progress.setValue(0)

    def on_progress(self, filename, percent):
        self.progress.setValue(int(percent))

    def on_status(self, s):
        if s == "done":
            if self.tasks.empty():
                self.progress.setValue(100)
        elif s.startswith("error:"):
            QMessageBox.critical(self, "Error", s[6:])


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
