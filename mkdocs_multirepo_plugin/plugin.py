from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import get_files
from .structure import DocsRepo, ImportDocsException
from pathlib import Path
from copy import deepcopy
import shutil
import os

IMPORT_STATEMENT = "!import"

class MultirepoPlugin(BasePlugin):

    def __init__(self):
        self.repos = []
        self.temp_dir = None

    def on_config(self, config):

        if not config.get('nav'):
            return config
        
        nav = config.get('nav')
        docs_dir = Path(config.get('docs_dir'))
        self.temp_dir = docs_dir.parent / 'temp_docs'
        print(f"temp_dir: {self.temp_dir}")
        os.mkdir(str(self.temp_dir))

        for index, entry in enumerate(nav):
            (key, value), = entry.items()
            if type(value) is str:
                if value.startswith(IMPORT_STATEMENT):
                    repo_url = value.split(" ", 1)[1]
                    repo = DocsRepo(key, repo_url, branch="docs_test")
                    print(f"INFO - Importing docs from {repo.url}")
                    repo.import_docs(self.temp_dir)
                    repo_config = repo.load_mkdocs_yaml(self.temp_dir)
                    config["nav"][index][key] = repo_config.get('nav')
                    self.repos.append(repo)
        return config

    def on_files(self, files, config):
        temp_config = deepcopy(config)
        temp_config["docs_dir"] = self.temp_dir
        other_repo_files = get_files(temp_config)
        for f in other_repo_files:
            files.append(f)
        return files

    def on_post_build(self, config):
        if self.temp_dir:
            shutil.rmtree(str(self.temp_dir))
        
        
