# mkdocs-multirepo-plugin

Build documentation in multiple repos into one site.

Example `mkdocs.yml`

```yaml

site_name: My Docs

nav:
  - Intro: 'index.md'
  - 'Section': '!import https://github.com/jdoiro3/2D-Projectiles'

plugins:
  - multirepo
```
