from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt

import pyqtgraph as pg

from EasyG.config import setPyqtgraphConfig


setPyqtgraphConfig()

_availableMarkers = [
    "None",
    "o",
    "s",
    "t",
    "d",
    "+",
    "t1",
    "t2",
    "t3",
    "p",
    "h",
    "star",
    "x",
    "arrow_up",
    "arrow_right",
    "arrow_down",
    "arrow_left",
    "crosshair"
]


class GlobalPlotDataItem(pg.PlotDataItem):
    def __init__(self, *, ancestor=None, **kwargs):
        super().__init__(clickable=True, **kwargs)

        self._kwargs = kwargs
        self._ancestor = None
        self.kids = []
        self.setAncestor(ancestor)

        self._plotClickedContextMenu = self._getPlotClickedContextMenu()
        self.sigClicked.connect(self.onPlotClicked)

        self.colorDialog = QtWidgets.QColorDialog()

    def ancestor(self):
        return self._ancestor

    def setAncestor(self, ancestor):
        if (myAncestor := self.ancestor()) is not None:
            myAncestor.kids.remove(self)

        if ancestor is not None:
            ancestor.kids.append(self)

        self._ancestor = ancestor

    def copy(self, **kwargs):
        kwargs = dict(self._kwargs, **kwargs)

        new = type(self)(ancestor=self, **kwargs)

        return new

    def deleteLater(self):
        if self.hasRelatives():
            ancestor = self.ancestor()
            if ancestor is None:
                ancestor = self.kids[0]
                ancestor.setAncestor(None)

            for kid in self.kids:
                kid.setAncestor(ancestor)

        self.setAncestor(None)
        super().deleteLater()

    def globalAncestor(self):
        return (self if self.isGlobalAncestor()
                else self.ancestor().globalAncestor())

    def isGlobalAncestor(self):
        return self.ancestor() is None

    def hasKids(self):
        return bool(self.kids)

    def hasRelatives(self):
        return self.hasKids() or not self.isGlobalAncestor()

    def isRelatedTo(self, item, *, _propagte=False):
        result = False

        if self.isGlobalAncestor():
            if item is self:
                result = True

            else:
                for kid in self.kids:
                    result = kid.isRelatedTo(item, _propagte=True)
                    if result:
                        break

        else:
            if _propagte:
                if item is self:
                    result = True

                else:
                    for kid in self.kids:
                        result = kid.isRelatedTo(item)
                        if result:
                            break

            else:
                result = self.ancestor().isRelatedTo(item)

        return result

    def setGlobalData(self, *, _propagte=False, **kwargs):
        """Set data for all related dataItems, starting at the
        global Ancestor and working our way down the tree"""

        if self.isGlobalAncestor():
            self._kwargs = kwargs
            self.setData(**self._kwargs)

            for kid in self.kids:
                kid.setGlobalData(_propagte=True, **kwargs)

        else:
            if _propagte:
                # we are not the global Ancestor, but we are told to update
                # ourself from the global Ancestor
                self._kwargs = kwargs
                self.setData(**self._kwargs)

                for kid in self.kids:
                    kid.setGlobalData(_propagte=True, **kwargs)

            else:
                # we are not the global Ancestor yet so keep looking
                self.ancestor().setGlobalData(**kwargs)

    def _getPlotClickedContextMenu(self):
        menu = QtWidgets.QMenu()
        self._plotClickedEditLineColor = menu.addAction("Edit line color")
        self._plotClickedEditMarkerColor = menu.addAction("Edit marker color")
        self._plotClickedEditMarkerSymbol = menu.addAction("Edit symbol")

        return menu

    def onPlotClicked(self):
        action = self._plotClickedContextMenu.exec(QtGui.QCursor.pos())

        if action == self._plotClickedEditLineColor:
            color = self.colorDialog.getColor()

            if color.isValid():
                self.setPen(color)

        elif action == self._plotClickedEditMarkerColor:
            color = self.colorDialog.getColor()

            if color.isValid():
                self.setSymbolBrush()

        elif action == self._plotClickedEditMarkerSymbol:
            marker, isValid = QtWidgets.QInputDialog.getItem(
                None,
                "Set line marker",
                "Select line marker:",
                _availableMarkers,
                editable=False)

            if isValid:
                if marker == "None":
                    marker = None
                self.setSymbol(marker)


