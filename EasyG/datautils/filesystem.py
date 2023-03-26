from __future__ import annotations
from typing import Any
from collections.abc import Set, Iterator, Callable, Iterable

import pathlib

from PyQt5 import QtCore


class DataObject(QtCore.QObject):

    """class DataObject

    Represents a File like object in a Filesystem. Allows to track data changes
    via the DataChanged Signal, which is emitted each time set_data is called
    on an instance.

    Attributes:
        DataChanged ( QtCore.pyqtSignal[pathlib.Path]): Emitted with the
            path to the owner whenever set_data is called on the isntance
        owner (LeafNode): The owning LeafNode of the DtaObject.
    """

    DataChanged = QtCore.pyqtSignal(pathlib.Path)

    def __init__(self, owner: LeafNode, data: Any = None, *args, **kwargs):
        """initalize a new DataObject.

        Args:
            owner (LeafNode): The owning LeafNode of the DataObject.
            data (Any, optional): The data to store in the DataObject.
            *args: Passed to QtCore.QObject.__init__
            **kwargs: Passed to QtCore.QObject.__init__
        """
        super().__init__(*args, **kwargs)

        self.owner = owner
        self._data = data

    @property
    def data(self) -> Any:
        """Return the data stored in this DataObject

        Returns:
            Any: The stored data
        """
        return self._data

    @data.setter
    def data(self, d: Any) -> None:
        """Convinence setter to set the data of the DataObhect. Calls
        DataObject.set_data. DataChanged will be emitted on exit.

        Args:
            d (Any): The data to set.
        """
        self.set_data(d)

    def set_data(self, d: Any) -> None:
        """Set the data of the DataObhect. DataChanged will be emitted on exit.

        Args:
            d (Any): The data to set.
        """
        self._data = d
        self.emit_data_changed_signal()

    def emit_data_changed_signal(self):
        self.DataChanged.emit(self.owner.get_path())


class FilesystemError(Exception):

    """Emitted when a Filesystem operation fails. Baseclass for more precise
    Filesystem type errors.
    """


class DuplicateNodeNameError(FilesystemError):

    """Raised when trying to add a node to a NodeSet with a name that is
    already present in the NodeSet.
    """


class NodeDoesNotExistError(FilesystemError):

    """Raised when trying to acces a node that does not exist"""


class AbstractNode:

    """class AbstractNode

    Class providing common attributes and methods for all Node types. Not meant
    to be used directly.

    Attributes:
        name (str): The name of the node
        parent (Node): The parent Node instance of this node.
    """

    def __init__(
        self,
        name: str,
        parent: Node | None = None,
    ):
        """Initialize a new AbstractNode instance.

        Args:
            name (str): The name of the node.
            parent (Node | None, optional): The parent Node instance of this
                node.
        """
        self.name = name
        self.set_parent(parent)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, n: str) -> None:
        self._name = n

    @property
    def parent(self) -> Node | None:
        return self._parent

    @parent.setter
    def parent(self, p: Node | None) -> None:
        self.set_parent(p)

    def set_parent(self, parent: Node | None) -> None:
        """Set the parent of this node to parent. If parent is a Node instance,
        this node will take ownership of the current node and it will add
        itself to the list of child inodes of the new parent node. If it is
        None, and the node previously had a parent, it will no longer be owner
        by that parent and it will remove itself from the parents set of child
        nodes.

        Args:
            parent (Node | None): The new parent node of this node.
        """
        if (old_parent := getattr(self, "parent", None)) is not None:
            old_parent.children.remove(self.name)

        if parent is not None:
            parent.children.add(self)

        self._parent = parent

    def get_path(self) -> pathlib.Path:
        """Return a pathlib.Path instance pointing from the root of the tree
        this node is part to the node itself.

        Returns:
            pathlib.Path: The absolute path to this node.
        """
        path = pathlib.Path(self.name)

        while self.parent:
            self = self.parent
            path = self.name / path

        return path


