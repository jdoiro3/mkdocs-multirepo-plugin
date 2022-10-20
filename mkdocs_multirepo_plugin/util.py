from typing import Dict, Any
from pathlib import Path
from sys import platform, version_info
import subprocess
import asyncio
import logging
from mkdocs.utils import warning_filter
from collections import namedtuple
from re import search

# used for getting Git version
GitVersion = namedtuple("GitVersion", "major minor")
LINUX_LIKE_PLATFORMS = ["linux", "linux2", "darwin"]

log = logging.getLogger("mkdocs.plugins." + __name__)
log.addFilter(warning_filter)


class ImportDocsException(Exception):
    pass


class GitException(Exception):
    pass


class ImportSyntaxError(Exception):
    pass


class BashException(Exception):
    pass


def is_windows():
    if platform not in LINUX_LIKE_PLATFORMS:
        return True
    return False


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


def git_version() -> GitVersion:
    extra_run_args = get_subprocess_run_extra_args()
    try:
        output = subprocess.run(["git", "--version"], **extra_run_args)
    except FileNotFoundError:
        raise GitException(
            "git executable not found. Please ensure git is available in PATH."
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
        process = await asyncio.create_subprocess_exec(
            'bash', script, *arguments, cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    except FileNotFoundError:
        raise GitException(
            "bash executable not found. Please ensure bash is available in PATH."
        )

    stdout, stderr = await process.communicate()
    stdout, stderr = stdout.decode(), stderr.decode()
    if process.returncode == 1:
        raise BashException(f"\n{stderr}\n")
    return stdout


def asyncio_run(futures) -> None:
    if (version_info.major == 3 and version_info.minor > 6) or (version_info.major > 3):
        asyncio.run(futures)
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(futures)


class ProgressList:

    def __init__(self, labels):
        self._labels = labels
        self._labels_map = {
            label: i for i, label in enumerate(self._labels)
        }
        self._num_items = len(self._labels)
        for label in self._labels:
            print(f"🔳 {label}")

    def index(self, label):
        return self._labels_map.get(label)

    def mark_completed(self, label, duration=""):
        i = self.index(label)
        num_items = self._num_items
        update_line = f"\033[{num_items - i}A"
        back_to_bottom = f"\033[{num_items - i - 1}B"
        if i == num_items - 1:
            print(f"{update_line}✅ {label} ({duration} secs)")
        else:
            print(f"{update_line}✅ {label} ({duration} secs){back_to_bottom}")
