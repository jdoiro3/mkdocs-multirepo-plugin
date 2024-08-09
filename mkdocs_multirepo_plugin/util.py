import asyncio
import logging
import re
import subprocess
from pathlib import Path
from sys import platform, version_info
from typing import Any, Dict, NamedTuple

LINUX_LIKE_PLATFORMS = ["linux", "linux2", "darwin"]

# This is a global variable imported by other modules
log = logging.getLogger("mkdocs.plugins." + __name__)


class Version(NamedTuple):
    major: int
    minor: int
    patch: int


class ImportDocsException(Exception):
    pass


class VersionException(Exception):
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
    return "/" + str(Path(*parts_to_keep)).replace("\\", "/")


def parse_version(val: str) -> Version:
    match = re.match(r"[^0-9]*(([0-9]+\.){2}[0-9]+).*", val)
    if not match:
        raise VersionException(f"Could not match version in {val}")
    version: str = match.group(1) if match else ""
    major, minor, patch = version.split(".", maxsplit=2)
    return Version(
        major=int(major),
        minor=int(minor),
        patch=int(patch),
    )


def git_version() -> Version:
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
    # thanks @matt
    match = re.match(r"[^0-9]*(([0-9]+\.){2}[0-9]+).*", stdout)
    if not match:
        raise GitException(f"Could not match Git version number in {stdout}")
    version: str = match.group(1) if match else ""
    return parse_version(version)


def git_supports_sparse_clone() -> bool:
    """The sparse-checkout was added in 2.25.0
    See RelNotes here: https://github.com/git/git/blob/9005149a4a77e2d3409c6127bf4fd1a0893c3495/Documentation/RelNotes/2.25.0.txt#L67
    """
    return git_version() >= Version(2, 25, 0)


async def execute_bash_script(
    script: str, arguments: list = [], cwd: Path = Path.cwd()
) -> str:
    """executes a bash script in an asynchronously"""
    try:
        process = await asyncio.create_subprocess_exec(
            "bash",
            script,
            *arguments,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        raise GitException(
            "bash executable not found. Please ensure bash is available in PATH."
        )

    stdout, stderr = await process.communicate()
    stdout_str, stderr_str = stdout.decode(), stderr.decode()
    if process.returncode != 0:
        raise BashException(f"\n{stderr_str}\n")
    return stdout_str


def asyncio_run(futures) -> None:
    if (version_info.major == 3 and version_info.minor > 6) or (version_info.major > 3):
        asyncio.run(futures)
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(futures)


class ProgressList:
    def __init__(self, labels):
        self._labels = labels
        self._labels_map = {label: i for i, label in enumerate(self._labels)}
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