class LeafNode(AbstractNode):

    """class LeafNode

    Class representing leafs in a Filesystem tree. LeafNodes are akin to
    regular File like objects in a file system, as they can carry data but
    can not have any child nodes, as opposed to directory like nodes.
    """

    def __init__(self, name: str, parent: Node | None, data: Any = None):
        """Initialize a new LeafNode.

        Args:
            name (str): The name of the node.
            parent (Node | None): The parent node of this node.
            data (object, optional): The data associated with this leaf node.
        """
        super().__init__(name=name, parent=parent)

        self._dataobj = DataObject(owner=self, data=data)

    @property
    def data(self) -> Any:
        return self._dataobj.data

    @data.setter
    def data(self, d: Any) -> None:
        self.set_data(d)

    def set_data(self, d: Any) -> None:
        self._dataobj.set_data(d)

    def watch(
        self, callback: Callable[[pathlib.Path], None]
    ) -> QtCore.QMetaObject.Connection:
        """Register a callback that is triggered whenver the data in this
        LeafNode changes. The callback recieves the absolute path to this
        node.

        Args:
            callback (Callable[[pathlib.Path], None]): The callback to invoke
                when the data associated with this leaf node changes.
        """
        return self._dataobj.DataChanged.connect(callback)

    def unwatch(self, *connections: QtCore.QMetaObject.Connection):
        self._dataobj.DataChanged.disconnect(*connections)


class Node(AbstractNode):

    def __init__(
        self,
        name: str,
        parent: Node | None = None,
        children: Iterable[Node] = []
    ):
        super().__init__(name=name, parent=parent)

        self._children = NodeSet(owner=self)
        for child in children:
            self.add_child(child)

    @property
    def children(self) -> NodeSet:
        """The NodeSet that stores the children of this node

        Returns:
            NodeSet: The NodeSet that stores the children of this node
        """
        return self._children

    def add_child(self, child: Node | LeafNode) -> None:
        """Add a new child node to the set of child nodes.

        Args:
            child (Node | LeafNode): The node to add as child. The current
                node will take ownership of the child node.
        """
        child.set_parent(self)

    def remove_child(self, name: str) -> Node | LeafNode:
        """Remove a node from the set of child nodes

        Args:
            name (str): The name of the node to remove. The child node will
                no longer be owned by the current node.

        Returns:
            Node | LeafNode: The removed node. It will no longer have a parent.

        Raises:
            NoSuchChildLeafNodeError: If the child does not exist.
        """

        try:
            child = self.children.get(name)
        except NodeDoesNotExistError as err:
            raise err from None

        child.set_parent(None)

        return child

    def get_child(self, name: str) -> Node | LeafNode:
        """Return the node with name equal to the given name

        Args:
            name (str): The name of the requested node

        Returns:
            Node | LeafNode: The node with name equal to the given name.

        Raises:
            NodeDoesNotExistError: If no child node with the given name exists.
        """
        try:
            child = self.children.get(name)
        except NodeDoesNotExistError as err:
            raise err from None

        return child

    def tree_repr(self, indent: int = 0) -> str:
        """Return a tree representation of the tree where the current node is
            the root and its children are the branches and leafs.

        Args:
            indent (int, optional): Internal variable not meant for using.
                Determines the indentation of the current level. Is used
                recursivley

        Returns:
            str: The tree representation of this node tree
        """
        string = f"{self.name}/"

        for kid in self.children:
            string += "\n" + "|  " * indent
            if isinstance(kid, Node):
                string += f"|__{kid.tree_repr(indent + 1)}"

            else:
                string += f"|__{kid.name}"

        return string


