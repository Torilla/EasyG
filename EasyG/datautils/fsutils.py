from collections import namedtuple

from EasyG.datautils import filesystem
from EasyG.network import client as _client


class TwoDimensionalPointArrayFile(filesystem.LeafNode):
    PointArray = namedtuple("PointArray", ("x", "y"))

    def __init__(self, name: str, parent: filesystem.Node | None = None):
        super().__init__(
            name=name,
            parent=parent,
            data=TwoDimensionalPointArrayFile.PointArray(x=[], y=[])
        )

    def set_data(
        self, data: tuple[list[float], list[float]] | list[float], action: str = "extend"
    ):
        x, y = data
        getattr(self.data.x, action)(x)
        getattr(self.data.y, action)(y)
        self.execute_callbacks()

    def clear_data(self):
        self.data.x.clear()
        self.data.y.clear()
        self.execute_callbacks()


class NoClientIDSetError(filesystem.FilesystemError):

    """Raised when trying to register a network client without clientID
    """


class NetworkClientFile(TwoDimensionalPointArrayFile):
    def set_client(self, client: _client.EasyGTCPClient):
        self.client = client
        self.client.newLineOfData.connect(self._store_data)

    def _store_data(self, data: list[float]):
        self.set_data(data, action="append")

    def start_parsing(self):
        self.client.startParsing()

    def stop_parsing(self):
        self.client.stopParsing()
