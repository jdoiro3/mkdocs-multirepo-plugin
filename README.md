# mkdocs-multirepo-plugin

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

*Some other repo's mkdocs.yml*
```yaml
edit_uri: /blob/master/

nav:
  - Home: index.md
```

If you'd prefer `MkDocs` to build the site nav based on the directory structure, you can define your other repos within the `plugins` section.

```yaml
plugins:
  - multirepo:
      cleanup: True # (optional) tells multirepo to cleanup the temporary directory where other repo docs are imported to
      temp_dir: multirepo_docs # (optional) tells multirepo what the temp directory should be called
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
    cd $(docs_dir)
    mkdocs build
  env:
    AccessToken: $(System.AccessToken)
  displayName: 'Build MkDocs Site'
```

## Development in Imported Repos

For `mkdocs serve` to work properly in another repo (a repo that is imported into a main site), you will need to add the multirepo plugin within the *imported* repo, including the following configuration.

> You will also need to have `plugins` the main repo (the repo what imports other repos) uses installed within your local `venv`.

```yml
site_name: My Docs

plugins:
  multirepo:
    included_repo: true
    url: https://azuredevops.unum.com/tfs/UNUM/Portfolio/_git/ENT_Audit.Docs
    dirs: ["overrides/*", "internal-site/mkdocs.yml"]
    custom_dir: overrides # assuming you use the material theme and have overrides
    yml_file: internal-site/mkdocs.yml # this can also be a relative path
    branch: dev
```

Engineers can now run `mkdocs serve` within there local repo and view what there section will look like in the combined site.

## Notes

- If both `repos` and `nav` is specified in `mkdocs.yml`, `repos` are ignored.

## TODO

- [ ] Add tests (no one will use it if it isn't tested well).
- [x] Change page edit urls to point to the correct repo and have the correct path
- [ ] Make sure Git version supports new `clone` arguments
- [x] Add Linux support
  - ~~Looks like `git clone --sparse` doesn't work with urls on Linux~~ git needs to be up to date
- [ ] Figure out how tech writers can develop on local copies of repos and see changes in the site before pushing. Maybe using symbolic links.
