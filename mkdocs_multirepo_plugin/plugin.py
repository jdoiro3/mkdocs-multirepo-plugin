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

        for index, entry in enumerate(nav):
            (key, value), = entry.items()
            if type(value) is str:
                if value.startswith(IMPORT_STATEMENT):
                    repo_url = value.split(" ", 1)[1]
                    repo = DocsRepo(key, repo_url, docs_dir)
                    terminal_output = repo.import_docs("docs_test")
                    print("start", terminal_output, "end")
                    repo_config = repo.load_mkdocs_yaml()
                    config["nav"][index][key] = repo_config.get('nav')
                    self.repos.append(repo)
        return config

    def on_post_build(self, config):
        for repo in self.repos:
            repo.delete_docs()
        
        
