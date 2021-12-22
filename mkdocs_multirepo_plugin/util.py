from pathlib import Path
import subprocess
import logging 
from mkdocs.utils import warning_filter

log = logging.getLogger("mkdocs.plugins." + __name__)
log.addFilter(warning_filter)

class GitPathException(Exception):
    pass

class ImportDocsException(Exception):
    pass

def remove_parents(path, num_to_remove) -> str:
    parts_to_keep = Path(path).parts[num_to_remove:]
    return '/' + str(Path(*parts_to_keep))

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
            raise GitPathException(
                f"git is not in PATH and install isn't located at {str(default_git_loc)}"
                )
    else:
        return Path(output).parent.parent