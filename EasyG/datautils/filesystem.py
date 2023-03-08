from __future__ import annotations
from typing import Any, Iterator, Callable

from collections import namedtuple
import pathlib


from PyQt5 import QtCore


class FileSystemError(Exception):

    """Base Exception common as parent for all FileSystem Errors"""


class ChildINodeAlreayExistsError(FileSystemError):

    """Raised when attempting to add a child INode with an ID that is already
    present in the INodeChildSet
    """


class NoSuchChildINodeError(FileSystemError):

    """Raised when trying to access an INode that does not exist"""


class INodeChildSet:

    """class INodeChildSet

    Class storing a unique set of INodes. Uniqueness of INodes is based on
    their name. Each name can only exist once in the set.
    """

    def __init__(self, owner: INode):
        """Initialize new INodeChildSet"""
        self._members: set[INode] = set()
        self._owner = owner

    def __iter__(self) -> Iterator[INode]:
        """Return an iterator of the members of the set

        Returns:
            Iterator[INode]: The iterator returning the members of the set
        """
        return iter(self._members)

    def __len__(self) -> int:
        """Returns the number of members in the set.

        Returns:
            int: The number of INodes in the set.
        """
        return len(self._members)

    def __contains__(self, name: str | INode) -> bool:
        """Determins wether an INode with name equal to the given name exists

        Args:
            name (str | INode): The name or an INode with the same name to test

        Returns:
            bool: True if an INode with the tested name exists, false otherwise
        """
        if isinstance(name, INode):
            name = name.name

        return any(n.name == name for n in self) or name in (".", "..")

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
            raise TypeError(f"Expected instance of {INode}, got {type(node)}")

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

        if name == ".":
            member = self._owner

        elif name == "..":
            member = self._owner.parent or self._owner

        else:
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


class FileObjectAlreadyExistsError(FileSystemError):

    """Raised when trying to add a FileObject to an INode with a name that
    is already registered as file object.
    """


class NoSuchFileObjectError(FileSystemError):

    """Raised when trying to access a FileObject that does not exists"""


class FileObjectSet:

    """class FileObjectSet

    Class storing a unique set of FileObjects. Uniqueness of FileObejcts is
    based on their name. Each name can only exist once in the set.
    """

    def __init__(self):
        """Initialize new FileObjectSet"""
        self._members = set()

    def __iter__(self) -> Iterator[FileObject]:
        """Return an iterator of the members of the set

        Returns:
            Iterator[FileObject]: The iterator returning the members of the set
        """
        return iter(self._members)

    def __contains__(self, name: str | FileObject) -> bool:
        """Determins if a FileObject with name equal to the given name exists

        Args:
            name (str | FileObject): The name or the FileObject with the same
                name to test

        Returns:
            bool: True if a FileObject with the tested name exists,
                false otherwise
        """
        if isinstance(name, FileObject):
            name = name.name

        return any(n.name == name for n in self)

    def __len__(self) -> int:
        """Returns the number of members in the set.

        Returns:
            int: The number of INodes in the set.
        """
        return len(self._members)

    def __bool__(self) -> bool:
        """Determines the truth value of the set

        Returns:
            bool: Returns false if the set is empty else true
        """
        return bool(self._members)

    def add(self, file: FileObject) -> None:
        """Adds another FileObject to the set

        Args:
            file (FileObject): The FileObject to add

        Raises:
            FileObjectAlreadyExistsError: If a FileObject with the same name
                already exists in the set
            TypeError: If file is not an instance of FileObject
        """
        if not isinstance(file, FileObject):
            raise TypeError(f"Expected {FileObject}, got {type(file)}")

        if file in self:
            raise FileObjectAlreadyExistsError(file.name)

        self._members.add(file)

    def get(self, name: str | FileObject) -> FileObject:
        """Return the FileObject with name equal to the given name

        Args:
            name (str | FileObject): The name of the FileObject or a FileObject
                with the same name

        Returns:
            FileObject: The FileObject with name equal to the given name

        Raises:
            NoSuchFileObjectError: If no FileObject with name equal to the
                given name is present
        """
        if isinstance(name, FileObject):
            name = name.name

        for member in self:
            if member.name == name:
                break
        else:
            raise NoSuchFileObjectError(name)

        return member

    def remove(self, name: str | FileObject) -> FileObject:
        """Removes a node from the set

        Args:
            name (str | FileObject): The name of the FileObject to remove or
                a FileObject with the same name

        Returns:
            FileObject: The removed member

        Raises:
            NoSuchFileObjectError: If no FileObject with the given name exists
        """
        if isinstance(name, FileObject):
            name = name.name

        for member in self:
            if member.name == name:
                self._members.remove(member)
                break

        else:
            raise NoSuchFileObjectError(name)

        return member


