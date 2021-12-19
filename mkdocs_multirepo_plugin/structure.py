from sys import platform
import shutil
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

class DocsRepo:

    def __init__(self, name, url, root_docs_dir, docs_dir="docs"):
        self.name = name
        self.url = url
        self.root_docs_dir = root_docs_dir
        self.docs_dir = docs_dir
        self.imported = False
        # will be populated later
        self.multi_repo_dir = None
        self.config = None
    
    def import_docs(self, branch: str="master"):
        if platform == "linux" or platform == "linux2":
            pass
        else:
            git_folder = where_git()
            process = subprocess.run(
                [
                    str(git_folder / "bin" / "bash.exe"), 
                    "sparse_checkout_docs.sh", self.name, self.url, self.docs_dir, branch, self.root_docs_dir
                    ], 
                capture_output=True
                )
            if process.returncode != 0:
                raise ImportDocsException("error importing docs")
            self.multi_repo_dir = Path(self.root_docs_dir) / self.name
            self.imported = True
            print(process.stdout.decode("utf-8"))

    def load_mkdocs_yaml(self):
        if self.imported:
            with open(str(self.multi_repo_dir / "mkdocs.yml"), 'rb') as f:
                self.config = yaml_load(f)
                return self.config
        else:
            raise ImportDocsException("docs must be imported before loading yaml")

    def delete_docs(self):
        shutil.rmtree(str(self.multi_repo_dir))




    