from PyQt5 import QtCore


class AbstractDataSource(object):
    dataChanged = QtCore.pyqtSignal()

    def __init__(self, name, *data):
        self.name = name
        self._data = (list(d) for d in data)

    def getCurrentData(self):
        return self.data


class StaticDataSource(AbstractDataSource):
    pass


class NetworkClientDataSource(AbstractDataSource):
    def __init__(self, client):
        super().__init__(name=client.getTitle(), data=([], []))

        self._client = client
        self._client.newLineOfData.connect(self._onNewClientData)

    def _onNewClientData(self, data):
        for d, x in zip(self.data, data):
            d.append(x)

        self.dataChanged.emit()


class MemberAlreadyExistsError(KeyError):
    pass


class NamespaceAlreadyExistsError(KeyError):
    pass


class DataNamespace(object):
    def __init__(self, name, members={}):
        self.name = name
        self.members = members

    def addMember(self, member):
        if member.name in self.members:
            raise MemberAlreadyExistsError(member.name)

        self.members[member.name] = member

    def getMember(self, name):
        return self.members[name]


class DataManager(object):
    DEFAULTNAMESPACE = "default"

    # name, namespace
    dataChanged = QtCore.pyqtSignal(str, str)

    def __init__(self):
        self._namespaces = {self.DEFAULTNAMESPACE: []}

    def addNamespace(self, ns):
        if not isinstance(ns, DataNamespace):
            ns, name = DataNamespace(name=ns), ns

        else:
            name = ns.name

        if name in self._namespaces:
            raise NamespaceAlreadyExistsError(name)

        self._namespaces[name]

    def registerNewDataSource(self, src, namespace=None):
        def _onDataSourceChanged():
            self.dataChanged.emit(src.name, namespace)

        if namespace is None:
            namespace = self.DEFAULTNAMESPACE

        self._namespaces[namespace].addMember(src)
        src.dataChanged.connect(self._onDataSourceChanged)

    def getData(self, name, namespace=None):
        if namespace is None:
            namespace = self.DEFAULTNAMESPACE

        return self._namespaces[namespace].getMember(name).getData()
