from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ui.styles import asset_path


class PlaylistDialog(QDialog):
    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.setWindowTitle("Select Tracks")
        self.setMinimumSize(720, 460)
        self.resize(720, 460)
        self.items = items or []

        icon_file = asset_path("icon.png")
        if icon_file.exists():
            self.setWindowIcon(QIcon(str(icon_file)))

        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Download", "Title"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setRowCount(len(self.items))

        for i, item in enumerate(self.items):
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Checked)
            self.table.setItem(i, 0, checkbox)
            self.table.setItem(i, 1, QTableWidgetItem(item.get("title") or "Untitled"))

        btn_select_all = QPushButton("Select All")
        btn_select_all.setObjectName("secondaryButton")
        btn_select_all.setCursor(Qt.PointingHandCursor)
        btn_select_none = QPushButton("Select None")
        btn_select_none.setObjectName("secondaryButton")
        btn_select_none.setCursor(Qt.PointingHandCursor)
        btn_ok = QPushButton("Download Selected")
        btn_ok.setObjectName("primaryButton")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("secondaryButton")
        btn_cancel.setCursor(Qt.PointingHandCursor)

        btn_select_all.clicked.connect(self.select_all)
        btn_select_none.clicked.connect(self.select_none)
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addWidget(btn_select_all)
        actions.addWidget(btn_select_none)
        actions.addStretch(1)
        actions.addWidget(btn_cancel)
        actions.addWidget(btn_ok)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        layout.addWidget(self.table, 1)
        layout.addLayout(actions)

    def selected_items(self):
        selected = []
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).checkState() == Qt.Checked:
                selected.append(self.items[i])
        return selected

    def select_all(self):
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setCheckState(Qt.Checked)

    def select_none(self):
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setCheckState(Qt.Unchecked)
