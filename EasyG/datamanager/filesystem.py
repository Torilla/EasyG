from PyQt5 import QtCore

from EasyG.utils import ActiveList


ROOT = "/"
SEP = "/"


class DataObject(QtCore.QObject):
    # self
    DataChanged = QtCore.pyqtSignal(object)

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data = data

    def data(self):
        return self._data

    def setData(self, data):
        self._data = data
        self.DataChanged.emit(self)


class NetworkClientDataObject(DataObject):
    def __init__(self, client):
        # only one list active, otherwise signals will be duplicate
        x, y = ActiveList(), []
        x.DataChanged.connect(self.DataChanged)

        super().__init__(data=(x, y))
        self.client = client
        self._newDataConnection = None

    @QtCore.pyqtSlot(list)
    def _appendData(self, data) -> None:
        _x, _y = self.data()
        x, y = data
        _x.append(x)
        _y.append(y)

    def startParsing(self):
        if not self._newDataConnection:
            self._newDataConnection = self.client.newLineOfData.connect(
                self._appendData)

            self.client.startParsing()

    def stopParsing(self):
        if self._newDataConnection:
            self.client.newLineOfData.disconnect(self._newDataConnection)

            self.client.stopParsing()


class NoSuchChildINodeError(ValueError):
    pass


class INodeNotEmptyError(ValueError):
    pass


class ChildINodeAlreayExistsError(ValueError):
    pass


class INode(object):

    """Emulates a Directory in a Files System. Can have a parent and children.
    Stores arbitray  data.
    """

    def __init__(self, id: str, parent: 'INode' = None,
                 children: ['INode'] = [], data: DataObject = DataObject()):
        """initalize INode class

        Args:
            id (str): Name of the INode in the File System
            parent (INode, optional): Parent INode
            children (list, optional): List of child INodes
            data (DataObject, optional): DataObject that is stored in this INode
        """
        self._children = children
        self.setid(id)
        self.setParent(parent)
        self.setData(data)

    def id(self) -> str:
        """returns the name of the INode

        Returns:
            str: the name of the INode
        """
        return self._id

    def setid(self, id) -> None:
        """sets the name of the INode

        Args:
            id (TYPE): the name of the INode
        """
        self._id = id

    def parent(self) -> str:
        """returns the parent of the INode

        Returns:
            str: the parent of the INode
        """
        return self._parent

    def setParent(self, parent: 'INode') -> None:
        """sets the parent of the INode

        Args:
            parent (INode): the parent of the INode
        """
        self._parent = parent

    def children(self) -> list:
        """returns the children of the INode

        Returns:
            list:  the children of the INode
        """
        return self._children.copy()

    def hasChild(self, id: str) -> bool:
        """Returns true if any child of this INode has a name equal to id

        Args:
            id (str): the id of the child INode in question

        Returns:
            bool: True if a child with name equal to id exists
        """
        return next((True for child in self.children() if child.id() == id),
                    False)

    def addChild(self, child: 'INode') -> None:
        """adds INode child to the list of children

        Args:
            child (INode): the  INode to add to the child list

        Raises:
            ChildINodeAlreayExistsError: if an INode with name equal to id
                already is present
        """
        if self.hasChild(child.id()):
            raise ChildINodeAlreayExistsError(child.id())

        child.setParent(self)
        self._children.append(child)

    def addINode(self, *args, **kwargs) -> None:
        """Convienent wrapper that creates an INode and adds it to the list
        of children

        Args:
            *args: All arguments are passed to the child INode initalizer
            **kwargs: All keyword arguments are passed to the child INode
                initalizer
        """
        self.addChild(INode(*args, **kwargs))

    def removeChild(self, id: str) -> None:
        """Removes child INode with name id from the list of children.

        Args:
            id (str): the name of the child INode

        Raises:
            NoSuchChildINodeError: If the child I node does not exists
        """
        idx = next((idx for idx, child in enumerate(self.children())
                    if child.id() == id), None)

        if idx is None:
            raise NoSuchChildINodeError(repr(id))

        child = self._children.pop(idx)
        child.setParent(None)

        return child

    def getChild(self, id: str) -> None:
        """Returns the child with name equal to id

        Args:
            id (str): the name of the child INode

        Returns:
            None: the target child INode

        Raises:
            NoSuchChildINodeError: If the child INode does not exist
        """
        for child in self.children():
            if child.id() == id:
                break
        else:
            raise NoSuchChildINodeError(repr(id))

        return child

    def dataObject(self):
        """returns the stored data

        Returns:
            DtaObject: the stored DataObject
        """
        return self._data

    def setData(self, data: DataObject) -> None:
        """Sets the stored data

        Args:
            data (DataObject): the data to store
        """
        if not isinstance(data, DataObject):
            raise TypeError(f"Can only store DataObjects, got {data}")

        self._data = data

    def getPath(self) -> str:
        path = [self.id()]
        while self := self.parent():
            path.append(self.id())

        return SEP.join(reversed(path))


class InvalidPathError(ValueError):
    pass


class FileSystem(object):

    """Class emulating a File System. It "implements" mkdir and rmdir
    type methods to store data at arbitrary points in the "File System"
    """

    def __init__(self) -> None:
        """Initalize FileSystem
        """
        self._root = INode(id=ROOT)

    def root(self) -> INode:
        """Return the root INode

        Returns:
            INode: root INode
        """
        return self._root

    def _cd(self, path: str) -> INode:
        """returns the last INode in //path/to/INode

        Args:
            path (str): //path/to/the/INode

        Returns:
            INode: the target INode

        Raises:
            ValueError: When the target INode does not exist
        """

        if not path.startswith(ROOT):
            raise ValueError(f"path must start at root: {ROOT}, got {path}")

        node = self.root()

        for _node in path.removeprefix(ROOT).split(SEP):
            if not _node:
                continue

            try:
                node = node.getChild(_node)
            except NoSuchChildINodeError as err:
                raise err from None

        return node

    def mkdir(self, path: str, data: DataObject) -> None:
        """Creates a child INode at //path/to/INode

        Args:
            path (str): path starting at root and ending at the target INode
            data (DataObject): data being stored at the new INode
        """
        _path, target = path.rsplit(SEP, maxsplit=1)
        _path = _path or ROOT

        try:
            self._cd(_path).addINode(id=target, parent=self, data=data)
        except NoSuchChildINodeError as err:
            raise InvalidPathError(
                f"{path}: No such INode: {err}") from None

    def rmdir(self, path: str) -> None:
        """Removes the INode at //path/to/INode.
        The INode must not have children.

        Args:
            path (str): path starting at root and ending at the target INode

        Raises:
            ValueError: Can not remove the root node

        Returns:
            None: Description
        """
        parent, child = path.rsplit(ROOT, maxsplit=1)
        if not child:
            raise ValueError("Can't remove root!")

        try:
            return self._cd(parent).removeChild(child)
        except NoSuchChildINodeError as err:
            raise InvalidPathError(err) from None

    def setData(self, path: str, data: DataObject) -> None:
        """sets the DataObject at //path/to/INode

        Args:
            path (str): the //path/to/the/INode
            data (DataObject): the DataObject to store at the INode
        """
        try:
            self._cd(path).setData(data)
        except NoSuchChildINodeError as err:
            raise InvalidPathError(err) from None

    def getDataObject(self, path: str) -> DataObject:
        try:
            return self._cd(path).dataObject()
        except NoSuchChildINodeError as err:
            raise InvalidPathError(err) from None
