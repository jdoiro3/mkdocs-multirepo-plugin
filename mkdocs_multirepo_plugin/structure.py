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

def resolve_nav_paths(nav, section_name):
    for index, entry in enumerate(nav):
        (key, value), = entry.items()
        if type(value) is list:
            resolve_nav_paths(value, section_name)
        else:
            nav[index][key] = str(section_name / Path(value))


class DocsRepo:

    def __init__(self, name, url, docs_dir="docs", branch="master"):
        self.name = name
        self.url = url
        self.branch = branch
        self.docs_dir = docs_dir
        self.imported = False
    
    def import_docs(self, temp_dir: Path):
        if platform == "linux" or platform == "linux2":
            pass
        else:
            git_folder = where_git()
            process = subprocess.run(
                [
                    str(git_folder / "bin" / "bash.exe"), 
                    "sparse_checkout_docs.sh", self.name, self.url, self.docs_dir, self.branch, temp_dir
                    ], 
                capture_output=True
                )
            if process.returncode == 1:
                raise ImportDocsException(f"{self.docs_dir} doesn't exist in the {self.branch} branch of {self.url}")
            if process.returncode > 1:
                raise ImportDocsException("Error occurred importing docs from another repo")
            self.imported = True

    def load_mkdocs_yaml(self, temp_dir: Path):
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




    