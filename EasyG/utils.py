import functools
import typing
import copy

from PyQt5 import QtCore


class ActiveList(QtCore.QObject):
    DataChanged = QtCore.pyqtSignal()

    def _emitDataChangedOnExit(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            r = func(*args, **kwargs)
            self.DataChanged.emit()

            return r

        return wrapper

    def __init__(self, items: typing.Iterable = [], *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self._list = list(items)
        except TypeError as err:
            raise err from None

        self.append = self._emitDataChangedOnExit(self._list.append)
        self.extend = self._emitDataChangedOnExit(self._list.extend)
        self.insert = self._emitDataChangedOnExit(self._list.insert)
        self.remove = self._emitDataChangedOnExit(self._list.remove)
        self.pop = self._emitDataChangedOnExit(self._list.pop)
        self.clear = self._emitDataChangedOnExit(self._list.clear)
        self.sort = self._emitDataChangedOnExit(self._list.sort)
        self.reverse = self._emitDataChangedOnExit(self._list.reverse)
        self.index = self._list.index
        self.count = self._list.count

    def copy(self) -> 'ActiveList':
        return copy.copy(self)

    def __str__(self) -> str:
        return str(self._list)

    def __repr__(self) -> str:
        return repr(self._list)
