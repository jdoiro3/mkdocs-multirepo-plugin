## 0.4.4

- Added support for importing extra directories via `extra_imports`. This allows users to import directories or files in addition to markdown contained in the docs directory (e.g., src). This might be done in order to get source code that is required to build docs using plugins like `mkdocstrings`.
- Added support for newer versions of Git that require `--no-cone` for the directories in the `set` command for sparse-checkout to be interpreted the same way as `.gitignore` paths/globs.

## 0.2.9

- Added support for macOS

## 0.2.2 (pre-release)

- Added progress bar to terminal output using [tqdm](https://github.com/tqdm/tqdm).

## 0.2.1 (pre-release)

- Added asynchronous importing of docs, using [asyncio subprocesses](https://docs.python.org/3/library/asyncio-subprocess.html#asyncio.asyncio.subprocess.Process). This should half import times.
