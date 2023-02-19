from __future__ import annotations
from typing import Optional, Any, Iterator

from functools import wraps
from pathlib import Path


class FileSystemError(Exception):
    pass


class ChildINodeAlreayExistsError(FileSystemError):
    pass


class NoSuchChildINodeError(FileSystemError):
    pass


class INodeChildSet(object):

    """class INodeChildSet

    Class storing a unique set of INodes. Uniqueness of INodes is based on
    their ID. Each ID can only exist once.
    """

    def __init__(self):
        self._members = set()

    def __iter__(self) -> Iterator[INode]:
        """Return an iterator of the members of the set

        Returns:
            Iterator: The iterator returning the members of the set
        """
        return iter(self._members)

    def __contains__(self, ID: str | INode) -> bool:
        """Determins wether an INode with ID equal to the given ID is present

        Args:
            ID (str | INode): The ID or an INode with the same ID to test for presence

        Returns:
            bool: True if an INode with the tested ID is present, otherwise false
        """
        if isinstance(ID, INode):
            ID = ID.ID

        return any(n.ID == ID for n in self)

    def __bool__(self) -> bool:
        """Determines the truth value of the set

        Returns:
            bool: Returns false if the set is empty else true
        """
        return bool(self._members)

    def add(self, node: INode) -> None:
        """Adds another node to the set if no node with the same ID is already
        present

        Args:
            node (INode): The node to add

        Raises:
            ChildINodeAlreayExistsError: If a node with the same ID already exists
            TypeError: If node is not an instance of INode
        """
        if not isinstance(node, INode):
            raise TypeError(f"Expected instance of {INode}, got '{node}'")

        if node in self:
            raise ChildINodeAlreayExistsError(node)

        self._members.add(node)

    def get(self, ID: str | INode) -> INode:
        """Return the node with ID equal to the given ID

        Args:
            ID (str | INode): The ID of the node or a node with the same ID to return

        Returns:
            INode: The node with ID equal to the given ID

        Raises:
            NoSuchChildINodeError: If no node with ID equal to the given ID is
                present
        """
        if isinstance(ID, INode):
            ID = ID.ID

        for member in self:
            if member.ID == ID:
                break
        else:
            raise NoSuchChildINodeError(ID)

        return member

    def remove(self, ID: str | INode) -> INode:
        """Removes a node from the set

        Args:
            ID (str | INode): The ID of the node to remove or a node with the
                same ID

        Returns:
            INode: The removed member

        Raises:
            NoSuchChildINodeError: Description
        """
        if isinstance(ID, INode):
            ID = ID.ID

        for member in self:
            if member.ID == ID:
                self._members.remove(member)
                break

        else:
            raise NoSuchChildINodeError(ID)

        return member


