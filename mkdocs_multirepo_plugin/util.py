from typing import Dict, Any
from pathlib import Path
from sys import platform, version_info
import subprocess
import asyncio
import logging
from mkdocs.utils import warning_filter
from collections import namedtuple
from re import search
import os

# used for getting Git version
GitVersion = namedtuple("GitVersion", "major minor")
LINUX_LIKE_PLATFORMS = ["linux", "linux2", "darwin"]

log = logging.getLogger("mkdocs.plugins." + __name__)
log.addFilter(warning_filter)


class ImportDocsException(Exception):
    pass


class GitException(Exception):
    pass


def get_src_path_root(src_path: str) -> str:
    """returns the root directory of a path (represented as a string)"""
    if "\\" in src_path:
        return src_path.split("\\", 1)[0]
    elif "/" in src_path:
        return src_path.split("/", 1)[0]
    return src_path


def get_subprocess_run_extra_args() -> Dict[str, Any]:
    if (version_info.major == 3 and version_info.minor > 6) or (version_info.major > 3):
        return {"capture_output": True, "text": True}
    return {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE}


def remove_parents(path: str, num_to_remove: int) -> str:
    parts = Path(path).parts
    if num_to_remove >= len(parts):
        raise ValueError(f"{num_to_remove} >= to path with {parts} parts.")
    parts_to_keep = parts[num_to_remove:]
    return '/' + str(Path(*parts_to_keep)).replace('\\', '/')


def where_git() -> Path:
    extra_run_args = get_subprocess_run_extra_args()
    output = (
        subprocess.run(["where", "git"], **extra_run_args)
        .stdout
        .replace("\r", "")  # remove carrage return
        .split("\n")[0]  # handle multiple locations of git.exe
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


def git_version() -> GitVersion:
    extra_run_args = get_subprocess_run_extra_args()
    if platform in LINUX_LIKE_PLATFORMS:
        output = subprocess.run(["git", "--version"], **extra_run_args)
    else:
        git_folder = where_git()
        output = subprocess.run(
            [str(git_folder / "bin" / "git.exe"), "--version"], **extra_run_args
            )
    stdout = output.stdout
    if isinstance(stdout, bytes):
        stdout = output.stdout.decode()
    version = search(r'([\d.]+)', stdout).group(1).split(".")[:2]
    return GitVersion(int(version[0]), int(version[1]))


def git_supports_sparse_clone() -> bool:
    git_v = git_version()
    if (git_v.major == 2 and git_v.minor < 25) or (git_v.major < 2):
        return False
    return True


async def execute_bash_script(script: str, arguments: list = [], cwd: Path = Path.cwd()) -> str:
    """executes a bash script in an asynchronously"""
    try:
        token = os.environ['AccessToken']
        #Insert the PAT after the url scheme
        schemeIndex = arguments[0].find("://") + 3 #The search string is 3 characters long; insert at the end of that
        arguments[0] = arguments[0][:schemeIndex] + token + "@" + arguments[0][schemeIndex:]
    except KeyError:
        pass
    
    if platform in LINUX_LIKE_PLATFORMS:
        process = await asyncio.create_subprocess_exec(
            'bash', script, *arguments, cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    else:
        git_folder = where_git()
        process = await asyncio.create_subprocess_exec(
            str(git_folder / "bin" / "bash.exe"), script, *arguments,
            cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    stdout, stderr = await process.communicate()
    stdout, stderr = stdout.decode(), stderr.decode()
    if process.returncode == 1:
        raise GitException(f"\n{stderr}\n")
    return stdout


def asyncio_run(futures) -> None:
    if (version_info.major == 3 and version_info.minor > 6) or (version_info.major > 3):
        asyncio.run(futures)
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(futures)
