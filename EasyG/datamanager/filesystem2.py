from __future__ import annotations
from typing import Optional, Any


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
            raise ChildINodeAlreayExistsError(repr(node))

        super().add(node)

    def remove(self, ID: str) -> None:
        for node in self:
            if node.ID() == ID:
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
                 parent: Optional[INode],
                 data: Optional[Any] = None):

        self.setID(ID)
        self.setParent(parent)
        self.setData(data)

        self._children = INodeSet()

    def ID(self) -> str:
        return self._ID

    def setID(self, ID: str) -> None:
        self._ID = ID

    def parent(self) -> INode:
        return self._parent

    def setParent(self, parent: Optional[INode]) -> None:
        self._parent = parent

    def data(self) -> Any:
        return self._data

    def setData(self, data: Any) -> None:
        self._data = data

    def children(self) -> [INode]:
        return self._children

    def addChild(self, child: INode) -> None:
        try:
            self.children().add(child)
        except ChildINodeAlreayExistsError as err:
            raise err from None

    def removeChild(self, ID: str) -> None:
        child = self.children().remove(ID)
        child.setParent(None)

        return child