class INode(object):

    """class repesenting a single node in a file system structure. It is
    inspired by the Linux INode.
    """

    def __init__(self, ID: str, parent: Optional[INode] = None,
                 data: Optional[Any] = None):
        """Initalize a new INode

        Args:
            ID (str): The ID of the new INode.
            parent (Optional[INode], optional): The parent of the new INode
            data (Optional[Any], optional): The data to store in this INode
        """
        self.setID(ID)
        self.set_parent(parent)
        self.setData(data)

        self._children = INodeChildSet()

    @property
    def ID(self) -> str:
        """Return the ID of the INode

        Returns:
            str: The ID of the INode
        """
        return self._ID

    def setID(self, ID) -> None:
        """Sets the ID of the INode to ID

        Args:
            ID (TYPE): The new ID
        """
        self._ID = ID

    @property
    def parent(self) -> INode | None:
        """Returns the parent of the INode

        Returns:
            INode | None: The parent of the INode. Returns None if no parent
                INode is set
        """
        return getattr(self, "_parent", None)

    def set_parent(self, parent: INode | None) -> None:
        """Set the parent of the INode to parent and add self to the list of
        children of parent. This will also remove the INode from the previous
        parent's list of children if the INode has a parent.

        Args:
            parent (INode | None): The new parent.
        """
        if (oldParent := self.parent) is not None:
            oldParent.children.remove(self)

        if parent is not None:
            parent.children.add(self)

        self._parent = parent

    def addChild(self, child: INode) -> None:
        """Add a new child INode to the INode

        Args:
            child (INode): The INode to add as child. The current INode will
                take ownership of the child INode
        """
        child.set_parent(self)

    def removeChild(self, child: str | INode) -> INode:
        """Remove a child INode

        Args:
            child (str | INode): The INode or the ID of the INode to remove.
                The child INode will not longer be owned by the current INode.

        Returns:
            INode: The removed INode

        Raises:
            NoSuchChildINodeError: If the request child does not exist.
        """

        try:
            child = self.children.get(child)
        except NoSuchChildINodeError as err:
            raise err from None

        child.set_parent(None)

        return child

    def getChild(self, ID: str) -> INode:
        """Return the INode with ID equal to the given ID

        Args:
            ID (str): The ID of the requested INode

        Returns:
            INode: The request INode with ID equal to the given ID
        """
        return self.children.get(ID)

    @property
    def data(self) -> Any:
        """Return the data stored in this INode

        Returns:
            Any: The stored data
        """
        return self._data

    def setData(self, data: Any) -> None:
        """Set the stored data in this INode to data

        Args:
            data (Any): The data to store
        """
        self._data = data

    @property
    def children(self) -> INodeChildSet:
        """The ChildINodeSet that stores the children of this INode

        Returns:
            INodeChildSet: The ChildINodeSet that stores the children of this
                INode
        """
        return self._children

    def tree(self, _indent: int = 0) -> str:
        """Return a tree representation of the tree where the current INode is
            the root and its children are the leafs

        Args:
            _indent (int, optional): Internal variable not meant for using directly

        Returns:
            str: The tree representation of this INode tree
        """
        string = self.ID

        for child in self.children:
            string += "\n" + "|  " * _indent + f"|__{child.tree(_indent=_indent + 1)}"

        return string

    def __repr__(self) -> str:
        """Return the representation of this INode

        Returns:
            str: The representation fiven as 'object (INode.ID, INode.parent)'
        """
        parent = self.parent
        if parent is not None:
            parent = parent.ID

        return f"{super().__repr__()} (ID: '{self.ID}' parent: {parent})"


class InvalidPathError(FileSystemError):
    pass


def ensureIsPathInstance(func):
    @wraps(func)
    def wrapper(self, path, *args, **kwargs):
        return func(self, Path(path), *args, **kwargs)

    return wrapper


