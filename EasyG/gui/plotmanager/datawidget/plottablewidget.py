from PyQt5 import QtWidgets, QtCore


class PlotTableWidget(QtWidgets.QTableWidget):
    # columnName, rowName, checkState
    PlotItemClicked = QtCore.pyqtSignal(str, str, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setMinimumWidth(350)
        self.itemClicked.connect(self.onItemClicked)

    def columnIndexOf(self, columnName):
        for colIdx in range(self.columnCount()):
            if self.horizontalHeaderItem(colIdx).text() == columnName:
                break

        else:
            raise ValueError(f"No such column: {columnName}")

        return colIdx

    def rowIndexOf(self, rowName):
        for rowIdx in range(self.rowCount()):
            if self.verticalHeaderItem(rowIdx).text() == rowName:
                break

        else:
            raise ValueError(f"No such row: {rowName}")

        return rowIdx

    def containsRow(self, rowName):
        for rowIdx in range(self.rowCount()):
            if self.verticalHeaderItem(rowIdx).text() == rowName:
                result = True
                break

        else:
            result = False

        return result

    def containsColumn(self, columnName):
        for colIdx in range(self.columnCount()):
            if self.horizontalHeaderItem(colIdx).text() == columnName:
                result = True
                break

        else:
            result = False

        return result

    def addColumn(self, columnName):
        if self.containsColumn(columnName):
            raise ValueError(f"Can't add dublicate column: {columnName}")

        # current columnCount will be last index of table with columnCount + 1
        lastColIdx = self.columnCount()
        self.setColumnCount(lastColIdx + 1)

        headerItem = QtWidgets.QTableWidgetItem(columnName)
        self.setHorizontalHeaderItem(lastColIdx, headerItem)

        for rowIdx in range(self.rowCount()):
            item = QtWidgets.QTableWidgetItem()
            item.setFlags(
                QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)

            self.setItem(rowIdx, lastColIdx, item)

        self.resizeColumnsToContents()

    def addRow(self, rowName):
        if self.containsRow(rowName):
            raise ValueError(f"Can't add dublicate row: {rowName}")

        # current rowCount will be last index of table with rowCount + 1
        lastRowIdx = self.rowCount()
        self.setRowCount(lastRowIdx + 1)

        headerItem = QtWidgets.QTableWidgetItem(rowName)
        self.setVerticalHeaderItem(lastRowIdx, headerItem)

        for colIdx in range(self.columnCount()):
            item = QtWidgets.QTableWidgetItem()
            item.setFlags(
                QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)

            self.setItem(lastRowIdx, colIdx, item)

    def removeColumn(self, columnName):
        super().removeColumn(self.columnIndexOf(columnName))

    def removeRow(self, rowName):
        super().removeRow(self.rowIndexOf(rowName))

    def setCheckState(self, colIdx, rowIdx, state):
        self.item(rowIdx, colIdx).setCheckState(state)

    def setCheckStateByName(self, columnName=None, rowName=None,
                            state=QtCore.Qt.CheckState.Unchecked):
        if (columnName and rowName) is None:
            colIdxs = range(self.columnCount())
            rowIdx = range(self.rowCount())

        elif columnName is None:
            colIdxs = range(self.columnCount())
            rowIdxs = [self.rowIndexOf(rowName)]

        elif rowName is None:
            colIdxs = [self.columnIndexOf(columnName)]
            rowIdxs = range(self.rowCount())

        else:
            colIdxs = [self.columnIndexOf(columnName)]
            rowIdxs = [self.rowIndexOf(rowName)]

        for colIdx in colIdxs:
            for rowIdx in rowIdxs:
                self.setCheckState(colIdx, rowIdx, state)

    def onItemClicked(self, item):
        colName = self.horizontalHeaderItem(item.column()).text()
        rowName = self.verticalHeaderItem(item.row()).text()

        self.PlotItemClicked.emit(colName, rowName, item.checkState())

    def updateRowName(self, previousName, newName):
        for idx in range(self.rowCount()):
            if (item := self.verticalHeaderItem(idx)).text() == previousName:
                item.setText(newName)

    def updateColumnName(self, previousName, newName):
        for idx in range(self.columnCount()):
            if (item := self.horizontalHeaderItem(idx)).text() == previousName:
                item.setText(newName)

        self.resizeColumnsToContents()
