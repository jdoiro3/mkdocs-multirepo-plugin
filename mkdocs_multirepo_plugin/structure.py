from typing import Tuple
from sys import platform
import shutil
import subprocess
from pathlib import Path
from mkdocs.utils import yaml_load
from .util import GitException, ImportDocsException, where_git

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
    if "@" in repo_url:
        repo_url, branch = repo_url.rsplit("@", 1)
    else:
        branch = "master"
    return repo_url, branch

def parse_import(import_stmt: str) -> Tuple[str, str]:
    """parses !import statements"""
    repo_url = import_stmt.split(" ", 1)[1]
    return parse_repo_url(repo_url)

def execute_bash_script(script: str, arguments: list, cwd: Path) -> subprocess.CompletedProcess:
    if platform == "linux" or platform == "linux2":
        process = subprocess.run(
            ["bash", script]+arguments, capture_output=True, text=True,
            cwd=cwd
        )
    else:
        git_folder = where_git()
        process = subprocess.run(
            [str(git_folder / "bin" / "bash.exe"), script]+arguments, stdout=subprocess.PIPE,
            cwd=cwd
        )
    return process

class Repo:

    def __init__(self, name: str, url: str, branch: str, temp_dir: Path):
        self.name = name
        self.url = url
        self.branch = branch
        self.temp_dir = temp_dir / self.name
        self.cloned = False

    def sparse_clone(self, dirs: list) -> subprocess.CompletedProcess:
        print(dirs)
        args = [self.url, self.name, self.branch]+dirs
        if self.temp_dir.is_dir():
            shutil.rmtree(str(self.temp_dir))
        process = execute_bash_script("sparse_clone.sh", args, self.temp_dir.parent)
        if process.returncode == 2:
            raise GitException(f"error cloning {self.url}\nBash Error\n---------------\n{process.stderr}")
        self.cloned = True
        return process
    
    def import_config_files(self, dirs: list):
        self.temp_dir.mkdir(exist_ok=True)
        return self.sparse_clone(dirs)

    def delete_temp_dir(self):
        shutil.rmtree(str(self.temp_dir))
        self.cloned = False

    def load_config(self, temp_dir: str, yml_file: str):
        if self.cloned:
            config_file = Path(temp_dir) / self.name / Path(yml_file)
            if config_file.is_file():
                with open(config_file, "rb") as f:
                    return yaml_load(f)
            else:
                raise ImportDocsException(f"{self.name} does not have a mkdocs.yml at {str(config_file)}")
        else:
            raise ImportDocsException("docs must be imported before loading yaml")

class DocsRepo(Repo):

    def __init__(
        self, name: str, url: str, temp_dir: Path, 
        docs_dir: str="docs", branch: str="master", edit_uri: str=None
        ):
        super().__init__(name, url, branch, temp_dir)
        self.docs_dir = docs_dir
        self.edit_uri = edit_uri or docs_dir
        self.imported = False

    def set_edit_uri(self, edit_uri):
        self.edit_uri = edit_uri or self.docs_dir
    
    def import_docs(self, temp_dir: Path, remove_existing=True) -> None:
        if (self.temp_dir / self.name).is_dir() and remove_existing:
            shutil.rmtree(str(temp_dir / self.name))
        args = [self.name, self.url, self.docs_dir, self.branch]
        process = execute_bash_script("git_docs.sh", args, temp_dir)
        stderr = process.stderr
        if process.returncode == 1:
            raise ImportDocsException(
                f"{self.docs_dir} doesn't exist in the {self.branch} branch of {self.url}\nSTDERR:\n{stderr}"
                )
        elif process.returncode == 2:
            raise ImportDocsException(f"Error occurred cloning {self.name}.\nSTDERR\n{stderr}")
        if process.returncode > 2:
            raise ImportDocsException(f"Error occurred importing {self.name}.\nSTDERR\n{stderr}")
        self.imported = True

    def load_config(self, temp_dir, yml_file) -> dict:
        config = self.load_config(temp_dir, yml_file)
        if 'nav' in config:
            resolve_nav_paths(config.get('nav'), self.name)
        return config