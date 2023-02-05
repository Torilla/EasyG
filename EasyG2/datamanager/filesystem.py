class NoSuchChildINodeError(ValueError):
    pass


class INodeNotEmptyError(ValueError):
    pass


class ChildINodeAlreayExistsError(ValueError):
    pass


class INode(object):
    def __init__(self, *data, id, parent=None, children=[], ):
        self._children = children
        self.setid(id)
        self.setParent(parent)
        self.setData(*data)

    def id(self):
        return self._id

    def setid(self, id):
        self._id = id

    def parent(self):
        return self._parent

    def setParent(self, parent):
        self._parent = parent

    def children(self):
        return self.children.copy()

    def hasChild(self, id):
        return next((True for child in self.children() if child.id() == id),
                    False)

    def addChild(self, child):
        if self.hasChild(child.id()):
            raise ChildINodeAlreayExistsError(child.id())

        child.setParent(self)
        self._children.append(child)

    def addINode(self, *args, **kwargs):
        self.addChild(INode(*args, **kwargs))

    def removeChild(self, id):
        idx = next((idx for idx, child in enumerate(self.children())
                    if child.id() == id), None)

        if idx is None:
            raise NoSuchChildINodeError(id)

        child = self._children.pop(idx)
        child.setParent(None)

        return child

    def getChild(self, id):
        for child in self.children():
            if child.id() == id:
                break
        else:
            raise NoSuchChildINodeError(id)

        return child

    def data(self):
        return self._data

    def setData(self, *data):
        self._data = data


class DataManager(object):
    ROOT = "/"

    def __init__(self):
        self._root = INode(id=self.ROOT)

    def root(self):
        return self._root

    def _cd(self, path):
        """returns the last INode in path/to/INode"""

        _root, *path = path.split(self.ROOT)

        node = self.root()
        if node.id() != _root:
            raise ValueError(f"path must start at the root: {self.ROOT}")

        for _node in path:
            node = node.getChild(_node)

        return node

    def mkdir(self, *data, path):
        path, target = path.rsplit(self.ROOT, maxsplit=1)

        self._cd(path).addINode(*data, id=target, parent=self)