class FileObject(QtCore.QObject):

    """class FileObject

    class representing a single file like object that can be stored in an
    INode.
    """

    DataChanged = QtCore.pyqtSignal()

    def __init__(self, name: str, data: Any = None, *args, **kwargs):
        """Initialize a new FileObject.

        Args:
            data (Any, optional): The data to store in this FileObject
        """
        super().__init__(*args, **kwargs)
        self.name = name
        self._data = data

    def data(self) -> Any:
        return self._data

    def set_data(self, data: Any) -> None:
        self._data = data
        self.DataChanged.emit()


PointList2D: namedtuple[list[float], list[float]] = namedtuple("PointList2D",
                                                               ("x", "y"))


class PointListFileObject(FileObject):
    def __init__(self, name):
        super().__init__(name=name, data=PointList2D([], []))

    def set_data(self, *args, **kwargs):
        raise NotImplementedError("Can not set data directly.")

    def appendPoint(self, data: tuple[float, float]) -> None:
        x, y = data
        self._data.x.append(x)
        self._data.y.append(y)
        self.DataChanged.emit()

    def extendPoints(self, data: tuple[list[float], list[float]]) -> None:
        x, y = data
        self._data.x.extend(x)
        self._data.y.extend(y)
        self.DataChanged.emit()


class INode:

    """class INode
    Repesenting a single node in a file system tree structure. It can
    have a parent INode and any number of child INodes. If it has no parent
    INode, it is considered the root of the current tree.
    """

    def __init__(self, name: str, parent: INode | None = None):
        """Initalize a new INode

        Args:
            name (str): The name of the new INode.
            parent (INode | None, optional): The parent of the new INode
        """
        self.set_name(name)
        self.set_parent(parent)

        self._children = INodeChildSet(owner=self)
        self._files = FileObjectSet()

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

    @property
    def children(self) -> INodeChildSet:
        """The ChildINodeSet that stores the children of this INode

        Returns:
            INodeChildSet: The ChildINodeSet that stores the children of this
                INode
        """
        return self._children

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

    def tree(self, indent: int = 0) -> str:
        """Return a tree representation of the tree where the current INode is
            the root and its children are the leafs

        Args:
            indent (int, optional): Internal variable not meant for using

        Returns:
            str: The tree representation of this INode tree
        """
        string = f"{self.name}/"

        for file in self._files:
            string += "\n" + "|  " * indent + f"|__{file.name}"

        for kid in self.children:
            string += "\n" + "|  " * indent + f"|__{kid.tree(indent + 1)}"

        return string

    def add_file(self, file: FileObject) -> None:
        self._files.add(file)

    def remove_file(self, filename: str) -> FileObject:
        return self._files.remove(filename)

    def get_file(self, filename: str | FileObject) -> FileObject:
        return self._files.get(filename)

    def get_path(self) -> pathlib.Path:
        path = pathlib.Path(self.name)
        parent = self.parent
        while parent:
            path = parent.name / path
            parent = parent.parent

        return path

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
    pass


