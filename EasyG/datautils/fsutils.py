from collections import namedtuple
import pathlib

from EasyG.datautils import sssh
from EasyG.network import client as _client


class TwoDimensionalPointArrayFile(sssh.LeafNode):
    PointArray = namedtuple("PointArray", ("x", "y"))

    def __init__(self, name: str, parent: sssh.Node | None = None):
        super().__init__(
            name=name,
            parent=parent,
            data=TwoDimensionalPointArrayFile.PointArray(x=[], y=[]),
        )

    def set_data(
        self,
        data: tuple[list[float], list[float]] | list[float],
        action: str = "extend",
    ):
        x, y = data
        getattr(self.data.x, action)(x)
        getattr(self.data.y, action)(y)
        self.execute_callbacks()

    def clear_data(self):
        self.data.x.clear()
        self.data.y.clear()
        self.execute_callbacks()


class NoClientIDSetError(sssh.FilesystemError):

    """Raised when trying to register a network client without clientID"""


class NetworkClientFile(TwoDimensionalPointArrayFile):
    def set_client(self, client: _client.EasyGTCPClient):
        self.client = client
        self.client.newLineOfData.connect(self._store_data)

    def _store_data(self, data: list[float]):
        self.set_data(data, action="append")


shell_extensions: list = []


def shell_extension(func):
    if hasattr(sssh.StupidlySimpleShell, func.__name__):
        raise ValueError("Cannot override a function as shell extension!")

    elif any(f.__name__ == func.__name__ for f in shell_extensions):
        raise ValueError(f"Already registered: {func.__name__}")

    shell_extensions.append(func)

    return func


def load_shell_extensions():
    for func in shell_extensions:
        if not hasattr(sssh.StupidlySimpleShell, func.__name__):
            setattr(sssh.StupidlySimpleShell, func.__name__, func)


@shell_extension
@sssh.resolved_path(default_path=".")
def id(self, path: pathlib.Path) -> str:
    try:
        node = self.filesystem.get_node(path)
    except sssh.NodeDoesNotExistError:
        raise sssh.InvalidPathError(path) from None

    return str(hash(node))


@shell_extension
@sssh.resolved_path()
def set_client(self, path, client):
    try:
        node = self.filesystem.get_node(path)
    except sssh.NodeDoesNotExistError:
        raise sssh.InvalidPathError(path) from None

    if not isinstance(node, NetworkClientFile):
        raise sssh.InvalidPathError(f"Not a NetworkClientFile: {path}") from None

    node.set_client(client)
