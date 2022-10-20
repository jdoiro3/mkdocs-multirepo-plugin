## 0.4.11

- Added a specific `GithubAccessToken` environment variable that allows usage of the plugin with GitHub Apps-generated access tokens and personal access tokens. 

## 0.4.10

- Added support for importing repos into a subsection.
- Fixed moving the imported docs folder up so that the docs folder does not appear in the menu.
- MkDocs versions  >= 1.4.0 changed the default config values from an empty string to None. You should use this version or newer to insure support with newer versions of MkDocs.

## 0.4.8

- Fixed the generation of edit urls for imported repos.

## 0.4.4

- Added support for importing extra directories via `extra_imports`. This allows users to import directories or files in addition to markdown contained in the docs directory (e.g., src). This might be done in order to get source code that is required to build docs using plugins like `mkdocstrings`.
- Added support for newer versions of Git that require `--no-cone` for the directories in the `set` command for sparse-checkout to be interpreted the same way as `.gitignore` paths/globs.

## 0.2.9

- Added support for macOS

## 0.2.2 (pre-release)

- Added progress bar to terminal output using [tqdm](https://github.com/tqdm/tqdm).

## 0.2.1 (pre-release)

- Added asynchronous importing of docs, using [asyncio subprocesses](https://docs.python.org/3/library/asyncio-subprocess.html#asyncio.asyncio.subprocess.Process). This should half import times.
