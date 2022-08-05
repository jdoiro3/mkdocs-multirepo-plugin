from typing import Tuple, List, Dict, Union
import shutil
import subprocess
from pathlib import Path
from mkdocs.utils import yaml_load
from mkdocs.structure.files import File
from .util import (
    ImportDocsException, 
    git_supports_sparse_clone,
    remove_parents, 
    execute_bash_script, 
    ImportSyntaxError,
    ProgressList
)
import asyncio
import tqdm
import os
from slugify import slugify
import ast
import time


def is_yaml_file(file: File) -> bool:
    return os.path.splitext(file.src_path)[1] in (".yaml", ".yml")


def resolve_nav_paths(nav: List[Dict], section_name: str) -> None:
    """Adds the section_name to the beginning of all paths in a MkDocs nav object"""
    for index, entry in enumerate(nav):
        if isinstance(entry, str):
            nav[index] = str(section_name / Path(entry)).replace("\\", "/")
        elif isinstance(entry, dict):
            (key, value), = entry.items()
            if type(value) is list:
                resolve_nav_paths(value, section_name)
            else:
                nav[index][key] = str(section_name / Path(value)).replace("\\", "/")


def parse_repo_url(repo_url: str) -> Dict[str, str]:
    """Parses !import statement urls"""
    url_parts = repo_url.split("?")
    url_parts_len = len(url_parts)
    if url_parts_len > 2:
        raise ImportSyntaxError(
            f"The import statement's repo url, {repo_url}, can only contain one ?"
            )
    if url_parts_len == 1:
        url, query_str = url_parts[0], None
    else:
        url, query_str = url_parts[0], url_parts[1]
    if query_str:
        query_parts = query_str.split("&")
    else:
        query_parts = []
    import_parts = {"url": url}
    for part in query_parts:
        k, v = part.split("=")
        if v[0] == "[" and v[len(v)-1] == "]":
            try:
                import_parts[k] = [lst_v.strip() for lst_v in ast.literal_eval(v)]
            except ValueError:
                raise ImportSyntaxError(
                    f"{v} is not a properly formatted python list\nException raised for import statement: {repo_url}"
                    )
        else:
            import_parts[k] = v
    return import_parts


def parse_import(import_stmt: str) -> Tuple[str, str]:
    """Parses !import statements"""
    import_url = import_stmt.split(" ", 1)[1]
    return parse_repo_url(import_url)


class NavImport:
    """Represents a nav import statement (e.g., section: '!import {url}').

    Attributes:
        section (str): The nav section title.
        nav_entry_ptr (dict): A reference to the dictionary, within the nav, that holds this section.
        repo (DocsRepo): The docs repo object created after parsing the import statement.
    """

    def __init__(self, section: str, nav_entry_ptr: Dict[str, Union[List, str]], repo: "DocsRepo"):
        self.section = section
        self.repo = repo
        self.nav_entry_ptr = nav_entry_ptr

    def __eq__(self, other):
        return (
            isinstance(other, NavImport) and
            self.section == other.section and
            self.nav_entry_ptr == other.nav_entry_ptr and
            self.repo == other.repo
        )

    def __str__(self):
        return f"NavImport({self.nav_entry_ptr}, {self.repo})"

    def __repr__(self):
        return self.__str__()

    def set_section_value(self, new_val: Union[List, str]) -> None:
        if isinstance(new_val, str) or isinstance(new_val, list):
            self.nav_entry_ptr[self.section] = new_val
            return
        raise ValueError(f"new_val must be either a list or a str, not {type(new_val)}")


