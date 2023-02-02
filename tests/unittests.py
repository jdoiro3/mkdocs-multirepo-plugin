import os
import pathlib
import stat
import subprocess
import sys
import unittest
from pathlib import Path
from shutil import copy

from aiofiles import tempfile

from mkdocs_multirepo_plugin import structure, util

SCRIPTS_DIR = Path.cwd() / "mkdocs_multirepo_plugin" / "scripts"
PYTHON_BIN = Path(sys.executable).parent
scripts = list(SCRIPTS_DIR.iterdir())


class BaseCase(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # move the script files to python bin
        for script in scripts:
            new_script = copy(script, PYTHON_BIN)
            # make executable by all
            file_stat = os.stat(new_script)
            os.chmod(
                new_script,
                file_stat.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            )

    def assertDirExists(self, dir: pathlib.Path):
        if not dir.is_dir():
            contents = []
            for p in dir.parent.rglob("*"):
                contents.append(p)
            raise AssertionError(
                f"Directory {str(dir)} doesn't exist.\nContents of {dir.parent.parent} are:\n{contents}"
            )

    def assertFileExists(self, path: pathlib.Path):
        if not path.is_file():
            raise AssertionError(f"File {str(path)} doesn't exist.")

    async def run_script_test(self, script: str, section: str):
        async with tempfile.TemporaryDirectory() as temp_dir:
            args = [
                "https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1",
                section,
                "main",
                "docs/*",
                "mkdocs.yml",
            ]
            temp_dir_path = pathlib.Path(temp_dir)
            await util.execute_bash_script(script, args, temp_dir_path)
            self.assertDirExists(temp_dir_path / section)
            docs_dir = temp_dir_path / section / "docs"
            self.assertDirExists(docs_dir)
            expected_files = [
                docs_dir / file
                for file in ["index.md", "mkdocs.yml", "page1.md", "page2.md"]
            ]
            for file in expected_files:
                self.assertFileExists(file)


class TestUtil(BaseCase):
    def test_remove_parents(self):
        test_cases = [
            (1, "root/subfolder", "/subfolder"),
            (2, "root/subfolder/subfolder2", "/subfolder2"),
            (3, "root/subfolder/subfolder2/subfolder3", "/subfolder3"),
            (0, "root/subfolder", "/root/subfolder"),
        ]
        for case in test_cases:
            self.assertEqual(util.remove_parents(case[1], case[0]), case[2])
        test_exception_cases = [
            (1, "root"),
            (2, "root/subfolder"),
            (3, "root/subfolder"),
            (3, "root"),
            (1, ""),
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

    maxDiff = None

    def test_resolve_nav_paths(self):
        section_name = "some_repo"
        nav = [
            {
                "Section1": [
                    {"Home": "folder/index.md"},
                    {"Section2": "folder/sub/page2.md"},
                ]
            },
            {"Home": "index.md"},
            {"Section2": [{"Section3": [{"Home": "index.md"}]}, {"Home": "index.md"}]},
        ]
        expected = [
            {
                "Section1": [
                    {"Home": "some_repo/folder/index.md"},
                    {"Section2": "some_repo/folder/sub/page2.md"},
                ]
            },
            {"Home": "some_repo/index.md"},
            {
                "Section2": [
                    {"Section3": [{"Home": "some_repo/index.md"}]},
                    {"Home": "some_repo/index.md"},
                ]
            },
        ]
        structure.resolve_nav_paths(nav, section_name)
        self.assertListEqual(nav, expected)

    def test_get_import_stmts(self):
        temp_dir = pathlib.Path("")
        nav = [
            "index.md",
            {"home": "home.md"},
            {
                "sec2": [
                    {"sec3": "bar.md"},
                    {
                        "sec4": [
                            {"sec5": "!import https://baz"},
                            {
                                "sec6": [
                                    {"sec7": "!import https://foo"},
                                    {"sec8": "foo.md"},
                                    {"sec12": "!import https://bar"},
                                ]
                            },
                        ]
                    },
                    {"sec9": [{"sec10": "index.md"}, {"sec11": "foo.md"}]},
                ]
            },
            {
                "sec13": [
                    {"sec14": "!import https://baz"},
                    {"sec15": "index.md"},
                    {
                        "sec16": [
                            {
                                "sec17": [
                                    {"sec18": "!import https://foo"},
                                    {"sec19": "index.md"},
                                ]
                            },
                            {"home": "index.md"},
                        ]
                    },
                ]
            },
        ]
        expected = [
            structure.NavImport(
                "sec5",
                nav[2]["sec2"][1]["sec4"][0],
                structure.DocsRepo(
                    name=str(Path("sec2/sec4/sec5")),
                    url="https://baz",
                    branch="master",
                    temp_dir=temp_dir,
                ),
            ),
            structure.NavImport(
                "sec7",
                nav[2]["sec2"][1]["sec4"][1]["sec6"][0],
                structure.DocsRepo(
                    name=str(Path("sec2/sec4/sec6/sec7")),
                    url="https://foo",
                    branch="master",
                    temp_dir=temp_dir,
                ),
            ),
            structure.NavImport(
                "sec12",
                nav[2]["sec2"][1]["sec4"][1]["sec6"][2],
                structure.DocsRepo(
                    name=str(Path("sec2/sec4/sec6/sec12")),
                    url="https://bar",
                    branch="master",
                    temp_dir=temp_dir,
                ),
            ),
            structure.NavImport(
                "sec14",
                nav[3]["sec13"][0],
                structure.DocsRepo(
                    name=str(Path("sec13/sec14")),
                    url="https://baz",
                    branch="master",
                    temp_dir=temp_dir,
                ),
            ),
            structure.NavImport(
                "sec18",
                nav[3]["sec13"][2]["sec16"][0]["sec17"][0],
                structure.DocsRepo(
                    name=str(Path("sec13/sec16/sec17/sec18")),
                    url="https://foo",
                    branch="master",
                    temp_dir=temp_dir,
                ),
            ),
        ]
        self.assertListEqual(
            structure.get_import_stmts(nav, temp_dir, "master"), expected
        )
        # make sure we're treating function as first class object
        # read more here: https://stackoverflow.com/a/1145781/10044811
        self.assertListEqual(
            structure.get_import_stmts(nav, temp_dir, "master"), expected
        )

    def test_parse_repo_url(self):
        base_url = "https://github.com/backstage/backstage"
        repo_url_cases = [
            (f"{base_url}", {"url": base_url}),
            (f"{base_url}?branch=master", {"url": base_url, "branch": "master"}),
            (
                f"{base_url}?branch=main&multi_docs=true",
                {"url": base_url, "branch": "main", "multi_docs": "true"},
            ),
            (
                f"{base_url}?multi_docs=false&branch=main",
                {"url": base_url, "multi_docs": "false", "branch": "main"},
            ),
            (
                f"{base_url}?docs_dir=fldr/docs/*",
                {"url": base_url, "docs_dir": "fldr/docs/*"},
            ),
            (
                f"{base_url}?multi_docs=false&branch=main&config=multirepo.yml",
                {
                    "url": base_url,
                    "multi_docs": "false",
                    "branch": "main",
                    "config": "multirepo.yml",
                },
            ),
            (
                f'{base_url}?multi_docs=false&branch=main&config=multirepo.yml&extra_imports=["README.md", "src/*"]',
                {
                    "url": base_url,
                    "multi_docs": "false",
                    "branch": "main",
                    "config": "multirepo.yml",
                    "extra_imports": ["README.md", "src/*"],
                },
            ),
        ]
        for case in repo_url_cases:
            parsed_url = structure.parse_repo_url(case[0])
            self.assertDictEqual(parsed_url, case[1])
        with self.assertRaises(util.ImportSyntaxError):
            structure.parse_repo_url(
                f"{base_url}?docs_dir=fldr/docs/*?config=multirepo.yml"
            )

    async def test_sparse_clone(self):
        async with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = pathlib.Path(temp_dir)
            repo = structure.Repo(
                "test-repo",
                "https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1",
                "main",
                temp_dir_path,
            )
            await repo.sparse_clone(["docs/*"])
            # make sure repo location is correct
            self.assertEqual(repo.location, pathlib.Path(temp_dir) / "test-repo")
            docs_dir = pathlib.Path(repo.location) / "docs"
            self.assertDirExists(docs_dir)
            expected_files = [
                docs_dir / file
                for file in ["index.md", "mkdocs.yml", "page1.md", "page2.md"]
            ]
            for file in expected_files:
                self.assertFileExists(file)

    async def test_sparse_clone_with_section_spaces(self):
        async with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = pathlib.Path(temp_dir)
            repo = structure.Repo(
                "test-repo",
                "https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1",
                "main",
                temp_dir_path,
            )
            await repo.sparse_clone(["docs/*"])
            # make sure the repo location is correct
            self.assertEqual(repo.location, pathlib.Path(temp_dir) / "test-repo")
            # make sure directory with spaces exists
            self.assertDirExists(repo.location)
            docs_dir = repo.location / "docs"
            self.assertDirExists(docs_dir)
            expected_files = [
                docs_dir / file
                for file in ["index.md", "mkdocs.yml", "page1.md", "page2.md"]
            ]
            for file in expected_files:
                self.assertFileExists(file)

    async def test_load_config(self):
        async with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = pathlib.Path(temp_dir)
            repo = structure.Repo(
                "test_repo",
                "https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1",
                "main",
                temp_dir_path,
            )
            await repo.sparse_clone(["docs/*"])
            docs_dir = pathlib.Path(repo.location) / "docs"
            self.assertDirExists(docs_dir)
            expected_files = [
                docs_dir / file
                for file in ["index.md", "mkdocs.yml", "page1.md", "page2.md"]
            ]
            for file in expected_files:
                self.assertFileExists(file)
            yml_dict = repo.load_config("docs/mkdocs.yml")
            self.assertDictEqual(
                yml_dict,
                {
                    "edit_uri": "/blob/master/",
                    "nav": [
                        {"Home": "index.md"},
                        {"Page1": "page1.md"},
                        {"Page2": "page2.md"},
                    ],
                },
            )
            with self.assertRaises(structure.ImportDocsException):
                yml_dict = repo.load_config("")
            with self.assertRaises(structure.ImportDocsException):
                repo = structure.Repo(
                    "test_repo",
                    "https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1",
                    "main",
                    temp_dir_path,
                )
                yml_dict = repo.load_config("")

    async def test_extra_imports(self):
        async with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = pathlib.Path(temp_dir)
            docsRepo = structure.DocsRepo(
                name="test-repo",
                url="https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1",
                temp_dir=temp_dir_path,
                docs_dir="docs/*",
                branch="main",
                edit_uri="/test",
                multi_docs=False,
                extra_imports=["src/*"],
            )
            await docsRepo.import_docs()
            expected_files = [
                docsRepo.location / file
                for file in ["index.md", "mkdocs.yml", "page1.md", "page2.md"]
            ]
            expected_src_files = [
                docsRepo.location / "src" / file for file in ["script.py"]
            ]
            for file in expected_files + expected_src_files:
                self.assertFileExists(file)

    async def test_keep_docs_dir(self):
        async with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = pathlib.Path(temp_dir)
            docsRepo = structure.DocsRepo(
                name="test-repo",
                url="https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1",
                temp_dir=temp_dir_path,
                docs_dir="docs/*",
                branch="main",
                edit_uri="/test",
                multi_docs=False,
                keep_docs_dir=True,
            )
            await docsRepo.import_docs()
            expected_files = [
                docsRepo.location / "docs" / file
                for file in ["index.md", "mkdocs.yml", "page1.md", "page2.md"]
            ]
            for file in expected_files:
                self.assertFileExists(file)

    async def test_multi_docs(self):
        async with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = pathlib.Path(temp_dir)
            docsRepo = structure.DocsRepo(
                name="test-repo",
                url="https://github.com/jdoiro3/mkdocs-multirepo-demoRepo1",
                temp_dir=temp_dir_path,
                docs_dir="docs/*",
                branch="test-multi-docs",
                edit_uri="/test",
                multi_docs=True,
            )
            await docsRepo.import_docs()
            expected_files = [
                docsRepo.location / path
                for path in [
                    "package1/index.md",
                    "package2/index.md",
                    "package1/getting-started/page.md",
                    "index.md",
                    "mkdocs.yml",
                    "page1.md",
                    "page2.md",
                ]
            ]
            for file in expected_files:
                self.assertFileExists(file)


if __name__ == "__main__":
    unittest.main()