class NodeSet(Set[Node | LeafNode]):

    """class NodeSet

    Class storing a unique set of Nodes. Uniqueness of Nodes is based on
    their name. Each name can only exist once in the set.
    """

    def __init__(self, owner: Node, members: Iterable[Node | LeafNode] = []):
        """Initialize new LeafNodeChildSet"""
        self._owner = owner
        self._members: set[Node | LeafNode] = set()

        for member in members:
            self.add(member)

    def __iter__(self) -> Iterator[Node | LeafNode]:
        """Return an iterator of the members of the set

        Returns:
            Iterator[LeafNode]: The iterator returning the members of the set
        """
        return iter(self._members)

    def __len__(self) -> int:
        """Returns the number of members in the set.

        Returns:
            int: The number of LeafNodes in the set.
        """
        return len(self._members)

    def __contains__(self, name: object) -> bool:
        """If name is given as string, return true if a member with a name
        given to the equal name exists, false otherwise. If name is given as
        an AbstractNode instance, return true if the node itself is member of
        the set, false otherwise. Any other object will raise a TypeErro

        Args:
            name (object): The name or an LeafNode isntance with the same
                name to test

        Returns:
            bool: True if an node with the tested name exists, false otherwise

        Raises:
            TypeError: If name is not an instance of object or AbstractNode
        """
        if not isinstance(name, (str, AbstractNode)):
            raise TypeError(f"Expected str or AbstractNode, got {type(name)}")

        elif isinstance(name, AbstractNode):
            result = name in self._members

        else:
            result = any(node.name == name for node in self)

        return result

    def __bool__(self) -> bool:
        """Determines the truth value of the set

        Returns:
            bool: Returns false if the set is empty else true
        """
        return bool(self._members)

    def add(self, node: Node | LeafNode) -> None:
        """Adds another node to the set of child nodes

        Args:
            node (Node | LeafNode): The node to add

        Raises:
            DuplicateNodeNameError: If a node with the same name
                already exists in the set.
            TypeError: If node is not an instance of AbstractNode
        """
        if not isinstance(node, AbstractNode):
            raise TypeError(f"Expected instance of {AbstractNode}, got "
                            f"{type(node)}")

        if node in self:
            raise DuplicateNodeNameError(node.name)

        self._members.add(node)

    def get(self, name: str) -> Node | LeafNode:
        """Return the node with name equal to the given name.

        Args:
            name (str): The name of the node to return

        Returns:
            Node | LeafNode: The node with name equal to the given name

        Raises:
            NodeDoesNotExistError: If no node with the given name exsits in
                the set
        """
        member: Node | LeafNode

        for member in self:
            if member.name == name:
                break
        else:
            raise NodeDoesNotExistError(name)

        return member

    def remove(self, name: str) -> Node | LeafNode:
        """Remove node with name equal to the given name from the set.

        Args:
            name (str): The name of the node to remove.

        Returns:
            Node | LeafNode: The removed node

        Raises:
            NodeDoesNotExistError: If no node with the given name exists.
        """
        for member in self:
            if member.name == name:
                self._members.remove(member)
                break
        else:
            raise NodeDoesNotExistError(name)

        return member


class InvalidPathError(FilesystemError):
    pass


class Filesystem:
    def __init__(self):

        # root node of the filesystem
        self._root = Node(name="/")

    @property
    def root(self) -> Node:
        return self._root

    def get_node(self, path: str | pathlib.Path) -> Node | LeafNode:
        path = pathlib.Path(path)
        root, *parts = path.parts

        if root == self.root.name:
            node = self.root
        else:
            try:
                node = self.root.get_child(root)
            except NodeDoesNotExistError as err:
                raise err from None

        for part in parts:
            try:
                node = node.get_child(part)

            except NodeDoesNotExistError as err:
                raise err from None

        return node

    def remove_node(self, path: str | pathlib.Path) -> Node | LeafNode:
        path = pathlib.Path(path)

        try:
            node = self.get_node(path.parent)
        except NodeDoesNotExistError:
            raise InvalidPathError(path)

        if not isinstance(node, Node):
            raise InvalidPathError(path)

        return node.remove_child(path.name)

    def move_node(
        self,
        source_path: str | pathlib.Path,
        target_path: str | pathlib.Path
    ) -> None:
        source_path = pathlib.Path(source_path)
        target_path = pathlib.Path(target_path)

        if not source_path.name:
            raise InvalidPathError(f"Invalid source: {source_path}")

        elif not target_path.name:
            raise InvalidPathError(f"Invalid target: {target_path}")

        try:
            source = self.get_node(source_path)
        except NodeDoesNotExistError:
            msg = f"Source does not exist: {source_path}"
            raise InvalidPathError(msg) from None

        try:
            target = self.get_node(target_path)
        except NodeDoesNotExistError:
            # if the last INode in target_path does not exist but its parent
            # does, the last INode in target_path is the new name of the last
            # INode in source_path. I.e it gets renamed as in bash mv command.
            try:
                target = self.get_node(target_path.parent)
            except NodeDoesNotExistError:
                msg = f"Target does not exist: {target_path}"
                raise InvalidPathError(msg) from None

            source.name = target_path.name

        if not isinstance(target, Node):
            raise InvalidPathError(f"Invalid target: {target}")

        source.set_parent(target)


