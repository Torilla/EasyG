from PyQt5 import QtCore


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

    def __init__(self, id: str, parent: INode = None, children: list = [],
                 **data):
        """initalize INode class

        Args:
            id (str): Name of the INode in the File System
            parent (INode, optional): Parent INode
            children (list, optional): List of child INodes
            **data: Data that is stored in this INode
        """
        self._children = children
        self.setid(id)
        self.setParent(parent)
        self.setData(**data)

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

    def setParent(self, parent: INode) -> None:
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
        return self.children.copy()

    def hasChild(self, id: str) -> bool:
        """Returns true if any child of this INode has a name equal to id

        Args:
            id (str): the id of the child INode in question

        Returns:
            bool: True if a child with name equal to id exists
        """
        return next((True for child in self.children() if child.id() == id),
                    False)

    def addChild(self, child: INode) -> None:
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
        """Convienent wrapper that creates and INode and adds it to the list
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
            raise NoSuchChildINodeError(id)

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
            raise NoSuchChildINodeError(id)

        return child

    def data(self) -> dict:
        """returns the stored data

        Returns:
            dict: the stored data
        """
        return self._data

    def setData(self, **data):
        """Sets the stored data

        Args:
            **data: the data to store
        """
        self._data = data


class DataManager(object):

    """Class emulating a File System. It "implements" mkdir and rmdir
    type methods to store data at arbitrary points in the "File System"

    Attributes:
        dataChanged (QtCore.pyqtsignal): emits the path to the INode when
            setData is called on an existing INode
        newDataSource (QtCore.pyQtSignal): emits path to the INode when a new
            INode is created
        ROOT (str): the root INode path
    """

    ROOT = "/"

    # path
    dataChanged = QtCore.pyqtSignal(str)
    newDataSource = QtCore.pyqtSignal(str)

    def __init__(self) -> None:
        """Initalize DataManager
        """
        self._root = INode(id=self.ROOT)

    def root(self) -> INode:
        """Return the root INode

        Returns:
            INode: root INode
        """
        return self._root

    def _cd(self, path: str) -> INode:
        """returns the last INode in /path/to/INode

        Args:
            path (str): /path/to/the/INode

        Returns:
            INode: the target INode

        Raises:
            ValueError: When the target INode does not exist
        """

        _root, *path = path.split(self.ROOT)

        node = self.root()
        if node.id() != _root:
            raise ValueError(f"path must start at the root: {self.ROOT}")

        for _node in path:
            node = node.getChild(_node)

        return node

    def mkdir(self, path: str, **data) -> None:
        """Creates a child INode at /path/to/INode

        Args:
            path (str): path starting at root and ending at the target INode
            **data: data being stored at the new INode
        """
        _path, target = path.rsplit(self.ROOT, maxsplit=1)

        self._cd(_path).addINode(id=target, parent=self, **data)

        self.newDataSource.emit(path)

    def rmdir(self, path: str) -> None:
        """Removes the INode at /path/to/INode.
        The INode must not have children.

        Args:
            path (str): path starting at root and ending at the target INode

        Raises:
            ValueError: Can not remove the root node

        Returns:
            None: Description
        """
        parent, child = path.rsplit(self.ROOT, maxsplit=1)
        if not child:
            raise ValueError("Can't remove root!")

        return self._cd(parent).removeChild(child)

    def setData(self, path: str, **data) -> None:
        """sets the data at /path/to/INode

        Args:
            path (str): the /path/to/the/INode
            **data: the data to store at the INode
        """
        self._cd(path).setData(**data)

        self.dataChanged.emit(path)
