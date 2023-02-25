"""Module filesystem.py

This module implements a very simply virtual implementation of a filesystem
as well as a shell (SsSh - The StupidlySimpleShell) to interact with the
filesystem and the stored data.

The main functionality is bundled in StupidlySimpleShell which exposes a
'Unix like' shell interface to create, move and delete virtual directories.
"""
from __future__ import annotations
from typing import Optional, Any, Iterator

import pathlib
from functools import wraps

from EasyG import defaults


class FileSystemError(Exception):

    """Raised when a FileSytem Operation Fails"""


class ChildINodeAlreayExistsError(FileSystemError):

    """Raised when attempting to add a child INode with an ID that is already
    present in the INodeChildSet
    """


class NoSuchChildINodeError(FileSystemError):

    """Raise when trying to access an INode that does not exist"""


class INodeChildSet:

    """class INodeChildSet

    Class storing a unique set of INodes. Uniqueness of INodes is based on
    their name. Each name can only exist once in the set.
    """

    def __init__(self):
        """Initialize new INodeChildSet"""
        self._members = set()

    def __iter__(self) -> Iterator[INode]:
        """Return an iterator of the members of the set

        Returns:
            Iterator[INode]: The iterator returning the members of the set
        """
        return iter(self._members)

    def __contains__(self, name: str | INode) -> bool:
        """Determins wether an INode with name equal to the given name exists

        Args:
            name (str | INode): The name or an INode with the same name to test

        Returns:
            bool: True if an INode with the tested name exists, otherwise false
        """
        if isinstance(name, INode):
            name = name.name

        return any(n.name == name for n in self)

    def __bool__(self) -> bool:
        """Determines the truth value of the set

        Returns:
            bool: Returns false if the set is empty else true
        """
        return bool(self._members)

    def add(self, node: INode) -> None:
        """Adds another node to the set of child nodes

        Args:
            node (INode): The node to add

        Raises:
            ChildINodeAlreayExistsError: If a node with the same name exists
            TypeError: If node is not an instance of INode
        """
        if not isinstance(node, INode):
            raise TypeError(f"Expected instance of {INode}, got '{node}'")

        if node in self:
            raise ChildINodeAlreayExistsError(node)

        self._members.add(node)

    def get(self, name: str | INode) -> INode:
        """Return the node with name equal to the given name

        Args:
            name (str | INode): The name of the node or a node with same name

        Returns:
            INode: The node with name equal to the given name

        Raises:
            NoSuchChildINodeError: If no node with name equal to the given name
                is present
        """
        if isinstance(name, INode):
            name = name.name

        for member in self:
            if member.name == name:
                break
        else:
            raise NoSuchChildINodeError(name)

        return member

    def remove(self, name: str | INode) -> INode:
        """Removes a node from the set

        Args:
            name (str | INode): The name of the node to remove or a node with
                the same name

        Returns:
            INode: The removed member

        Raises:
            NoSuchChildINodeError: If no inode with the given name exists
        """
        if isinstance(name, INode):
            name = name.name

        for member in self:
            if member.name == name:
                self._members.remove(member)
                break

        else:
            raise NoSuchChildINodeError(name)

        return member