class FileSystem:
    def __init__(self):

        # root node of the filesystem
        self._root = INode(name="/")

    def get_INode(
        self, path: str | pathlib.Path, create_non_existing: bool = False
    ) -> INode:
        """Return the last INode present in path.

        Args:
            path (str | pathlib.Path): The path to the INode in question. If
                given as string, it is implicitly converted to a pathlib.Path
                instance.
            create_non_existing (bool, optional): If true, any non-existing
                INodes in path will be created on the fly. False by default

        Returns:
            INode: The requested INode

        Raises:
            NoSuchChildINodeError: If any of the INodes referenced in path do
                not exist and create_non_existing is False.
        """

        path = pathlib.Path(path)

        if not path.root:
            # we require absolute paths
            raise InvalidPathError(f"Path must start at root: {path}")

        parts = path.parts[1:]
        node = self._root

        for part in parts:
            try:
                node = node.get_child(part)
            except NoSuchChildINodeError as err:
                if create_non_existing:
                    node = INode(name=part, parent=node)

                else:
                    raise err from None

        return node

    def remove_INode(self, path: str | pathlib.Path) -> INode:
        path = pathlib.Path(path)

        if not path.name:
            raise InvalidPathError(path)

        return self.get_INode(path.parent).remove_child(path.name)

    def move_INode(self,
                   source_path: str | pathlib.Path,
                   target_path: str | pathlib.Path) -> None:
        source_path = pathlib.Path(source_path)
        target_path = pathlib.Path(target_path)

        if not source_path.name:
            raise InvalidPathError(f"Invalid source: {source_path}")

        elif not target_path.name:
            raise InvalidPathError(f"Invalid target: {target_path}")

        try:
            source = self.get_INode(source_path)
        except NoSuchChildINodeError:
            msg = f"Source does not exist: {source_path}"
            raise InvalidPathError(msg) from None

        try:
            target = self.get_INode(target_path)
        except NoSuchChildINodeError:
            # if the last INode in target_path does not exist but its parent
            # does, the last INode in target_path is the new name of the last
            # INode in source_path. I.e it gets renamed as in bash mv command.
            try:
                target = self.get_INode(target_path.parent)
            except NoSuchChildINodeError:
                msg = f"Target does not exist: {target_path}"
                raise InvalidPathError(msg) from None

            source.set_name(target_path.name)

        source.set_parent(target)

    def get_fileobject(self, path: str | pathlib.Path):
        path = pathlib.Path(path)
        target, filename = path.parent, path.name

        if not (target or filename):
            raise InvalidPathError(path)

        return self.get_INode(target).get_file(filename)


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
        self._fs = FileSystem()

        self._cwd = self._fs.get_INode("/")

    def pwd(self) -> pathlib.Path:
        """Return the current working directory as pathlib.Path instance

        Returns:
            pathlib.Path: The current working directory
        """
        return self._cwd.get_path()

    def cd(self, path: str | pathlib.Path) -> None:
        """Change the current working directory to path. All subsequent
        FileSystem operations will be relative to this directory.

        Args:
            path (str | pathlib.Path): The path to change to.
        """
        path = pathlib.Path(path)

        if not path.root:
            # relative path to the cwd, so prepend it to make an aboslute path
            path = self.pwd() / path

        self._cwd = self._fs.get_INode(path)

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
        path = pathlib.Path(path)
        if not path.name:
            raise InvalidPathError(path)

        if not path.root:
            path = self.pwd() / path

        if not parents:
            try:
                parent = self._fs.get_INode(path.parent)
            except NoSuchChildINodeError:
                msg = f"No such directory: {path.parent}"
                raise InvalidPathError(msg) from None

            try:
                INode(path.name, parent=parent)
            except ChildINodeAlreayExistsError:
                msg = f"Directory already exists: {path}"
                raise InvalidPathError(msg) from None

        else:
            self._fs.get_INode(path, create_non_existing=True)

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
        source_path = pathlib.Path(source_path)
        target_path = pathlib.Path(target_path)

        if not source_path.root:
            source_path = self.pwd() / source_path

        if not target_path.root:
            target_path = self.pwd() / target_path

        self._fs.move_INode(source_path, target_path)

    def touch(
        self, path: str | pathlib.Path, file_type=FileObject
    ) -> FileObject:
        """Create a new file_type instance at path. the name of the file
        will be the last directory in path.

        Args:
            path (str | pathlib.Path): The path with the name of the file
            file_type (TYPE, optional): The type of file that should be created
        """
        path = pathlib.Path(path)
        target, filename = path.parent, path.name

        if not filename:
            raise InvalidPathError(path)

        if not target.root:
            target = self.pwd() / target

        file = file_type(name=filename)

        self._fs.get_INode(target).add_file(file)

        return file

    def add_file(
        self, file: FileObject, path: str | pathlib.Path = "."
    ) -> None:
        """Add an existing FileObject to the directory in path

        Args:
            file (FileObject): The FileObject to add
            path (str | pathlib.Path, optional): The path to the directory
                where to add the file. The current working directory by default
        """
        path = pathlib.Path(path)
        if not path.root:
            path = self.pwd() / path

        self._fs.get_INode(path).add_file(file)

    def get_file(self, path: str | pathlib.Path) -> FileObject:
        """Return a FileObject instance stored at path.

        Args:
            path (str | pathlib.Path): The path where the FileObject is stored.

        Returns:
            FileObject: The requested FileObject
        """
        path = pathlib.Path(path)
        if not path.root:
            path = self.pwd() / path

        return self._fs.get_fileobject(path)

    def rm(self,
           path: str | pathlib.Path,
           recursive: bool = False) -> INode | FileObject:
        """Remove a file or directory from the filesystem.

        Args:
            path (str | pathlib.Path): The path to the directory or file which
                to remove
            recursive (bool, optional): If true, directories will be removed,
                otherwise only files can be remove and trying to remove a
                directory will raise and InvalidPathError

        Returns:
            INode | FileObject: The removed file or INode

        Raises:
            InvalidPathError: When recursive is false and trying to remove
                a directory instead of a file.
        """
        path = pathlib.Path(path)
        if not path.root:
            path = self.pwd() / path

        err = InvalidPathError(f"No such FileObject or INode: {path}")
        target, name = path.parent, path.name

        if not name:
            raise err

        try:
            node = self._fs.get_INode(target)
        except NoSuchChildINodeError:
            raise err from None

        try:
            node = node.remove_file(name)

        except NoSuchFileObjectError:
            if recursive:
                try:
                    node = node.remove_child(name)
                except NoSuchChildINodeError:
                    raise err from None

            else:
                if name in node.children:
                    msg = f"{path} is a directory. Use recursive=True"
                    err = InvalidPathError(msg)

                raise err from None

        return node

    def add_file_watcher(self, path, callback):
        """Register a callback that will be triggered whenever the data
        stored in path changes. The callback will receive the path to the
        dataobject that has changed.

        Args:
            path (TYPE): The path to the dataobject to monitor
            callback (TYPE): The callback to invoke when the data in path has
                changed.
        """
        path = pathlib.Path(path)
        if not path.root:
            path = self.pwd() / path

        self.get_file(path).DataChanged.connect(lambda: callback(path))