class ChangeDirContextManager:
    def __init__(self, shell, target_dir):
        self._shell = shell
        self._target = target_dir

    def __enter__(self):
        self._pwd = self._shell.pwd()
        self._shell.cd(self._target)

        return self._shell

    def __exit__(self, type, value, traceback):
        self._shell.cd(self._pwd)


class StupidlySimpleShell:
    def __init__(self):
        self._filesystem = Filesystem()

        self._cwd = self.filesystem.get_node("/")

    @property
    def filesystem(self) -> Filesystem:
        return self._filesystem

    def pwd(self) -> pathlib.Path:
        """Return the current working directory as pathlib.Path instance

        Returns:
            pathlib.Path: The current working directory
        """
        return self._cwd.get_path()

    def tree(self, path: str | pathlib.Path = ".") -> str:
        path = self.resolve_path(path)

        return self.filesystem.get_node(path).tree_repr()

    def resolve_path(self, path: str | pathlib.Path) -> pathlib.Path:
        """Return the absolute representation of path, with all relative parts
        resolved: 'this/is/a/loooong/../path' -> '/path/to/root/this/is/a/path'

        Args:
            path (str | pathlib.Path): The path to resolve

        Returns:
            pathlib.Path: The resolved, absolute path.

        Raises:
            InvalidPathError: Raised when the provided path cannot be resolved.
        """
        path = pathlib.Path(path)
        try:
            root, *parts = path.parts
        except ValueError:
            # if path is just the current dir, i.e. '.', there are not
            # enough values to unpack, but it is still a valid path.
            if str(path) != ".":
                raise InvalidPathError(path)

            root, parts = ".", []

        if root != self.filesystem.root.name:
            # this is a relative path to the cwd, make it absolute by
            # prepending the current work path and reset the root and parts
            path = self.pwd() / path
            root, *parts = path.parts

        if "." in parts or ".." in parts:
            # '.' just refers to the same dir as the previous part of the path
            # so we can just remove it, '..' refers to the second to last dir
            # in the path, so also remove the previous dir
            for idx, part in enumerate(parts):
                if part == ".":
                    del parts[idx]

                elif part == "..":
                    del parts[idx]
                    # if there are no more parts left we are at the root dir
                    if parts:
                        del parts[idx - 1]

            path = pathlib.Path(root)
            for part in parts:
                path /= part

        return path

    def cd(self, path: str | pathlib.Path) -> None:
        """Change the current working directory to path. All subsequent
        Filesystem operations will be relative to this directory.

        Args:
            path (str | pathlib.Path): The path to change to.
        """
        path = self.resolve_path(path)

        try:
            node = self.filesystem.get_node(path)
        except NodeDoesNotExistError:
            raise InvalidPathError(path) from None

        if not isinstance(node, Node):
            raise InvalidPathError(f"Not a directory: {path}")

        self._cwd = node

    def managed_cd(self, path: str | pathlib.Path) -> ChangeDirContextManager:
        """Create a context manager that changes the current working directory
        to path and return to the previous working directory on exit.

        Args:
            path (str | pathlib.Path): The path to change to when entering the
                context manager

        Returns:
            ChangeDirContextManager: The context manager that manages the
                change dir.
        """
        return ChangeDirContextManager(self, path)

    def mkdir(self, path: str | pathlib.Path, parents: bool = False) -> None:
        """Create a new directory at path. If parents is true all non-existing
        directories in path will also be created.

        Args:
            path (str | pathlib.Path): The path to the directory which should
                be created
            parents (bool, optional): Create non-existing directories in path
                on the fly if true, else raise an InvalidPathError if any
                directories in path do not exist.

        Raises:
            InvalidPathError: When parents is false and any of the directories
                in path do not exist.
        """

        path = self.resolve_path(path)

        if not path.name:
            raise InvalidPathError(path)

        if not parents:
            try:
                parent = self.filesystem.get_node(path.parent)
            except NodeDoesNotExistError:
                msg = f"No such directory: {path.parent}"
                raise InvalidPathError(msg) from None

            if not isinstance(parent, Node):
                raise InvalidPathError(f"Not a directory: {path}")

            try:
                Node(name=path.name, parent=parent)
            except DuplicateNodeNameError:
                msg = f"Directory already exists: {path}"
                raise InvalidPathError(msg) from None

        else:
            node = self.filesystem.get_node(path.root)

            if not isinstance(node, Node):
                raise InvalidPathError(path)

            for part in path.parts[1:]:
                try:
                    node = node.get_child(part)
                    if not isinstance(node, Node):
                        raise InvalidPathError(path)
                except NodeDoesNotExistError:
                    if not isinstance(node, Node):
                        raise InvalidPathError(path)

                    node = Node(name=part, parent=node)

    def mv(
        self,
        source_path: str | pathlib.Path,
        target_path: str | pathlib.Path
    ) -> None:
        """Move the directory in source_path to the directory specified in
        target_path. If the last directory in target_path does not exist, but
        the second to last does, the source_path directory gets renamed to the
        name of the last directory in target_path before it is moved. This is
        the same behaviour as the bash mv command.

        Args:
            source_path (str | pathlib.Path): The path to the directory to move
            target_path (str | pathlib.Path): The path to the directory which
                to move the source directory to
        """
        source_path = self.resolve_path(source_path)
        target_path = self.resolve_path(target_path)

        self.filesystem.move_node(source_path, target_path)

    def touch(
        self, path: pathlib.Path, file_type: type[LeafNode] = LeafNode
    ) -> None:
        path = self.resolve_path(path)

        if not path.name:
            raise InvalidPathError(path)

        try:
            parent = self.filesystem.get_node(path.parent)
        except NodeDoesNotExistError:
            raise InvalidPathError(path)

        if not isinstance(parent, Node):
            raise InvalidPathError(f"Not a directory: {path}")

        try:
            file_type(name=path.name, parent=parent)
        except DuplicateNodeNameError:
            raise InvalidPathError(f"Already exists: {path}") from None

    def get_data(self, path: str | pathlib.Path) -> Any:
        path = self.resolve_path(path)
        node = self.filesystem.get_node(path)
        if not isinstance(node, LeafNode):
            raise InvalidPathError(f"Not a file: {path}")

        return node.data

    def set_data(
        self, path: str | pathlib.Path, data: Any, *args, **kwargs
    ) -> None:
        path = self.resolve_path(path)
        node = self.filesystem.get_node(path)
        if not isinstance(node, LeafNode):
            raise InvalidPathError(f"Not a file: {path}")

        node.set_data(data, *args, **kwargs)

    def rm(
        self, path: str | pathlib.Path, recursive: bool = False
    ) -> Node | LeafNode:
        path = self.resolve_path(path)

        try:
            node = self.filesystem.get_node(path)
        except NodeDoesNotExistError:
            raise InvalidPathError(path) from None

        if isinstance(node, Node) and not recursive:
            raise InvalidPathError("Use recursive=true to remove directories!")

        elif not node.parent:
            raise InvalidPathError("Can't remove root!")

        return node.parent.remove_child(node.name)

    def ls(self, path: str | pathlib.Path = ".") -> list[str]:
        path = self.resolve_path(path)
        node = self.filesystem.get_node(path)
        if not isinstance(node, Node):
            raise InvalidPathError(f"Not a directory: {path}")

        return sorted(c.name for c in node.children)

    def watch_file(
        self, path: str | pathlib.Path, callback: Callable[[pathlib.Path], None]
    ) -> QtCore.QMetaObject.Connection:
        """Register a callback that will be triggered whenever the data
        stored in path changes. The callback will receive the path to the
        dataobject that has changed.

        Args:
            path (TYPE): The path to the dataobject to monitor
            callback (TYPE): The callback to invoke when the data in path has
                changed.
        """

        path = self.resolve_path(path)
        node = self.filesystem.get_node(path)

        if not isinstance(node, LeafNode):
            raise InvalidPathError(f"Not a file: {path}")

        return node.watch(callback)

    def unwatch_file(
        self,
        path: str | pathlib.Path,
        *connections: QtCore.QMetaObject.Connection
    ) -> None:
        path = self.resolve_path(path)
        node = self.filesystem.get_node(path)

        if not isinstance(node, LeafNode):
            raise InvalidPathError(f"Not a file: {path}")

        node.unwatch(*connections)
