from typing import Callable

from PyQt5 import QtCore

from EasyG.gui import guiwidgets
from EasyG.network import server as _server
from EasyG.network import client as _client
from EasyG.gui import widgets


class SignalConnector:

    """class SignalConnector

    This class takes care of storing connection elements for PyQt's signal
    and slot mechanism.
    """

    def __init__(self):
        """Initalize a new SignalConnector instance."""
        self._connections = {}

    def connect(
        self,
        source: QtCore.pyqtBoundSignal,
        target: QtCore.pyqtBoundSignal | Callable
    ) -> None:
        """Connect source signal to target slot and store the resulting
        connection object for later disconnection.

        Args:
            source (QtCore.pyqtBoundSignal): The signal which to connect the
                target slot to
            target (QtCore.pyqtBoundSignal | Callable): The slot which to
                connect to othe source signal
        """
        cons = self._connections[source] = self._connections.get(source, [])
        cons.append(source.connect(target))

    def disconnect(self, source: QtCore.pyqtBoundSignal) -> None:
        """Disconnect all connections of source.

        Args:
            source (QtCore.pyqtBoundSignal): The signal that will be fully
                disconnected from all stored connections
        """
        connections = self._connections.get(source, [])
        while connections:
            source.disconnect(connections.pop())

        if source in self._connections:
            del self._connections[source]


class ServerPlugin(QtCore.QObject):

    """class ServerPlugin

    This class handles the communication between the GUI and the server
    instance. It is responsible for setting the available elemnts in the GUI
    to enabled or disabled as appropriate.

    Attributes:
        NewClientAvailable (QtCore.pyqtSignal[_client.EasyGTCPClient]): Signal
            emitted when a new client is connecting to the server and has
            succesfully authenticated against the client database.
    """

    NewClientAvailable = QtCore.pyqtSignal(_client.EasyGTCPClient)

    def __init__(
        self,
        gui: guiwidgets.MainWindow,
        server: _server.EasyGAuthenticationServer | None = None,
        *args, **kwargs
    ):
        """Initalize a new ServerPlugin instance

        Args:
            gui (mainwindow.MainWindow): The active GUI which to manage the
                server section of
            server (_server.EasyGAuthenticationServer | None, optional): The
                underlying server implementation. If set to None, the Plugin
                will be disabled in the GUI.
            *args: Forwared to QtCore.QObject.__init__
            **kwargs: Forwared to QtCore.QObject.__init__
        """
        super().__init__(*args, **kwargs)
        self._connector = SignalConnector()

        self._gui = gui

        self._server_config_widget = widgets.ServerConfigurationWidget()
        self._server_config_widget.ConfigurationChanged.connect(
            self._server_config_widget_changed)

        self.set_server(server)

    def set_server(
        self, server: _server.EasyGAuthenticationServer | None
    ) -> _server.EasyGAuthenticationServer | None:
        """Set the underlying server instance to server. The old server, if
        any, will be closed and disconnected from the GUI and returned at the
        end.

        Args:
            server (_server.EasyGAuthenticationServer | None): The new server
            instance to use or None to disable the Plugin in the GUI.

        No Longer Returned:
            _server.EasyGAuthenticationServer | None: The oldServer instance
                if any
        """
        old_server = getattr(self, "_server", None)
        if old_server is not None:
            # stop old server and disconnect it
            self.stop_server()
            self._disconnect_server()

        # set gui to disabled by default if new server is None
        self._gui.serverMenu.setEnabled(False)
        self._gui.startServerAction.setEnabled(False)
        self._gui.stopServerAction.setEnabled(False)
        self._gui.configureServerAction.setEnabled(False)

        self._server = server
        if self._server is not None:
            self._gui.serverMenu.setEnabled(True)
            cfg = self._server.get_configuration()
            self._server_config_widget.set_configuration(cfg)
            self._gui.configureServerAction.setEnabled(True)

            self._connect_server()
            self._gui.startServerAction.setEnabled(True)

        return old_server

    def _disconnect_server(self) -> None:
        """Fully disconnect the server from the GUI"""
        assert self._server is not None, "must set a server first!"

        self._connector.disconnect(self._gui.startServerAction.triggered)
        self._connector.disconnect(self._gui.stopServerAction.triggered)
        self._connector.disconnect(self._gui.configureServerAction.triggered)
        self._connector.disconnect(self._server.NewClientAvailable)

    def _connect_server(self) -> None:
        """Fully connect the server to the GUI"""
        assert self._server is not None, "must set a server first!"

        self._connector.connect(self._gui.startServerAction.triggered,
                                self.start_server)
        self._connector.connect(self._gui.stopServerAction.triggered,
                                self.stop_server)
        self._connector.connect(self._gui.configureServerAction.triggered,
                                self._server_config_widget.show)
        self._connector.connect(self._server.NewClientAvailable,
                                self.NewClientAvailable)

    def _server_config_widget_changed(self) -> None:
        """Initialize a new server instance with the current GUI server config
        settings and set it as the new underlying server.
        """
        assert self._server is not None, "must set a server first!"

        config = self._server_config_widget.get_configuration()
        if config != self._server.get_configuration():
            server = _server.EasyGAuthenticationServer.from_configuration(config)
            self.set_server(server)
            self._gui.print_status("Updated server configuration.")

    def start_server(self) -> None:
        """Start the underlying server and listen for new clients."""
        assert self._server is not None, "must set a server first!"

        if not self._server.is_listening():
            try:
                self._server.start_listening()

            except OSError:
                err = self._server.error_string()
                status = f"Failed to start server: {err}"

            else:
                self._gui.startServerAction.setEnabled(False)
                self._gui.configureServerAction.setEnabled(False)
                self._gui.stopServerAction.setEnabled(True)
                address = self._server.server_address().toString()
                port = self._server.server_port()
                status = f"Server listening at {address}:{port}"

        else:
            address = self._server.server_address().toString()
            port = self._server.server_port()
            status = f"Server is listening at {address}:{port}"

        self._gui.print_status(status)

    def stop_server(self) -> None:
        """Stop the underlying server instance"""
        assert self._server is not None, "must set a server first!"

        if self._server.is_listening():
            self._server.close()
            self._gui.stopServerAction.setEnabled(False)
            self._gui.startServerAction.setEnabled(True)
            self._gui.configureServerAction.setEnabled(True)
            self._gui.print_status("Server stopped listening.")
