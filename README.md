# mkdocs-multirepo-plugin

Build documentation in multiple repos into one site.

## Setup

Install plugin using pip:

```
pip install mkdocs-multirepo-plugin
```
Next, add the plugin to your `mkdocs.yml`

```yaml
plugins:
  - multirepo
```

The plugin introduces the `!import` statement in your config's `nav` section, allowing you to pass another repo's url, which has a `docs` directory and `mkdocs.yml` with its own `nav`, into the navigation.

```yaml
nav:
  - Home: 'index.md'
  - MicroService1: '!import https://github.com/{user}/{repo name}@{branch}'
```

## Example