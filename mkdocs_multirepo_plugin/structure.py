from typing import Tuple
import re
import shutil
import subprocess
from pathlib import Path
from mkdocs.utils import yaml_load
from .util import (
    GitException, ImportDocsException, execute_bash_script,
    git_supports_sparse_clone
)

def get_src_path_root(src_path: str) -> str:
    """returns the root directory of a path (represented as a string)"""
    if "\\" in src_path:
        return src_path.split("\\", 1)[0]
    elif "/" in src_path:
        return src_path.split("/", 1)[0]
    return src_path

def resolve_nav_paths(nav: list, section_name: str) -> None:
    """adds the section_name to the begining of all paths in a MkDocs nav object"""
    for index, entry in enumerate(nav):
        (key, value), = entry.items()
        if type(value) is list:
            resolve_nav_paths(value, section_name)
        else:
            nav[index][key] = str(section_name / Path(value)).replace("\\", "/")

def parse_repo_url(repo_url: str) -> Tuple[str, str]:
    """parses !import statement urls"""
    url_parts = repo_url.split("?")
    import_parts = {"url": url_parts[0]}
    for part in url_parts[1:]:
        k, v = part.split("=")
        import_parts[k] = v
    print(import_parts)
    return import_parts

    
def parse_import(import_stmt: str) -> Tuple[str, str]:
    """parses !import statements"""
    import_url = import_stmt.split(" ", 1)[1]
    return parse_repo_url(import_url)

class Repo:

    def __init__(self, name: str, url: str, branch: str, temp_dir: Path):
        self.name = name
        self.url = url
        self.branch = branch
        self.temp_dir = temp_dir
        self.location = temp_dir / self.name

    @property
    def cloned(self):
        if self.location.is_dir():
            return True
        return False

    def sparse_clone(self, dirs: list) -> subprocess.CompletedProcess:
        """sparse clones a repo, using dirs in sparse checkout set command"""
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
        """imports directories needed for building the site
        the list of dirs might include: mkdocs.yml, overrides/*, etc"""
        self.temp_dir.mkdir(exist_ok=True)
        return self.sparse_clone(dirs)

    def delete_repo(self) -> None:
        """deletes the repo from the temp directory"""
        shutil.rmtree(str(self.location))

    def load_config(self, yml_file: str) -> dict:
        """loads the mkdocs config yaml file into a dictionary"""
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

    def __init__(self, name: str, url: str, temp_dir: Path, 
        docs_dir: str="docs/*", branch: str="master", edit_uri: str=None, multi_docs: bool=False
        ):
        super().__init__(name, url, branch, temp_dir)
        self.docs_dir = docs_dir
        self.edit_uri = edit_uri or docs_dir
        self.multi_docs = multi_docs

    def set_edit_uri(self, edit_uri):
        """sets the edit uri for the repo. Used for mkdocs pages"""
        self.edit_uri = edit_uri or self.docs_dir

    def transform_docs_dir(self) -> None:
        # remove docs nodes from the file tree
        for p in self.location.rglob("*"):
            if p.parent.name == "docs":
                p.rename(p.parent.parent / p.name)
        # delete all empty docs directories
        for p in self.location.rglob("*"):
            if p.name == "docs":
                shutil.rmtree(str(p))
    
    def import_docs(self, remove_existing=True) -> None:
        """imports the markdown documentation to be included in the site"""
        if self.location.is_dir() and remove_existing:
            shutil.rmtree(str(self.location))
        self.sparse_clone([self.docs_dir])
        if self.multi_docs:
            self.transform_docs_dir()
        else:
            execute_bash_script("transform_docs_dir.sh", [self.docs_dir.replace("/*", "")], self.location)

    def load_config(self, yml_file) -> dict:
        config = super().load_config(yml_file)
        if 'nav' in config:
            resolve_nav_paths(config.get('nav'), self.name)
        return config