def get_import_stmts(
    nav: List[Dict], temp_dir: Path, default_branch: str, path_to_section: List[str] = None
        ) -> List[NavImport]:
    """Searches through the nav and finds import statements, returning a list of NavImport objects.
    The NavImport object contains, among other things, a reference to the dictionary in the nav that
    allows later updates to this nav entry in place.
    """
    imports: List[NavImport] = []
    if path_to_section is None:
        path_to_section = []
    for index, entry in enumerate(nav):
        if isinstance(entry, str):
            continue
        (section, value), = entry.items()
        path_to_section.append(section)
        if type(value) is list:
            imports += get_import_stmts(value, temp_dir, default_branch, path_to_section)
        elif value.startswith("!import"):
            import_stmt: Dict[str, str] = parse_import(value)
            # slugify the section names and turn them into a valid path string
            path = str(Path(*[slugify(section) for section in path_to_section]))
            repo = DocsRepo(
                        name=path, url=import_stmt.get("url"),
                        temp_dir=temp_dir, docs_dir=import_stmt.get("docs_dir", "docs/*"),
                        branch=import_stmt.get("branch", default_branch),
                        multi_docs=bool(import_stmt.get("multi_docs", False)),
                        config=import_stmt.get("config", "mkdocs.yml"),
                        extra_imports=import_stmt.get("extra_imports", [])
                    )
            imports.append(NavImport(section, nav[index], repo))
            path_to_section.pop()
        else:
            path_to_section.pop()
    try:
        path_to_section.pop()
    except IndexError:
        pass
    return imports


class Repo:
    """Represents a Git repository.

    Attributes:
        name (str): The name (used as the section name) of the repo.
        url (str): The remote's url.
        branch (str): The branch that will be cloned.
        temp_dir (Path): The directory where all repos are cloned to.
        location (Path): The location of the local repo on the filesystem.
    """

    def __init__(self, name: str, url: str, branch: str, temp_dir: Path):
        self.name = name
        self.url = url
        self.branch = branch
        self.temp_dir = temp_dir
        self.location = temp_dir / self.name

    @property
    def cloned(self):
        """Returns True if the repo is cloned and False if it isn't"""
        if self.location.is_dir():
            return True
        return False

    async def sparse_clone(self, dirs: List[str]) -> Tuple[str, str]:
        """sparse clones a Git repo asynchronously"""
        args = [self.url, self.name, self.branch] + dirs
        if git_supports_sparse_clone():
            stdout = await execute_bash_script("sparse_clone.sh", args, self.temp_dir)
        else:
            stdout = await execute_bash_script("sparse_clone_old.sh", args, self.temp_dir)
        return stdout

    async def import_config_files(self, dirs: List[str]) -> subprocess.CompletedProcess:
        """Imports directories needed for building the site
        the list of dirs might include: mkdocs.yml, overrides/*, etc"""
        self.temp_dir.mkdir(exist_ok=True)
        return await self.sparse_clone(dirs)

    def delete_repo(self) -> None:
        """Deletes the repo from the temp directory"""
        shutil.rmtree(str(self.location))

    def load_config(self, yml_file: str = "mkdocs.yml") -> dict:
        """Loads the config yaml file into a dictionary"""
        if self.cloned:
            # If the config file is within the docs directory, it will be moved to the parent
            # directory (see scripts/mv_docs_up.sh) which is the location.
            config_file = self.location / Path(yml_file)
            if config_file.is_file():
                with open(config_file, "rb") as f:
                    return yaml_load(f)
            else:
                raise ImportDocsException(f"{self.name} doesn't have {yml_file} at {str(config_file)}")
        else:
            raise ImportDocsException("docs must be imported before loading yaml")


