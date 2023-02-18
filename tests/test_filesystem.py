import unittest

from EasyG.datamanager import filesystem2


class TestFileSystem_Basics(unittest.TestCase):
    def setUp(self):
        self.fs = filesystem2.FileSystem()

    def test_root_is_named_correct(self):
        self.assertEqual(self.fs.root.ID, "/")

    def test_cant_remove_root(self):
        with self.assertRaises(filesystem2.InvalidPathError):
            self.fs.rmdir("/")

    def test_cant_remove_non_existent_dir(self):
        with self.assertRaises(filesystem2.InvalidPathError):
            self.fs.rmdir("a")

    def test_default_cwd_is_root(self):
        self.assertIs(self.fs.cwd, self.fs.root)

    def test_can_create_simple_directory(self):
        self.assertIsNone(self.fs.mkdir("a"))
        self.assertEqual(len(self.fs.root.children), 1)

        self.assertIsNone(self.fs.mkdir("b"))
        self.assertEqual(len(self.fs.root.children), 2)

        self.assertIsNone(self.fs.mkdir("a/b"))
        self.assertEqual(len(self.fs.root.children), 2)
        self.assertEqual(len(self.fs._getChildINode("a").children), 1)

        self.assertIsNone(self.fs.mkdir("a/b/c"))
        self.assertEqual(len(self.fs.root.children), 2)
        self.assertEqual(len(self.fs._getChildINode("a/b").children), 1)

        self.assertIsNone(self.fs.mkdir("a/b/c/d"))
        self.assertEqual(len(self.fs.root.children), 2)
        self.assertEqual(len(self.fs._getChildINode("a/b").children), 1)
        self.assertEqual(len(self.fs._getChildINode("a/b/c").children), 1)

    def test_can_create_nested_directories(self):
        self.assertIsNone(self.fs.mkdir("a/b", parents=True))
        self.assertIsNone(self.fs.mkdir("a/b/c", parents=True))
        self.assertIsNone(self.fs.mkdir("b/c/d", parents=True))
        self.assertIsNone(self.fs.mkdir("b/c/d/e/f/g", parents=True))


class TestFileSystem_Advanced(unittest.TestCase):
    def setUp(self):
        self.fs = filesystem2.FileSystem()
        self.fs.mkdir("a/aa/aaa", parents=True)
        self.fs.mkdir("a/ab/aba", parents=True)
        self.fs.mkdir("b/ba/baa", parents=True)
        self.fs.mkdir("b/bb/bba", parents=True)

    def test_can_remove_dir(self):
        path = "a"
        nChild = len(self.fs.root.children)
        self.assertIs(self.fs._getChildINode(path), self.fs.rmdir(path))
        self.assertEqual(len(self.fs.root.children), nChild - 1)

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


if __name__ == "__main__":
    unittest.main()
