from math import ceil

from PyQt5 import QtWidgets, QtCore


class ResultTableWidget(QtWidgets.QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                           QtWidgets.QSizePolicy.Minimum)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setColumnCount(4)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.setShowGrid(False)

    def setResults(self, results):
        def enumerate(it, start=0, step=1):
            for i in it:
                yield (start, i)
                start += step

        rowIdx = -1
        colCount = self.columnCount()
        rowCount = ceil(len(results) / self.columnCount() * 2)
        self.setRowCount(rowCount)

        for colIdx, (k, v) in enumerate(results.items(), start=0, step=2):
            colIdx %= colCount
            if colIdx <= 1:
                rowIdx += 1

            v = f"{v:.2f}"

            self.setItem(rowIdx, colIdx, QtWidgets.QTableWidgetItem(k))
            self.setItem(rowIdx, colIdx + 1, QtWidgets.QTableWidgetItem(v))

        self.resizeColumnsToContents()

    def setTableSize(self):
        width = self.verticalHeader().width()
        width += self.horizontalHeader().length()
        if self.verticalScrollBar().isVisible():
            width += self.verticalScrollBar().width()
        width += self.frameWidth() * 4
        self.setFixedWidth(width)

        height = self.verticalHeader().height()
        if self.horizontalScrollBar().isVisible():
            height += self.horizontalScrollBar().height()

        self.setFixedHeight(height)

    def resizeEvent(self, event):
        self.setTableSize()
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.destroyed.emit()