class INode:

    """class repesenting a single node in a file system structure. It is
    inspired by the Linux INode.
    """

    def __init__(
        self, name: str, parent: Optional[INode] = None, data: Optional[Any] = None
    ):
        """Initalize a new INode

        Args:
            name (str): The name of the new INode.
            parent (Optional[INode], optional): The parent of the new INode
            data (Optional[Any], optional): The data to store in this INode
        """
        self.set_name(name)
        self.set_parent(parent)
        self.set_data(data)

        self._children = INodeChildSet()

    @property
    def name(self) -> str:
        """Return the name of the INode

        Returns:
            str: The name of the INode
        """
        return self._name

    def set_name(self, name: str) -> None:
        """Sets the name of the INode to name

        Args:
            name (str): The new name
        """
        self._name = name

    @property
    def parent(self) -> INode | None:
        """Returns the parent of the INode

        Returns:
            INode | None
        """
        return getattr(self, "_parent", None)

    def set_parent(self, parent: INode | None) -> None:
        """Set the parent of the INode to parent and add self to the list of
        children of parent. This will also remove the INode from the previous
        parent's list of children if the INode has a parent.

        Args:
            parent (INode | None): The new parent INode or None. If the INode
                already has a parent, it will remove itself from its previous
                parent's list of child nodes.
        """
        if (old_parent := self.parent) is not None:
            old_parent.children.remove(self)

        if parent is not None:
            parent.children.add(self)

        self._parent = parent

    def add_child(self, child: INode) -> None:
        """Add a new child INode to the INode

        Args:
            child (INode): The INode to add as child. The current INode will
                take ownership of the child INode
        """
        child.set_parent(self)

    def remove_child(self, child: str | INode) -> INode:
        """Remove an INode from the set of child nodes

        Args:
            child (str | INode): The INode or the name of the INode to remove.
                The child INode will not longer be owned by the current INode.

        Returns:
            INode: The removed INode. It will no longer have a parent INode.

        Raises:
            NoSuchChildINodeError: If the request child does not exist.
        """

        try:
            child = self.children.get(child)
        except NoSuchChildINodeError as err:
            raise err from None

        child.set_parent(None)

        return child

    def get_child(self, name: str) -> INode:
        """Return the INode with name equal to the given name

        Args:
            name (str): The name of the requested INode

        Returns:
            INode: The request INode with name equal to the given name
        """
        return self.children.get(name)

    @property
    def data(self) -> Any:
        """Return the data stored in this INode

        Returns:
            Any: The stored data
        """
        return self._data

    def set_data(self, data: Any) -> None:
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

    def tree(self, indent: int = 0) -> str:
        """Return a tree representation of the tree where the current INode is
            the root and its children are the leafs

        Args:
            indent (int, optional): Internal variable not meant for using

        Returns:
            str: The tree representation of this INode tree
        """
        string = self.name

        for kid in self.children:
            string += "\n" + "|  " * indent + f"|__{kid.tree(indent + 1)}"

        return string

    def __repr__(self) -> str:
        """Return the representation of this INode

        Returns:
            str: The representation fiven as object (INode.name, INode.parent)
        """
        parent = self.parent
        if parent is not None:
            parent = parent.name  # type: ignore[assignment]

        return f"{super().__repr__()} (name: '{self.name}' parent: {parent})"


class InvalidPathError(FileSystemError):

    """Raised when an invalid path is being accessed"""


