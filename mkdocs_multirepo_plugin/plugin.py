from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import get_files
from mkdocs.config import config_options
from .structure import DocsRepo, ImportDocsException
from pathlib import Path
from copy import deepcopy
import shutil

IMPORT_STATEMENT = "!import"

class MultirepoPlugin(BasePlugin):

    config_scheme = (
        ("cleanup", config_options.Type(bool, default=True)),
        ("folder_name", config_options.Type(str, default="temp_docs"))
    )

    def __init__(self):
        self.repos = []
        self.temp_dir = None

    def on_config(self, config):

        if not config.get('nav'):
            return config
        
        nav = config.get('nav')
        docs_dir = Path(config.get('docs_dir'))
        self.temp_dir = docs_dir.parent / self.config.get("folder_name")
        self.temp_dir.mkdir(exist_ok=True)

        for index, entry in enumerate(nav):
            (section_name, value), = entry.items()
            if type(value) is str:
                if value.startswith(IMPORT_STATEMENT):
                    repo_url = value.split(" ", 1)[1]
                    if "@" in repo_url:
                        repo_url, branch = repo_url.rsplit("@", 1)
                    else:
                        branch = "master"
                    repo = DocsRepo(section_name, repo_url, branch=branch)
                    folder_name = self.config.get("folder_name")
                    print(f"INFO     -  Multirepo plugin is importing docs from {repo.url} into {folder_name}/")
                    repo.import_docs(self.temp_dir)
                    repo_config = repo.load_mkdocs_yaml(self.temp_dir)
                    nav[index][section_name] = repo_config.get('nav')
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
        if self.temp_dir and self.config.get("cleanup"):
            folder_name = self.config.get("folder_name")
            print(f"INFO     -  Multirepo plugin is cleaning up {folder_name}/")
            shutil.rmtree(str(self.temp_dir))
        
        