class StupidlySimpleShell(object):

    """Class emulating a very simple shell that has a few virtual filesystem
        operations such as mkdir, rmdir, mv, cd, etc.

    Attributes:
        ROOT_ID (str): The name of the root node of the filesystem.
    """

    ROOT_ID = "/"

    def __init__(self):
        self._root = INode(ID=self.ROOT_ID)
        self._cwd = self._root

    @ensureIsPathInstance
    def _implicit_cd(self, path: Path,
                     createParents: bool = False) -> INode:
        """Return the last INode present in path.

        Args:
            path (Path): The path to the INode in question
            createParents (bool, optional): If true, any non-existing INodes
                in path will be created on the fly

        Returns:
            INode: The request INode

        Raises:
            NoSuchChildINodeError: If createdParents is false and any of the
                INodes in path do not exist
        """
        def getChild():
            try:
                child = node.getChild(part)

            except NoSuchChildINodeError:
                if createParents:
                    child = INode(ID=part, parent=node)

                else:
                    raise

            return child

        # determine if we operate on the cwd or on the root
        if path.root:
            # remove root from the path
            parts = path.parts[1:]
            node = self._root

        else:
            parts = path.parts
            node = self._cwd

        for part in parts:
            # iterate over each child INode in given path
            if part == ".":
                continue

            elif part == "..":
                # if the current node has no parent we are at the root.
                # In this case '..' just points back to the root itself
                # otherwise we want the parent node
                node = node.parent or node

            else:
                # get the current child Node for this part of the path
                try:
                    node = getChild()
                except NoSuchChildINodeError as err:
                    raise err from None

        return node

    @ensureIsPathInstance
    def cd(self, path: Path) -> None:
        """Set the current working directory to path

        Args:
            path (str | Path): The path to set the cwd to

        Raises:
            NoSuchChildINodeError: If any of the INodes in path do not exist
        """
        try:
            self._cwd = self._implicit_cd(path)
        except NoSuchChildINodeError as err:
            raise err from None

    @ensureIsPathInstance
    def mkdir(self, path: Path, parents: bool = False,
              data: Optional[Any] = None) -> None:
        """Create a new directory in the filesystm.

        Args:
            path (str | Path): The path to the directory to create
            parents (bool, optional): If true, any non-existing nodes in path
                will be created on the fly
            data (Optional[Any], optional): The data to store in the new dir

        Raises:
            InvalidPathError: If parents is false and any of the INodes in path
                do not exist or if there is already a target INode with the
                same name as the new directory
        """
        if not path.name:
            raise InvalidPathError(path)

        try:
            parent = self._implicit_cd(path.parent, createParents=parents)
        except NoSuchChildINodeError as err:
            raise InvalidPathError(f"{path}: {err}") from None

        try:
            INode(ID=path.name, parent=parent, data=data)
        except ChildINodeAlreayExistsError as err:
            raise InvalidPathError(f"{path}: {err}") from None

    @ensureIsPathInstance
    def rmdir(self, path: Path) -> None:
        """Removes the last INode in path from the filesystem

        Args:
            path (Path): The path to the INode to remove

        Raises:
            InvalidPathError: If the target INode does not exis
        """
        if not path.name:
            raise InvalidPathError(path)

        try:
            parent = self._implicit_cd(path.parent)

        except NoSuchChildINodeError as err:
            raise InvalidPathError(f"{path}: {err}") from None

        try:
            parent.removeChild(path.name)
        except NoSuchChildINodeError as err:
            raise InvalidPathError(f"{path}: {err}") from None

    def mv(self, src: str | Path, dest: str | Path) -> None:
        """Summary

        Args:
            src (str | Path): The path to the src directory to move
            dest (str | Path): The path to the directorz which to move the src
                directory to. If the last node in dest path does not exist,
                the old src dir will be renamed to this last node ID

        Raises:
            InvalidPathError: If the src dir does not exist or the dest path is invalid.
        """
        src, dest = Path(src), Path(dest)

        if not src.name:
            raise InvalidPathError(src)

        src_dir = self._implicit_cd(src.parent)
        try:
            dest_dir = self._implicit_cd(dest)

        except NoSuchChildINodeError:
            try:
                dest_dir = self._implicit_cd(dest.parent)

            except NoSuchChildINodeError:
                raise InvalidPathError(dest)

        src_child = src_dir.removeChild(src.name)

        if dest_dir.ID != dest.name:
            # if the last dir in path does not exist, we rename the old dir to this
            src_child.setID(dest.name)

        dest_dir.addChild(src_child)

    @ensureIsPathInstance
    def getData(self, path: Path) -> Any:
        """Returns the data stored in the last node in path

        Args:
            path (Path): The path to the INode to which to retrieve the data from

        Returns:
            Any: The data stored in the INode
        """
        return self._implicit_cd(path).data

    @ensureIsPathInstance
    def setData(self, path: Path, data: Any) -> None:
        """Set the data of the node given in path to data

        Args:
            path (Path): The path of the INode where to store the data
            data (Any): The data to store at this INode
        """
        self._implicit_cd(path).setData(data)

    def tree(self) -> str:
        """Return a tree representation starting at the current workind directory

        Returns:
            str: The tree representation starting at the cwd
        """
        return self._cwd.tree()
