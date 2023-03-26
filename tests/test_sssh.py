import unittest

import pathlib

from EasyG.datautils import filesystem


class TestFileSystemBasics(unittest.TestCase):

    """Test basic functionaly of the SsSh"""

    def setUp(self):
        self.shell = filesystem.StupidlySimpleShell()

    def test_cant_remove_root(self):
        root = self.shell.filesystem.root
        self.assertEqual(root.name, "/")

        with self.assertRaises(filesystem.InvalidPathError):
            self.shell.rm("/", recursive=True)

        self.assertIs(self.shell.filesystem.root, root)

    def test_cant_remove_non_existent_dir(self):
        with self.assertRaises(filesystem.InvalidPathError):
            self.shell.rm("a", recursive=True)

    def test_can_remove_existing_dir(self):
        self.shell.mkdir("/a/b", parents=True)
        self.shell.mkdir("/b/a", parents=True)

        self.assertEqual(self.shell.ls(), ["a", "b"])

        self.shell.cd("/a")
        self.assertEqual(self.shell.ls(), ["b"])
        self.shell.cd("..")

        self.assertIs(
            self.shell.filesystem.get_node("/a"),
            self.shell.rm("/a", recursive=True)
        )
        with self.assertRaises(filesystem.InvalidPathError):
            self.shell.cd("/a")

    def test_can_create_directories(self):
        self.shell.mkdir("a")
        self.shell.mkdir("a/b/c/ d", parents=True)
        self.assertEqual(self.shell.ls(), ["a"])
        self.shell.cd("a")
        self.assertEqual(self.shell.ls(), ["b"])
        self.assertEqual(self.shell.pwd(), pathlib.Path("/a"))
        self.shell.cd("b/c/ d")
        self.assertEqual(self.shell.pwd(), pathlib.Path("/a/b/c/ d"))
        self.assertEqual(self.shell.ls(), [])

    def test_can_move_directories(self):
        self.shell.mkdir("a")
        self.shell.mkdir("b")
        self.assertEqual(self.shell.ls(), ["a", "b"])
        self.shell.mv("a", "b")
        self.assertEqual(self.shell.ls(), ["b"])
        self.assertEqual(self.shell.ls("b"), ["a"])

    def test_can_set_and_retrieve_data(self):
        data = "test"
        self.shell.touch("a")
        self.shell.set_data("a", data)
        self.assertEqual(self.shell.get_data("a"), data)

        data2 = "test2"
        self.shell.mkdir("b")
        self.shell.touch("b/a")
        self.shell.set_data("b/a", data2)
        self.assertEqual(self.shell.get_data("b/a"), data2)
#
#    def test_new_node_is_empty(self):
#        self.assertIsNone(self.shell.get_data("/"))
#
#        self.shell.mkdir("a")
#        self.assertIsNone(self.shell.get_data("a"))
#
#    def test_cant_get_nonexisting_data(self):
#        with self.assertRaises(filesystem.NoSuchChildINodeError):
#            self.shell.get_data("a")


if __name__ == "__main__":
    unittest.main()
