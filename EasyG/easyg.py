from .utils import Singleton


class EasyG(Singleton):
    def __init__(self, cpu, gui, datamanager):
        super().__init__()

        self.cpu = cpu
        self.gui = gui
        self.datamanager = datamanager