class FileSystem:

    """Class emulating a very simple shell that has a few virtual filesystem
        operations such as mkdir, rmdir, mv, cd, etc.

    Attributes:
        name (str): The name of the root node of the filesystem.
    """

    ROOT_NAME = "/"

    def __init__(self):
        """Initalize a new StupdilySimpleShell instance"""

        # root node of the filesystem
        self._root = INode(name=self.ROOT_NAME)
        # current working directory, i.e a child node in the tree of self._root
        self._cwd = self._root

    def _implicit_cd(
        self, path: str | pathlib.Path, create_parents: bool = False
    ) -> INode:
        """Return the last INode present in path.

        Args:
            path (str | pathlib.Path): The path to the INode in question. If
                given as string, it is implicitly converted to a pathlib.Path
                instance.
            create_parents (bool, optional): If true, any non-existing INodes
                in path will be created on the fly

        Raises:
            NoSuchChildINodeError: If createdParents is false and any of the
                INodes in path do not exist

        Returns:
            INode: The request INode
        """

        def get_child():
            """Summary

            Returns:
                TYPE: Description
            """
            try:
                child = node.get_child(part)

            except NoSuchChildINodeError:
                if create_parents:
                    child = INode(name=part, parent=node)

                else:
                    raise

            return child

        path = pathlib.Path(path)

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

            if part == "..":
                # if the current node has no parent we are at the root.
                # In this case '..' just points back to the root itself
                # otherwise we want the parent node
                node = node.parent or node

            else:
                # get the current child Node for this part of the path
                try:
                    node = get_child()
                except NoSuchChildINodeError as err:
                    raise err from None

        return node

    def cd(self, path: str | pathlib.Path) -> None:
        """Set the current working directory to path

        Args:
            path (str | pathlib.Path): The path to set the current working
                directory to. If given as a string instance, it is implicitly
                converted to a pathlib.Path instance.

        Raises:
            NoSuchChildINodeError: If any of the INodes in path do not exist
        """
        try:
            self._cwd = self._implicit_cd(path)
        except NoSuchChildINodeError as err:
            raise err from None

    def mkdir(
        self,
        path: str | pathlib.Path,
        parents: bool = False,
        data: Optional[Any] = None,
    ) -> None:
        """Create a new directory in the filesystm.

        Args:
            path (str | pathlib.Path): The path to the directory to create. If
                given as a string instance, it is implicitly converted to a
                patlib.Path instance.
            parents (bool, optional): If true, any non-existing nodes in path
                will be created on the fly
            data (Optional[Any], optional): The data to store in the new dir

        Raises:
            InvalidPathError: If parents is false and any of the INodes in path
                do not exist or if there is already a target INode with the
                same name as the new directory
        """
        path = pathlib.Path(path)

        if not path.name:
            raise InvalidPathError(path)

        try:
            parent = self._implicit_cd(path.parent, create_parents=parents)
        except NoSuchChildINodeError as err:
            raise InvalidPathError(f"{path}: {err}") from None

        try:
            INode(name=path.name, parent=parent, data=data)
        except ChildINodeAlreayExistsError as err:
            raise InvalidPathError(f"{path}: {err}") from None

    def rmdir(self, path: str | pathlib.Path) -> None:
        """Removes the last INode in path from the filesystem

        Args:
            path (str | pathlib.Path): The path to the INode which to remove.
                If given as a string instance, it is implicitly converted to
                a pathlib.Path instance

        Raises:
            InvalidPathError: If the target INode does not exis
        """
        path = pathlib.Path(path)

        if not path.name:
            raise InvalidPathError(path)

        try:
            parent = self._implicit_cd(path.parent)

        except NoSuchChildINodeError as err:
            raise InvalidPathError(f"{path}: {err}") from None

        try:
            parent.remove_child(path.name)
        except NoSuchChildINodeError as err:
            raise InvalidPathError(f"{path}: {err}") from None

    def mv(self, src: str | pathlib.Path, dest: str | pathlib.Path) -> None:
        """Move the directory specified in src to the directory specified in
        dest. If the last node in dest does not exist, but the second to last
        does, the src node is being renamed to the last node in dest path
        and added as child to the second to last node in dest.

        Args:
            src (str | pathlib.Path): The path to the src directory which to is
                to be moved. If given as a string instance, it is implicitly
                converted to a pathlib.Path instance
            dest (str | pathlib.Path): The path to the directory which to move
                the src directory to. If the last node in dest path does not
                exist, the old src dir will be renamed to this last node name.
                If given as a string instance, it is implicitly converted to a
                pathlib.Path instance

        Raises:
            InvalidPathError: If src dir does not exist or dest path is invalid
        """
        src, dest = pathlib.Path(src), pathlib.Path(dest)

        if not src.name:
            raise InvalidPathError(src)

        src_dir = self._implicit_cd(src.parent)
        try:
            dest_dir = self._implicit_cd(dest)

        except NoSuchChildINodeError:
            try:
                dest_dir = self._implicit_cd(dest.parent)

            except NoSuchChildINodeError:
                raise InvalidPathError(dest) from None

        # !! This part of the code is bugged. If the src dir needs to be
        # !! renamed but a node with this name already exists in the dest dir
        # !! it will fail to add it as a child but it will be removed from the
        # !! parent and thus be lost.

        src_child = src_dir.remove_child(src.name)
        if dest_dir.name != dest.name:
            # if the target dir in path doesn't exist, it is the new name of
            # moved child
            src_child.set_name(dest.name)

        dest_dir.add_child(src_child)

    def get_data(self, path: str | pathlib.Path) -> Any:
        """Returns the data stored in the last node in path

        Args:
            path (str | pathlib.Path): The path to the INode from which to
                retrieve the data

        Returns:
            Any: The data stored in the INode
        """
        return self._implicit_cd(path).data

    def set_data(self, path: str | pathlib.Path, data: Any) -> None:
        """Set the data of the node given in path to data

        Args:
            path (str | pathlib.Path): The path of the INode where to store
                the data at.
            data (Any): The data to store at this INode
        """
        self._implicit_cd(path).set_data(data)

    def tree(self) -> str:
        """Return tree representation starting at the current workind directory

        Returns:
            str: The tree representation starting at the cwd
        """
        return self._cwd.tree()
