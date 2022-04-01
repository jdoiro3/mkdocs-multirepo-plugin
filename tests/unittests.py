import unittest
from mkdocs_multirepo_plugin import util
from mkdocs_multirepo_plugin import structure
from aiofiles import tempfile
import pathlib


class BaseCase(unittest.IsolatedAsyncioTestCase):

    def assertDirExists(self, dir: pathlib.Path):
        if not dir.is_dir():
            raise AssertionError(f"Directory {str(dir)} doesn't exist.")

    def assertFileExists(self, path: pathlib.Path):
        if not path.is_file():
            raise AssertionError(f"File {str(path)} doesn't exist.")

    async def run_script_test(self, script: str, section: str):
        async with tempfile.TemporaryDirectory() as temp_dir:
            args = [
                "https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1",
                section, "main", "docs/*", "mkdocs.yml"
                ]
            temp_dir_path = pathlib.Path(temp_dir)
            await util.execute_bash_script(script, args, temp_dir_path)
            self.assertDirExists(temp_dir_path / section)
            docs_dir = temp_dir_path / section / "docs"
            self.assertDirExists(docs_dir)
            expected_files = [
                docs_dir / file for file in
                ["index.md", "mkdocs.yml", "page1.md", "page2.md"]
                ]
            for file in expected_files:
                self.assertFileExists(file)


class TestUtil(BaseCase):

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

    async def test_sparse_clone(self):
        await self.run_script_test("sparse_clone.sh", "test_docs")

    async def test_sparse_clone_old(self):
        await self.run_script_test("sparse_clone_old.sh", "test_docs")

    async def test_section_with_spaces(self):
        await self.run_script_test("sparse_clone.sh", "has spaces")

    async def test_section_with_spaces_old(self):
        await self.run_script_test("sparse_clone_old.sh", "has spaces")


class TestStructure(BaseCase):

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

    def test_parse_repo_url(self):
        base_url = "https://github.com/backstage/backstage"
        repo_url_cases = [
            (f"{base_url}", {"url": base_url}),
            (f"{base_url}?branch=master", {"url": base_url, "branch": "master"}),
            (f"{base_url}?branch=main?multi_docs=true", {"url": base_url, "branch": "main", "multi_docs": "true"}),
            (f"{base_url}?multi_docs=false?branch=main", {"url": base_url, "multi_docs": "false", "branch": "main"}),
            (f"{base_url}?docs_dir=fldr/docs/*", {"url": base_url, "docs_dir": "fldr/docs/*"}),
            (f"{base_url}?multi_docs=false?branch=main?config=multirepo.yml", {"url": base_url, "multi_docs": "false", "branch": "main", "config": "multirepo.yml"}),
        ]
        for case in repo_url_cases:
            parsed_url = structure.parse_repo_url(case[0])
            self.assertDictEqual(parsed_url, case[1])

    """
    async def test_sparse_clone(self):
        async with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = pathlib.Path(temp_dir)
            repo = structure.Repo(
                "test_repo", "https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1", "main",
                temp_dir_path
            )
            await repo.sparse_clone(["docs/*"])
            # make sure repo location is correct
            self.assertEqual(repo.location, pathlib.Path(temp_dir) / "test_repo")
            docs_dir = pathlib.Path(repo.location) / "docs"
            self.assertDirExists(docs_dir)
            expected_files = [
                docs_dir / file for file in
                ["index.md", "mkdocs.yml", "page1.md", "page2.md"]
                ]
            for file in expected_files:
                self.assertFileExists(file)

    async def test_sparse_clone_with_section_spaces(self):
        async with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = pathlib.Path(temp_dir)
            repo = structure.Repo(
                "test repo", "https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1", "main",
                temp_dir_path
            )
            await repo.sparse_clone(["docs/*"])
            # make sure the repo locaton is correct
            self.assertEqual(repo.location, pathlib.Path(temp_dir) / "test repo")
            # make sure directory with spaces exists
            self.assertDirExists(repo.location)
            docs_dir = repo.location / "docs"
            self.assertDirExists(docs_dir)
            expected_files = [
                docs_dir / file for file in
                ["index.md", "mkdocs.yml", "page1.md", "page2.md"]
                ]
            for file in expected_files:
                self.assertFileExists(file)

    async def test_load_config(self):
        async with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = pathlib.Path(temp_dir)
            repo = structure.Repo(
                "test_repo", "https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1", "main",
                temp_dir_path
                )
            await repo.sparse_clone(["docs/*"])
            docs_dir = pathlib.Path(repo.location) / "docs"
            self.assertDirExists(docs_dir)
            expected_files = [
                docs_dir / file for file in
                ["index.md", "mkdocs.yml", "page1.md", "page2.md"]
                ]
            for file in expected_files:
                self.assertFileExists(file)
            yml_dict = repo.load_config("docs/mkdocs.yml")
            self.assertDictEqual(
                yml_dict,
                {
                    'edit_uri': '/blob/master/',
                    'nav': [
                        {'Home': 'index.md'}, {'Page1': 'page1.md'}, {'Page2': 'page2.md'}
                        ]
                    }
                )
            with self.assertRaises(structure.ImportDocsException):
                yml_dict = repo.load_config("")
            with self.assertRaises(structure.ImportDocsException):
                repo = structure.Repo(
                    "test_repo", "https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1", "main",
                    temp_dir_path
                )
                yml_dict = repo.load_config("")
    """


if __name__ == '__main__':
    unittest.main()
