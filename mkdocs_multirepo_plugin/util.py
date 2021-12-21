from pathlib import Path
import subprocess
import logging 
from mkdocs.utils import warning_filter

log = logging.getLogger("mkdocs.plugins." + __name__)
log.addFilter(warning_filter)

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