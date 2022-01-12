# mkdocs-multirepo-plugin

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)

Build documentation in multiple repos into one site.

## Setup

Install plugin using pip:

```
pip install git+https://github.com/jdoiro3/mkdocs-multirepo-plugin
```

Next, add the plugin to your `mkdocs.yml`

```yaml
plugins:
  - multirepo
```

The plugin introduces the `!import` statement in your config's `nav` section. You can now use the import statement to add a documentation section, where the docs are pulled from the source repo.

> Things to Note:
>
> - If using `!import` in the `nav`, the repo's docs folder must have a `mkdocs.yml` file with a `nav` section.
> - `nav` takes precedence over `repos` (see below).

```yaml
nav:
  - Home: 'index.md'
  - MicroService: '!import https://github.com/{user}/{repo name}@{branch}'
```

*MicroService mkdocs.yml*
```yaml
edit_uri: /blob/master/

nav:
  - Home: index.md
```

If you'd prefer `MkDocs` to build the site nav based on the directory structure, you can define your other repos within the `plugins` section.

> Note:
> Cleanup should be set to `False` when developing (i.e., when calling `mkdocs serve`). This will prevent importing repos multiple times with livereload.

```yaml
plugins:
  - multirepo:
      # (optional) tells multirepo to cleanup the temporary directory after site is built.
      cleanup: True
      # (optional) tells multirepo what the temp directory should be called
      temp_dir: multirepo_docs
      repos:
        - section: Backstage
          import_url: 'https://github.com/backstage/backstage'
          # you can define the edit uri path
          edit_uri: /blob/master/
        - section: Monorepo
          import_url: 'https://github.com/backstage/mkdocs-monorepo-plugin'
          edit_uri: /blob/master/
        - section: 'Techdocs-cli'
          import_url: 'https://github.com/backstage/techdocs-cli@main'
          edit_uri: /blob/main/
        - section: FastAPI
          import_url: 'https://github.com/tiangolo/fastapi'
          # you can also define where the docs are located in the repo. Default is docs
          docs_dir: docs/en/docs
```

## Use in CI/CD

If you want to use the plugin within Azure Pipelines or Github Actions, you'll need to define an `AccessToken` environment variable for the `mkdocs build` step. The `AccessToken` should have access to `clone` all repos.

### Azure Pipeline Step Example

```yaml
- script: |
    source ./env/bin/activate
    mkdocs build
  env:
    AccessToken: $(System.AccessToken)
  displayName: 'Build MkDocs Site'
```

## Development in Imported Repos

For `mkdocs serve` to work properly in another repo (a repo that is imported into a main site), you will need to add the multirepo plugin within the *imported* repo, including the following configuration.

> Notes:
> - You will also need to have `plugins` the main repo (the repo what imports other repos) uses installed within your local `venv`.
> - See documentation on the [set](https://git-scm.com/docs/git-sparse-checkout#Documentation/git-sparse-checkout.txt-emsetem) git command for `sparse-checkout` if you are confused with what `dirs` can contain.

```yml
site_name: My Docs

plugins:
  multirepo:
    imported_repo: true
    url: [url to main repo]
    # directories and files needed for building the site
    dirs: ["overrides/*", "mkdocs.yml"]
    custom_dir: overrides # overrides directory
    yml_file: mkdocs.yml # this can also be a relative path
    branch: dev
```

Engineers can now run `mkdocs serve` within their local repo, using the main site's configuration, custom theming and features.

## TODO

- [ ] Add tests (no one will use it if it isn't tested well).
- [x] Change page edit urls to point to the correct repo and have the correct path
- [x] ~~Make sure Git version supports new `clone` arguments~~ Use old sparse checkout method if git version is old
- [x] Add Linux support
  - ~~Looks like `git clone --sparse` doesn't work with urls on Linux~~ git needs to be up to date
- [x] Figure out how tech writers can develop on local copies of repos and see changes in the site before pushing. ~~Maybe using symbolic links.~~
