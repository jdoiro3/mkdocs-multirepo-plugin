from typing import Tuple
from sys import platform
import shutil
import subprocess
from pathlib import Path
from mkdocs.utils import yaml_load
from .util import where_git

class GitPathException(Exception):
    pass

class ImportDocsException(Exception):
    pass

def resolve_nav_paths(nav: list, section_name: str) -> None:
    for index, entry in enumerate(nav):
        (key, value), = entry.items()
        if type(value) is list:
            resolve_nav_paths(value, section_name)
        else:
            nav[index][key] = str(section_name / Path(value))

def parse_repo_url(repo_url: str) -> Tuple[str, str]:
    if "@" in repo_url:
        repo_url, branch = repo_url.rsplit("@", 1)
    else:
        branch = "master"
    return repo_url, branch

def parse_import(import_stmt: str) -> Tuple[str, str]:
    repo_url = import_stmt.split(" ", 1)[1]
    return parse_repo_url(repo_url)

def git_docs(arguments: list, cwd: Path):
    if platform == "linux" or platform == "linux2":
        process = subprocess.run(
            ["bash", "git_docs.sh"]+arguments, capture_output=True, text=True,
            cwd=cwd
        )
    else:
        git_folder = where_git()
        process = subprocess.run(
            [str(git_folder / "bin" / "bash.exe"), "git_docs.sh"]+arguments, capture_output=True, text=True,
            cwd=cwd
        )
    return process



class DocsRepo:

    def __init__(self, name: str, url: str, docs_dir: str="docs", branch: str="master"):
        self.name = name
        self.url = url
        self.branch = branch
        self.docs_dir = docs_dir
        self.imported = False
    
    def import_docs(self, temp_dir: Path, remove_existing=True) -> None:
        if (temp_dir / self.name).is_dir() and remove_existing:
            shutil.rmtree(str(temp_dir / self.name))
        args = [self.name, self.url, self.docs_dir, self.branch]
        process = git_docs(args, temp_dir)
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

    def load_mkdocs_yaml(self, temp_dir: Path) -> dict:
        if self.imported:
            config_file = temp_dir / self.name / "mkdocs.yml"
            if config_file.is_file():
                with open(str(config_file), 'rb') as f:
                    config = yaml_load(f)
                    if 'nav' in config:
                        resolve_nav_paths(config.get('nav'), self.name)
                    return config
            else:
                raise ImportDocsException(f"{self.name} does not have a mkdocs.yml within the docs directory")
        else:
            raise ImportDocsException("docs must be imported before loading yaml")




    