class ECGPlotDataItem(GlobalPlotDataItem):
    def estimateSampleRate(self):
        x = self.getData()[0]

        if x:
            rate = len(x) / (x[-1] - x[0]) * 1000

        else:
            rate = 0

        # assuming millisecond timestamps
        return rate


class ECGPlotWidget(pg.PlotWidget):
    # self
    TitleChangeRequest = QtCore.pyqtSignal(object)
    # x0, x1 coordinates of self._ROI
    NewROICoordinates = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None, background='default',
                 **kargs):
        pg.GraphicsView.__init__(self, parent, background=background)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)

        self.enableMouse(False)

        self.plotItem = pg.PlotItem(**kargs)
        self.setCentralItem(self.plotItem)

        for m in ['autoRange', 'clear', 'setAxisItems', 'setXRange',
                  'setYRange', 'setRange', 'setAspectLocked',
                  'setMouseEnabled', 'setXLink', 'setYLink', 'enableAutoRange',
                  'disableAutoRange', 'setLimits', 'register', 'unregister',
                  'viewRect']:
            setattr(self, m, getattr(self.plotItem, m))

        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)

        self.addLegend()

        # region of interest, activated by double clicking
        self._ROI = pg.RectROI(pos=(0, 0), size=(0, 0),
                               pen=pg.mkPen("g", width=1.5, style=Qt.DashLine),
                               invertible=True)
        self._ROI.sigRegionChangeFinished.connect(self.emitROICoordinates)
        self._ROI.hide()
        self.addItem(self._ROI)

        # connection of the setROISize slot upon double click
        self._setROISizeConnection = None

        self.titleLabelContextMenu = self._getTitleLabelContextMenu()

        # inject a contextMenuEventHandler into the titleLabel so we can catch
        # right click events
        self.plotItem.titleLabel.contextMenuEvent = self._showTitleContextMenu

    def _showTitleContextMenu(self, event):
        event.accept()
        action = self.titleLabelContextMenu.exec(QtGui.QCursor.pos())

        if action == self.titleLabelEditTextAction:
            self.TitleChangeRequest.emit(self)

    def getTitle(self):
        return self.plotItem.titleLabel.text

    def setTitle(self, title):
        self.plotItem.setTitle(title)

    def _getTitleLabelContextMenu(self):
        menu = QtWidgets.QMenu(self)
        self.titleLabelEditTextAction = menu.addAction("Edit Title")

        return menu

    def mouseDoubleClickEvent(self, event):
        event.accept()

        self._ROI.setSize((0, 0))

        pos = self.getViewBox().mapSceneToView(event.pos())
        self._ROI.setPos(pos)
        self._setROISizeConnection = self.scene().sigMouseMoved.connect(
            self._setROISize)
        self._ROI.show()

    @QtCore.pyqtSlot(object)
    def _setROISize(self, pos):
        pos = self.getViewBox().mapSceneToView(pos)
        self._ROI.setSize(pos - self._ROI.pos())

    def mouseReleaseEvent(self, event):
        if self._setROISizeConnection is not None:
            event.accept()
            self.scene().sigMouseMoved.disconnect(self._setROISizeConnection)
            self._setROISizeConnection = None

        else:
            super().mouseReleaseEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton and self._ROI.isVisible():
            event.accept()
            self._ROI.hide()

        else:
            super().mousePressEvent(event)

    def emitROICoordinates(self):
        x0 = self._ROI.pos().x()
        x1 = x0 + self._ROI.size().x()

        self.NewROICoordinates.emit(x0, x1)

    def addItem(self, item):
        if isinstance(item, GlobalPlotDataItem):
            if any(item.isRelatedTo(it) for it in self.listDataItems()):
                # we only allow non-related plotItems to be part!
                raise ValueError("PlotItem already present!")

        self.plotItem.addItem(item)

    def removeItem(self, item):
        if isinstance(item, GlobalPlotDataItem):
            item = next((it for it in self.listDataItems()
                         if item.isRelatedTo(it)), None)

            if item is not None:
                self.plotItem.removeItem(item)

        else:
            self.plotItem.removeItem(item)

    def itemFromName(self, name):
        for item in self.listDataItems():
            if item.name() == name:
                break

        else:
            raise ValueError(f"No item with name: {name}")

        return item

    def containsItemWithName(self, name):
        return any(item.name() == name for item in self.listDataItems())
