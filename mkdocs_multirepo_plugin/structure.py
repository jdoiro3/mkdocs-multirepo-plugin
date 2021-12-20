from typing import Tuple
from sys import platform
import subprocess
from pathlib import Path
from mkdocs.utils import yaml_load

class GitPathException(Exception):
    pass

class ImportDocsException(Exception):
    pass

def where_git() -> Path:
    output = (
        subprocess.run(["where","git"], capture_output=True, shell=True)
        .stdout
        .decode("utf-8")
        .replace("\r", "").replace("\n", "")
    )
    if "INFO" in output:
        # see if a git install is located in the default location
        default_git_loc = Path("C:/Program Files/Git")
        if default_git_loc.is_dir():
            return default_git_loc
        else:
            raise GitPathException(
                f"git is not in PATH and install isn't located at {str(default_git_loc)}"
                )
    else:
        return Path(output).parent.parent

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


class DocsRepo:

    def __init__(self, name: str, url: str, docs_dir: str="docs", branch: str="master"):
        self.name = name
        self.url = url
        self.branch = branch
        self.docs_dir = docs_dir
        self.imported = False
    
    def import_docs(self, temp_dir: Path) -> None:
        if platform == "linux" or platform == "linux2":
            pass
        else:
            git_folder = where_git()
            process = subprocess.run(
                [
                    str(git_folder / "bin" / "bash.exe"), 
                    "git_docs.sh", self.name, self.url, self.docs_dir, self.branch, temp_dir
                    ], 
                capture_output=True
                )
            if process.returncode == 1:
                raise ImportDocsException(f"{self.docs_dir} doesn't exist in the {self.branch} branch of {self.url}")
            if process.returncode > 1:
                error_output = process.stderr.decode("utf-8")
                raise ImportDocsException(f"Error occurred importing docs from another repo.\n{error_output}")
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
                print("can't load mkdocs.yml")
        else:
            raise ImportDocsException("docs must be imported before loading yaml")




    
