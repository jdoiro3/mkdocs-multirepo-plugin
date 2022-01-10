from pathlib import Path
from sys import platform, version_info
import subprocess
import logging 
from mkdocs.utils import warning_filter

log = logging.getLogger("mkdocs.plugins." + __name__)
log.addFilter(warning_filter)

class ImportDocsException(Exception):
    pass

class GitException(Exception):
    pass

def remove_parents(path, num_to_remove) -> str:
    parts = Path(path).parts
    if num_to_remove >= len(parts):
        raise ValueError(f"{num_to_remove} >= to path with {parts} parts.")
    parts_to_keep = parts[num_to_remove:]
    return '/' + str(Path(*parts_to_keep)).replace('\\', '/')

def where_git() -> Path:
    output = (
        subprocess.run(["where","git"], capture_output=True)
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
            raise GitException(
                f"git is not in PATH and install isn't located at {str(default_git_loc)}"
                )
    else:
        return Path(output).parent.parent

def execute_bash_script(script: str, arguments: list, cwd: Path) -> subprocess.CompletedProcess:
    if platform == "linux" or platform == "linux2":
        process = subprocess.run(
            ["bash", script]+arguments, capture_output=True, text=True,
            cwd=cwd
        )
    else:
        git_folder = where_git()
        # capture_outpout was added in 3.7.
        if version_info.major == 3 and version_info.minor > 6:
            process = subprocess.run(
                [str(git_folder / "bin" / "bash.exe"), script]+arguments, capture_output=True, text=True,
                cwd=cwd
            )
        else:
            process = subprocess.run(
                [str(git_folder / "bin" / "bash.exe"), script]+arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=cwd
            )
    return process