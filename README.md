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

> `nav` takes precedence over `repos` (see below).
```yaml
nav:
  - Home: 'index.md'
  - MicroService: '!import https://github.com/{user}/{repo name}@{branch}'
```

If you'd prefer `MkDocs` to build the site nav based on the directory structure, you can define your other repos within the `plugins` section.

```yaml
plugins:
  - multirepo:
      cleanup: True # (optional) tells multirepo to cleanup the temporary directory where other repo docs are imported to
      folder_name: multirepo_docs # (optional) tells multirepo what the temp directory should be called
      repos:
        - section: Backstage
          import_url: 'https://github.com/backstage/backstage'
        - section: Monorepo
          import_url: 'https://github.com/backstage/mkdocs-monorepo-plugin'
        - section: 'Techdocs-cli'
          import_url: 'https://github.com/backstage/techdocs-cli@main'
```

## Notes

- If both `repos` and `nav` is specified in `mkdocs.yml`, `repos` are ignored.

## TODO

- [ ] Add tests (no one will use it if it isn't tested well).
- [ ] Add Linux support.
- [ ] Figure out how tech writers can develop on local copies of repos and see changes in the site before pushing. Maybe using symbolic links.
