import unittest

from EasyG.datamanager import filesystem


class TestSsSh_Basics(unittest.TestCase):

    """Test basic functionaly of the SsSh
    """

    def setUp(self):
        self.sssh = filesystem.StupidlySimpleShell()

    def test_cant_remove_root(self):
        with self.assertRaises(filesystem.InvalidPathError):
            self.sssh.rmdir("/")

    def test_cant_remove_non_existent_dir(self):
        with self.assertRaises(filesystem.InvalidPathError):
            self.sssh.rmdir("a")

    def test_can_create_simple_directory(self):
        self.assertIsNone(self.sssh.mkdir("a"))
        self.assertIsNone(self.sssh.mkdir("b"))
        self.assertIsNone(self.sssh.mkdir("a/b"))
        self.assertIsNone(self.sssh.mkdir("a/b/c"))
        self.assertIsNone(self.sssh.mkdir("a/b/c/d"))

    def test_can_create_nested_directories(self):
        self.assertIsNone(self.sssh.mkdir("a/b", parents=True))
        self.assertIsNone(self.sssh.mkdir("a/b/c", parents=True))
        self.assertIsNone(self.sssh.mkdir("b/c/d", parents=True))
        self.assertIsNone(self.sssh.mkdir("b/c/d/e/f/g", parents=True))

    def test_can_set_and_retrieve_data(self):
        data = "test"
        data2 = "test2"
        self.sssh.mkdir("a", data=data)
        self.assertEqual(self.sssh.getData("a"), data)
        self.sssh.setData("a", data2)
        self.assertEqual(self.sssh.getData("a"), data2)

    def test_new_node_is_empty(self):
        self.assertIsNone(self.sssh.getData("/"))

        self.sssh.mkdir("a")
        self.assertIsNone(self.sssh.getData("a"))

    def test_cant_get_nonexisting_data(self):
        with self.assertRaises(filesystem.NoSuchChildINodeError):
            self.sssh.getData("a")


class TestSsSh_Advanced(unittest.TestCase):
    def setUp(self):
        self.sssh = filesystem.StupidlySimpleShell()
        self.sssh.mkdir("a/aa/aaa", parents=True)
        self.sssh.mkdir("a/ab/aba", parents=True)
        self.sssh.mkdir("b/ba/baa", parents=True)
        self.sssh.mkdir("b/bb/bba", parents=True)

    def test_can_remove_dir(self):
        self.assertIsNone(self.sssh.rmdir("a"))

    def test_can_change_directory_absolute(self):
        self.assertIsNone(self.sssh.cd("/a"))
        self.assertIsNone(self.sssh.cd("/b"))
        self.assertIsNone(self.sssh.cd("/"))
        self.assertIsNone(self.sssh.cd("/a/aa"))
        self.assertIsNone(self.sssh.cd("/a/ab/aba"))

    def test_can_change_directory_relative(self):
        self.assertIsNone(self.sssh.cd("a"))
        self.assertIsNone(self.sssh.cd("aa"))
        self.assertIsNone(self.sssh.cd("aaa"))
        self.assertIsNone(self.sssh.cd(".."))
        self.assertIsNone(self.sssh.cd(".."))
        self.assertIsNone(self.sssh.cd("ab"))

    def test_can_move_existing_dir(self):
        self.assertIsNone(self.sssh.mv("a", "b"))
        self.assertIsNone(self.sssh.cd("b/a/aa"))
        self.assertIsNone(self.sssh.mv("aaa", "aba"))

    def test_cant_move_nonexisting_dir(self):
        with self.assertRaises(filesystem.NoSuchChildINodeError):
            self.sssh.mv("c", "a")

        with self.assertRaises(filesystem.InvalidPathError):
            self.sssh.mv("a", "c/a")

    def test_cant_move_root(self):
        with self.assertRaises(filesystem.InvalidPathError):
            self.sssh.mv("/", "a")

    def test_cant_move_if_existing(self):
        self.sssh.mv("a/aa/aaa", "a/aa/aba")

        with self.assertRaises(filesystem.ChildINodeAlreayExistsError):
            self.sssh.mv("a/aa/aba", "a/ab")


if __name__ == "__main__":
    unittest.main()
