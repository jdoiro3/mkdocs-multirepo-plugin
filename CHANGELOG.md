## 0.6.0

### Prs in Release

- [Add support for nav repos](https://github.com/jdoiro3/mkdocs-multirepo-plugin/pull/80)

### Added Features

A new `nav_repos` was added to the configuration. This is similar to the `repos` configuration except that `nav_repos`
expects a `nav` to be present to use in the navigation. This configuration can also be used along with `!import` statements.

### Usage Example

<details><summary><b>See example</b></summary>

  ```yaml
  plugins:
    - search
    - multirepo:
        # (optional) tells multirepo to cleanup the temporary directory after site is built.
        cleanup: false
        nav_repos:
          - name: backstage
            import_url: https://github.com/backstage/backstage
            # forward slash is needed in '/README.md' so that only the README.md in the root
            # directory is imported and not all README.md files.
            imports: [
              docs/publishing.md, docs/integrations/index.md, /README.md,
              # asset files needed
              docs/assets/*
              ]
          - name: fast-api
            import_url: https://github.com/tiangolo/fastapi
            imports: [docs/en/docs/index.md]

  nav:
    - Backstage:
        - Home: backstage/README.md
        - Integration: backstage/docs/integrations/index.md
        - Publishing: backstage/docs/publishing.md
    - FastAPI: fast-api/docs/en/docs/index.md
    # you can still use the !import statement
    - MkdocStrings: '!import https://github.com/mkdocstrings/mkdocstrings'
  ```

</details>

In addition this release adds `keeps_docs_dir` to the `!import` statement, which means one imported repo can override the behavior set by the global configuration. See [Fix edit urls and add new `keep_docs_dir` config param](https://github.com/jdoiro3/mkdocs-multirepo-plugin/pull/75) for more details.

## 0.5.0

### PRs in Release

- [Create .git/info dir if it does not exist](https://github.com/jdoiro3/mkdocs-multirepo-plugin/pull/59)
- [Fix edit urls and add new `keep_docs_dir` config param](https://github.com/jdoiro3/mkdocs-multirepo-plugin/pull/75)
- [Fix Readme](https://github.com/jdoiro3/mkdocs-multirepo-plugin/pull/77)

### Added Features

A new `keep_docs_dir` was added to the `multirepo` config. Setting this to `true` will cause the plugin to not move the contents of the `docs_dir` up and delete it. See issue [#74](https://github.com/jdoiro3/mkdocs-multirepo-plugin/issues/74) for more details.

### Usage Example

```yaml
plugins:
  - search
  - multirepo:
      keep_docs_dir: true
```

## 0.4.12

- Fixed use of `GithubAccessToken` environment variable so that the sparse clone now uses the correct token.

## 0.4.11

- Added a specific `GithubAccessToken` environment variable that allows usage of the plugin with GitHub Apps-generated access tokens and personal access tokens.
- Fixed edit urls for imported repos where the the Mkdocs `edit_uri` and `repo_url` aren't set, and the Multirepo `edit_uri` for an imported repo isn't set. Note that the edit url for imported repos hasn't been robustly tested yet.

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
