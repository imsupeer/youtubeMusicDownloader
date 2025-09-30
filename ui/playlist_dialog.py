from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QPushButton,
    QHBoxLayout,
    QHeaderView,
)
from PySide6.QtCore import Qt


class PlaylistDialog(QDialog):
    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.setWindowTitle("Playlist Selection")
        self.resize(700, 420)
        self.items = items or []
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Download", "Title"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setRowCount(len(self.items))
        for i, it in enumerate(self.items):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Checked)
            self.table.setItem(i, 0, chk)
            self.table.setItem(i, 1, QTableWidgetItem(it.get("title") or ""))
        btn_select_all = QPushButton("Select All")
        btn_select_none = QPushButton("Select None")
        btn_ok = QPushButton("Download Selected")
        btn_cancel = QPushButton("Cancel")
        btn_select_all.clicked.connect(self.select_all)
        btn_select_none.clicked.connect(self.select_none)
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        hl = QHBoxLayout()
        hl.addWidget(btn_select_all)
        hl.addWidget(btn_select_none)
        hl.addStretch(1)
        hl.addWidget(btn_cancel)
        hl.addWidget(btn_ok)
        lay = QVBoxLayout(self)
        lay.addWidget(self.table)
        lay.addLayout(hl)

    def selected_items(self):
        out = []
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).checkState() == Qt.Checked:
                out.append(self.items[i])
        return out

    def select_all(self):
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setCheckState(Qt.Checked)

    def select_none(self):
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setCheckState(Qt.Unchecked)