class DocsRepo(Repo):
    """Represents a Git repository, containing documentation.

    Attributes:
        name (str): The name (used as the section name) of the repo.
        url (str): The remote's url.
        branch (str): The branch that will be cloned.
        temp_dir (Path): The directory where all repos are cloned to.
        location (Path): The location of the local repo on the filesystem.
        docs_dir (str): The location of the documentation, which can be a glob. Default is "docs/*".
        edit_uri (str): The edit_uri used for MkDocs.
        config (str): The filename and extension for the yaml configuration file. Default is "mkdocs.yml".
        multi_docs (bool): If this is True, it means the repo has multiple docs directories that the user
                            wants to be pulled into the site.
        extra_imports (list): Extra directories to import along with the docs
    """

    def __init__(
        self,
        name: str,
        url: str,
        temp_dir: Path,
        docs_dir: str = "docs/*",
        branch: str = "main",
        edit_uri: str = None,
        multi_docs: bool = False,
        config: str = "mkdocs.yml",
        extra_imports: List[str] = []
    ):
        super().__init__(name, url, branch, temp_dir)
        self.docs_dir = docs_dir
        self.edit_uri = edit_uri or docs_dir
        self.multi_docs = multi_docs
        self.src_path_map = {}
        self.config = config
        self.extra_imports = extra_imports

    def __str__(self):
        return f"DocsRepo({self.name}, {self.url}, {self.location})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (
            isinstance(other, DocsRepo) and
            (self.name == other.name) and
            (self.url == other.url) and
            (self.temp_dir == other.temp_dir) and
            (self.docs_dir == other.docs_dir) and
            (self.branch == other.branch) and
            (self.edit_uri == other.edit_uri) and
            (self.multi_docs == other.multi_docs) and
            (self.config == other.config)
        )

    def get_edit_url(self, src_path):
        src_path = remove_parents(src_path, 1)
        if self.multi_docs:
            parent_path = str(Path(src_path).parent).replace("\\", "/")
            if parent_path in self.src_path_map:
                src_path = Path(src_path)
                return self.url + self.edit_uri + self.src_path_map.get(parent_path) + "/" + str(src_path.name)
            else:
                return self.url + self.edit_uri + self.src_path_map.get(str(src_path), str(src_path))
        return self.url + self.edit_uri + self.docs_dir.replace("/*", "") + src_path

    def set_edit_uri(self, edit_uri) -> None:
        """Sets the edit uri for the repo. Used for mkdocs pages"""
        self.edit_uri = edit_uri or self.docs_dir

    def transform_docs_dir(self) -> None:
        """Moves all files within a docs directory to the parent directory, deleting the docs directory after."""
        # remove docs nodes from the file tree
        for p in self.location.rglob("*"):
            if p.parent.name == "docs":
                # python versions < 3.8 don't return the new path instance
                new_p = p.rename(p.parent.parent / p.name)
                if not new_p:
                    new_p = p.parent.parent / p.name
                # create a mapping from the old src_path to the old for page edit_urls
                old_src_path = str(p).replace(str(self.location), "").replace("\\", "/")[1:]
                new_src_path = str(new_p).replace(str(self.location), "").replace("\\", "/")
                self.src_path_map[new_src_path] = old_src_path
        # delete all empty docs directories
        for p in self.location.rglob("*"):
            if p.name == "docs":
                shutil.rmtree(str(p))

    async def import_docs(self, remove_existing=True) -> 'DocsRepo':
        """imports the markdown documentation to be included in the site asynchronously"""
        if self.location.is_dir() and remove_existing:
            shutil.rmtree(str(self.location))
        if self.multi_docs:
            if self.docs_dir == "docs/*":
                docs_dir = "docs"
            else:
                docs_dir = self.docs_dir
            await self.sparse_clone([docs_dir, self.config] + self.extra_imports)
            self.transform_docs_dir()
        else:
            await self.sparse_clone([self.docs_dir, self.config] + self.extra_imports)
            await execute_bash_script("mv_docs_up.sh", [self.docs_dir.replace("/*", "")], cwd=self.location)
        return self

    def load_config(self) -> Dict:
        """Loads the repo's multirepo config file"""
        config = super().load_config(self.config)
        if 'nav' in config:
            resolve_nav_paths(config.get('nav'), self.name)
        return config


async def batch_import(repos: List[DocsRepo]) -> None:
    """Given a list of DocRepo instances, performs a batch import asynchronously"""
    if not repos:
        return None
    progress_list = ProgressList([repo.name for repo in repos])
    start = time.time()
    for import_async in asyncio.as_completed([repo.import_docs() for repo in repos]):
        repo = await import_async
        progress_list.mark_completed(repo.name, round(time.time() - start, 3))
