from mkdocs.plugins import BasePlugin
from .structure import DocsRepo, ImportDocsException

IMPORT_STATEMENT = "!import"

class MultirepoPlugin(BasePlugin):

    def __init__(self):
        self.repos = []

    def on_config(self, config):

        if not config.get('nav'):
            return config
        
        nav = config.get('nav')
        docs_dir = config.get('docs_dir')

        for entry in nav:
            (key, value), = entry.items()
            if type(value) is str:
                if value.startswith(IMPORT_STATEMENT):
                    repo_url = value.split(" ", 1)[1]
                    repo = DocsRepo(key, repo_url, docs_dir)
                    repo.import_docs("docs_test")
                    repo_config = repo.load_mkdocs_yaml()
                    print(repo_config, type(repo_config))
                    config[key] = repo_config.get('nav')
                    self.repos.append(repo)
        print(config)
        return config

    def on_post_build(self, config):
        for repo in self.repos:
            repo.delete_docs()
        
        