import unittest
from mkdocs_multirepo_plugin import util
from mkdocs_multirepo_plugin import structure

class Tests(unittest.TestCase):

    def test_remove_parents(self):
        test_cases = [
            (1, "root/subfolder", "/subfolder"),
            (2, "root/subfolder/subfolder2", "/subfolder2"), 
            (3, "root/subfolder/subfolder2/subfolder3", "/subfolder3")
        ]
        for case in test_cases:
            self.assertEqual(
                util.remove_parents(case[1], case[0]),
                case[2]
                )
        test_exception_cases = [
            (1, "root"), (2, "root/subfolder"),
            (3, "root/subfolder")
        ]
        for case in test_exception_cases:
            with self.assertRaises(ValueError):
                util.remove_parents(case[1], case[0])

    def test_resolve_nav_paths(self):
        section_name = "some_repo"
        nav = [
            {"Section1": [{"Home": "folder/index.md"}, {"Section2": "folder/sub/page2.md"}]},
            {"Home": "index.md"}
            ]
        expected = [
            {"Section1": [{"Home": "some_repo/folder/index.md"}, {"Section2": "some_repo/folder/sub/page2.md"}]},
            {"Home": "some_repo/index.md"}
            ]
        structure.resolve_nav_paths(nav, section_name)
        self.assertListEqual(nav, expected)


if __name__ == '__main__':
    unittest.main()
