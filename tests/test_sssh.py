import unittest

from EasyG.datamanager import filesystem


class TestFileSystemBasics(unittest.TestCase):

    """Test basic functionaly of the SsSh"""

    def setUp(self):
        self.fs = filesystem.FileSystem()

    def test_cant_remove_root(self):
        with self.assertRaises(filesystem.InvalidPathError):
            self.fs.rmdir("/")

    def test_cant_remove_non_existent_dir(self):
        with self.assertRaises(filesystem.InvalidPathError):
            self.fs.rmdir("a")

    def test_can_create_simple_directory(self):
        self.assertIsNone(self.fs.mkdir("a"))
        self.assertIsNone(self.fs.mkdir("b"))
        self.assertIsNone(self.fs.mkdir("a/b"))
        self.assertIsNone(self.fs.mkdir("a/b/c"))
        self.assertIsNone(self.fs.mkdir("a/b/c/ d"))

    def test_can_create_nested_directories(self):
        self.assertIsNone(self.fs.mkdir("a/b", parents=True))
        self.assertIsNone(self.fs.mkdir("a/b/c", parents=True))
        self.assertIsNone(self.fs.mkdir("b/c/d", parents=True))
        self.assertIsNone(self.fs.mkdir("b/c/d/e/f/g", parents=True))

    def test_can_set_and_retrieve_data(self):
        data = "test"
        data2 = "test2"
        self.fs.mkdir("a", data=data)
        self.assertEqual(self.fs.get_data("a"), data)
        self.fs.set_data("a", data2)
        self.assertEqual(self.fs.get_data("a"), data2)

    def test_new_node_is_empty(self):
        self.assertIsNone(self.fs.get_data("/"))

        self.fs.mkdir("a")
        self.assertIsNone(self.fs.get_data("a"))

    def test_cant_get_nonexisting_data(self):
        with self.assertRaises(filesystem.NoSuchChildINodeError):
            self.fs.get_data("a")


class TestFileSystemAdvanced(unittest.TestCase):
    def setUp(self):
        self.fs = filesystem.FileSystem()
        self.fs.mkdir("a/aa/aaa", parents=True)
        self.fs.mkdir("a/ab/aba", parents=True)
        self.fs.mkdir("b/ba/baa", parents=True)
        self.fs.mkdir("b/bb/bba", parents=True)

    def test_can_remove_dir(self):
        self.assertIsNone(self.fs.rmdir("a"))

    def test_can_change_directory_absolute(self):
        self.assertIsNone(self.fs.cd("/a"))
        self.assertIsNone(self.fs.cd("/b"))
        self.assertIsNone(self.fs.cd("/"))
        self.assertIsNone(self.fs.cd("/a/aa"))
        self.assertIsNone(self.fs.cd("/a/ab/aba"))

    def test_can_change_directory_relative(self):
        self.assertIsNone(self.fs.cd("a"))
        self.assertIsNone(self.fs.cd("aa"))
        self.assertIsNone(self.fs.cd("aaa"))
        self.assertIsNone(self.fs.cd(".."))
        self.assertIsNone(self.fs.cd(".."))
        self.assertIsNone(self.fs.cd("ab"))

    def test_can_move_existing_dir(self):
        self.assertIsNone(self.fs.mv("a", "b"))
        self.assertIsNone(self.fs.cd("b/a/aa"))
        self.assertIsNone(self.fs.mv("aaa", "aba"))

    def test_cant_move_nonexisting_dir(self):
        with self.assertRaises(filesystem.NoSuchChildINodeError):
            self.fs.mv("c", "a")

        with self.assertRaises(filesystem.InvalidPathError):
            self.fs.mv("a", "c/a")

    def test_cant_move_root(self):
        with self.assertRaises(filesystem.InvalidPathError):
            self.fs.mv("/", "a")

    def test_cant_move_if_existing(self):
        self.fs.mv("a/aa/aaa", "a/aa/aba")

        with self.assertRaises(filesystem.ChildINodeAlreayExistsError):
            self.fs.mv("a/aa/aba", "a/ab")


if __name__ == "__main__":
    unittest.main()
