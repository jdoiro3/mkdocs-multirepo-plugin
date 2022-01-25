from typing import Tuple
import re
import shutil
import subprocess
from pathlib import Path
from mkdocs.utils import yaml_load
from .util import (
    GitException, ImportDocsException, execute_bash_script,
    git_supports_sparse_clone, remove_parents
)

def resolve_nav_paths(nav: list, section_name: str) -> None:
    """Adds the section_name to the begining of all paths in a MkDocs nav object"""
    for index, entry in enumerate(nav):
        (key, value), = entry.items()
        if type(value) is list:
            resolve_nav_paths(value, section_name)
        else:
            nav[index][key] = str(section_name / Path(value)).replace("\\", "/")

def parse_repo_url(repo_url: str) -> dict:
    """Parses !import statement urls"""
    url_parts = repo_url.split("?")
    import_parts = {"url": url_parts[0]}
    for part in url_parts[1:]:
        k, v = part.split("=")
        import_parts[k] = v
    return import_parts

    
def parse_import(import_stmt: str) -> Tuple[str, str]:
    """Parses !import statements"""
    import_url = import_stmt.split(" ", 1)[1]
    return parse_repo_url(import_url)


class Repo:
    """Represents a Git repository.

    Attributes:
        name (str): The name (used as the section name) of the repo.
        url (str): The remote's url.
        branch (str): The branch that will be cloned.
        temp_dir (pathlib.Path): The directory where all repos are cloned to.
        location (pathlib.Path): The location of the local repo on the filesystem.
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

    def sparse_clone(self, dirs: list) -> subprocess.CompletedProcess:
        """Sparse clones a repo, using dirs in sparse checkout set command"""
        args = [self.url, self.name, self.branch] + dirs + ["./mkdocs.yml"]
        if git_supports_sparse_clone():
            process = execute_bash_script("sparse_clone.sh", args, self.temp_dir)
        else:
            process = execute_bash_script("sparse_clone_old.sh", args, self.temp_dir)
        stderr = process.stderr
        if process.returncode >= 1:
            raise ImportDocsException(f"Error occurred cloning {self.name}.\nSTDERR\n{stderr}")
        return process
    
    def import_config_files(self, dirs: list) -> subprocess.CompletedProcess:
        """Imports directories needed for building the site
        the list of dirs might include: mkdocs.yml, overrides/*, etc"""
        self.temp_dir.mkdir(exist_ok=True)
        return self.sparse_clone(dirs)

    def delete_repo(self) -> None:
        """Deletes the repo from the temp directory"""
        shutil.rmtree(str(self.location))

    def load_config(self, yml_file: str) -> dict:
        """Loads the mkdocs config yaml file into a dictionary"""
        if self.cloned:
            config_file = self.location / Path(yml_file)
            if config_file.is_file():
                with open(config_file, "rb") as f:
                    return yaml_load(f)
            else:
                raise ImportDocsException(f"{self.name} does not have a mkdocs.yml at {str(config_file)}")
        else:
            raise ImportDocsException("docs must be imported before loading yaml")

class DocsRepo(Repo):
    """Represents a Git repository, containing documentation.

    Attributes:
        name (str): The name (used as the section name) of the repo.
        url (str): The remote's url.
        branch (str): The branch that will be cloned.
        temp_dir (pathlib.Path): The directory where all repos are cloned to.
        location (pathlib.Path): The location of the local repo on the filesystem.
        docs_dir (str): The location of the documentation, which can be a glob. Default is "docs/*".
        edit_uri (str): The edit_uri used for MkDocs.
        multi_docs (bool): If this is True, it means the repo has multiple docs directories that the user
                            wants to be pulled into the site.
    """

    def __init__(self, name: str, url: str, temp_dir: Path, 
        docs_dir: str="docs/*", branch: str="master", edit_uri: str=None, multi_docs: bool=False
        ):
        super().__init__(name, url, branch, temp_dir)
        self.docs_dir = docs_dir
        self.edit_uri = edit_uri or docs_dir
        self.multi_docs = multi_docs
        self.src_path_map = {}


    def get_edit_url(self, src_path):
        src_path = remove_parents(src_path, 1)
        if self.multi_docs:
            parent_path = str(Path(src_path).parent).replace("\\", "/")
            print(f"Looking for path: {parent_path}...")
            if parent_path in self.src_path_map:
                print(f"found {parent_path} in src_path_map")
                src_path = Path(src_path)
                return self.url + self.edit_uri + self.src_path_map.get(parent_path) + "/" + str(src_path.name)
            else:
                print(f"didn't find {parent_path} in:")
                print(self.src_path_map.keys())
                return self.url + self.edit_uri + self.src_path_map.get(src_path, src_path)
        return self.url + self.edit_uri + self.docs_dir.replace("/*", "") + src_path

    def set_edit_uri(self, edit_uri) -> None:
        """Sets the edit uri for the repo. Used for mkdocs pages"""
        self.edit_uri = edit_uri or self.docs_dir

    def transform_docs_dir(self) -> None:
        """Moves all files within a docs directory to the parent directory, deleting the docs directory after."""
        # remove docs nodes from the file tree
        for p in self.location.rglob("*"):
            if p.parent.name == "docs":
                new_p = p.rename(p.parent.parent / p.name)
                # create a mapping from the old new src_path to the old for page edit_urls
                old_src_path = str(p).replace(str(self.location), "").replace("\\", "/")[1:]
                new_src_path = str(new_p).replace(str(self.location), "").replace("\\", "/")
                self.src_path_map[new_src_path] = old_src_path
        # delete all empty docs directories
        for p in self.location.rglob("*"):
            if p.name == "docs":
                shutil.rmtree(str(p))

    
    def import_docs(self, remove_existing=True) -> None:
        """Imports the markdown documentation to be included in the site"""
        if self.location.is_dir() and remove_existing:
            shutil.rmtree(str(self.location))
        if self.multi_docs:
            if self.docs_dir == "docs/*":
                docs_dir = "docs"
            else:
                docs_dir = self.docs_dir
            self.sparse_clone([docs_dir])
            self.transform_docs_dir()
        else:
            self.sparse_clone([self.docs_dir])
            execute_bash_script("mv.sh", [self.docs_dir.replace("/*", "")], cwd=self.location)

    def load_config(self, yml_file) -> dict:
        """Loads the repo's mkdocs.yml configuration file or the same file with a different name"""
        config = super().load_config(yml_file)
        if 'nav' in config:
            resolve_nav_paths(config.get('nav'), self.name)
        return config