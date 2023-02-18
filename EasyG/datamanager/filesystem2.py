from __future__ import annotations
from typing import Optional, Any

from pathlib import Path


_ROOT_ID = Path.home().root


class FileSystemError(Exception):
    pass


class ChildINodeAlreayExistsError(FileSystemError):
    pass


class NoSuchChildINodeError(FileSystemError):
    pass


class INodeSet(set):
    def add(self, node: INode) -> None:
        if not isinstance(node, INode):
            raise TypeError(f"{node!r} is not an instance of {INode!r}")

        if node in self:
            raise ChildINodeAlreayExistsError(f"INode already exists: {node.ID}")

        super().add(node)

    def get(self, ID: str) -> INode:
        for node in self:
            if node.ID == ID:
                break
        else:
            raise NoSuchChildINodeError(ID)

        return node

    def __contains__(self, ID: str | INode) -> bool:
        if isinstance(ID, INode):
            ID = ID.ID

        return any(node.ID == ID for node in self)

    def remove(self, ID: str) -> None:
        for node in self:
            if node.ID == ID:
                super().remove(node)
                break
        else:
            raise NoSuchChildINodeError(ID)

        return node

    def discard(self, ID: str) -> None:
        for node in self:
            if node.ID == ID:
                super().discard(node)
                break

    def update(self, nodes: [INode]) -> None:
        return self.__ior__(nodes)

    def __ior__(self, nodes: [INode]) -> None:
        if any(node in self for node in nodes):
            raise ChildINodeAlreayExistsError(repr(nodes))

        return super().__ior__(nodes)


class INode(object):
    def __init__(self,
                 ID: str,
                 parent: Optional[INode] = None,
                 data: Optional[Any] = None):

        self.setParent(parent)
        self.setID(ID)
        self.setData(data)

        self._children = INodeSet()

    @property
    def ID(self) -> str:
        return self._ID

    def setID(self, ID: str) -> None:
        if (ID == _ROOT_ID and self.parent is not None):
            raise ValueError(f"Invalid INode ID: {ID}")
        self._ID = ID

    @property
    def parent(self) -> INode:
        return self._parent

    def setParent(self, parent: INode | None) -> None:
        if p := getattr(self, "_parent", None):
            p.removeChild(self)

        if parent is not None:
            parent.children.add(self)

        self._parent = parent

    @property
    def children(self) -> INodeSet:
        return self._children

    def addChild(self, child: INode) -> None:
        child.setParent(self)

    def removeChild(self, ID: str) -> None:
        child = self.children.remove(ID)
        child._parent = None

        return child

    def getChild(self, ID: str) -> INode:
        return self.children.get(ID)

    @property
    def data(self) -> Any:
        return self._data

    def setData(self, data: Any) -> None:
        self._data = data

    def tree(self, indent: int = 0) -> str:
        string = self.ID

        for child in self.children:
            string += "\n" + "|  " * indent + f"|__{child.tree(indent=indent + 1)}"

        return string

    def __repr__(self) -> str:
        parent = self.parent
        if parent is not None:
            parent = parent.ID

        return f"{super().__repr__()} (ID: '{self.ID}' parent: {parent})"


class InvalidPathError(FileSystemError):
    pass


class FileSystem(object):
    def __init__(self):
        self._root = INode(ID=_ROOT_ID, parent=None)
        self._cwd = self._root
        self._stack = []

    @property
    def stack(self):
        return self._stack

    @property
    def root(self) -> INode:
        return self._root

    @property
    def cwd(self) -> INode:
        return self._cwd

    def _getChildINode(self, path: str | Path,
                       createParents: bool = False) -> INode:
        path = Path(path)
        parts = path.parts

        if path.root:
            parts = parts[1:]     # remove root from path, this is an implicit cd to root
            node = self.root
        else:
            node = self.cwd

        for part in parts:
            if part == ".":
                continue

            elif part == "..":
                # if we are at the root, .. points back to itself
                node = node.parent or node

            else:
                try:
                    node = node.getChild(part)
                except NoSuchChildINodeError:
                    if createParents:
                        _node = INode(ID=part)
                        node.addChild(_node)
                        node = _node

                    else:
                        err = f"{path}: No such INode: {part}"
                        raise InvalidPathError(err) from None

        return node

    def cd(self, path: str | Path = _ROOT_ID) -> None:
        self._cwd = self._getChildINode(path)

    def pushd(self, path: str | Path) -> None:
        self.stack.append(self._cwd)
        try:
            self.cd(path)

        except FileSystemError as err:
            # restore the old stack in case the cd fails
            self.stack.pop()
            raise err from None

    def popd(self) -> None:
        self._cwd = self.stack.pop()

    def mkdir(self, path: str | Path, parents: bool = False) -> None:
        path = Path(path)
        if not path.name:
            raise InvalidPathError(path)
        try:
            node = self._getChildINode(path.parent, createParents=parents)
        except InvalidPathError as err:
            raise err from None

        child = INode(ID=path.name)
        node.addChild(child)

    def rmdir(self, path: str | Path) -> INode:
        path = Path(path)

        if not path.name:
            raise InvalidPathError(path)

        try:
            child = self._getChildINode(path.parent).removeChild(path.name)
        except NoSuchChildINodeError as err:
            raise InvalidPathError(err) from None

        return child

    def tree(self) -> str:
        return self.cwd.tree()
