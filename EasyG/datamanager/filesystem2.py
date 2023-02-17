from __future__ import annotations
from typing import Optional, Any

from pathlib import Path


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

        if any(node.ID == n.ID for n in self):
            raise ChildINodeAlreayExistsError(f"INode already exists: {node.ID}")

        super().add(node)

    def remove(self, ID: str) -> None:
        for node in self:
            if node.ID() == ID:
                super().remove(node)
                node.setParent(None)
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
        if (ID == FileSystem._ROOT_ID and self.parent is not None):
            raise ValueError(f"Invalid INode ID: {ID}")
        self._ID = ID

    @property
    def parent(self) -> INode:
        return self._parent

    def setParent(self, parent: Optional[INode]) -> None:
        self._parent = parent

    @property
    def data(self) -> Any:
        return self._data

    def setData(self, data: Any) -> None:
        self._data = data

    @property
    def children(self) -> INodeSet:
        return self._children

    def addChild(self, child: INode) -> None:
        try:
            self.children.add(child)
        except ChildINodeAlreayExistsError as err:
            raise err from None

        child.setParent(self)

    def removeChild(self, ID: str) -> None:
        child = self.children.remove(ID)
        child.setParent(None)

        return child

    def getChild(self, ID: str) -> INode:
        for child in self.children:
            if child.ID == ID:
                break
        else:
            raise NoSuchChildINodeError(ID)

        return child

    def __repr__(self) -> str:
        return "{} (ID: '{}' parent: {})".format(super().__repr__(),
                                                 self.ID,
                                                 self.parent,
                                                 self.children)


INodeType = tuple[str, Optional[INode], Optional[Any]]


class InvalidPathError(FileSystemError):
    pass


class FileSystem(object):
    _ROOT_ID = Path.home().root

    def __init__(self):
        self._root = INode(ID=FileSystem._ROOT_ID, parent=None)
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

    def cd(self, path: str | Path) -> None:
        node = self.cwd

        path = Path(path)
        parts = path.parts

        if path.root:
            parts = parts[1:]     # remove root
            node = self.root

        for part in parts:
            if part == ".":
                continue

            elif part == "..":
                node = node.parent
                if not node:
                    raise InvalidPathError(path)

            else:
                try:
                    node = node.getChild(part)
                except NoSuchChildINodeError:
                    err = f"{path}: No such INode: {part}"
                    raise InvalidPathError(err) from None

        self._cwd = node

    def pushd(self, path: str | Path) -> None:
        self.stack.append(self._cwd)
        self.cd(path)

    def popd(self) -> None:
        self._cwd = self.stack.pop()

    def mkdir(self, path: str | Path) -> None:
        path = Path(path)
        if not path.name:
            raise InvalidPathError(path)

        self.pushd(path.parent)

        try:
            self.cwd.addChild(INode(ID=path.name, parent=self.cwd))
        except ChildINodeAlreayExistsError as err:
            raise InvalidPathError(err) from None
        finally:
            self.popd()
