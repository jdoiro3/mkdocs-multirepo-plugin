from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import get_files, Files
from mkdocs.config import config_options
from .structure import DocsRepo, ImportDocsException, parse_import, parse_repo_url
from .util import log
from pathlib import Path
from copy import deepcopy
import shutil

IMPORT_STATEMENT = "!import"

class MultirepoPlugin(BasePlugin):

    config_scheme = (
        ("cleanup", config_options.Type(bool, default=True)),
        ("temp_dir", config_options.Type(str, default="temp_docs")),
        ("repos", config_options.Type(list, default=[]))
    )

    def __init__(self):
        self.temp_dir = None

    def on_config(self, config: dict) -> dict:

        docs_dir = Path(config.get('docs_dir'))
        self.temp_dir = docs_dir.parent / self.config.get("temp_dir")
        repos = self.config.get("repos")

        if not self.temp_dir.is_dir():
            self.temp_dir.mkdir(exist_ok=True)

        # navigation isn't defined no repos defined in plugin section
        if not config.get('nav') and not repos:
            return config

        # navigation isn't defined but plugin section has repos
        if not config.get('nav') and repos:
            for repo in repos:
                repo_url, branch = parse_repo_url(repo.get("import_url"))
                repo = DocsRepo(repo.get("section"), repo_url, docs_dir=repo.get("docs_dir", "docs"), branch=branch)
                log.info(f"Multirepo plugin is importing docs for section {repo.name}")
                repo.import_docs(self.temp_dir)
            return config

        # nav takes precedence over repos
        if config.get('nav') and repos:
            log.warning("Multirepo plugin is ignoring plugins.multirepo.repos. Nav takes precedence")
        
        nav = config.get('nav')
        for index, entry in enumerate(nav):
            (section_name, value), = entry.items()
            if type(value) is str:
                if value.startswith(IMPORT_STATEMENT):
                    repo_url, branch = parse_import(value)
                    repo = DocsRepo(section_name, repo_url, branch=branch)
                    folder_name = self.config.get("folder_name")
                    print(f"INFO     -  Multirepo plugin is importing docs for section {repo.name}")
                    repo.import_docs(self.temp_dir)
                    repo_config = repo.load_mkdocs_yaml(self.temp_dir)
                    nav[index][section_name] = repo_config.get('nav')
                    self.repos.append(repo)
        return config

    def on_files(self, files: Files, config: dict) -> Files:
        temp_config = deepcopy(config)
        temp_config["docs_dir"] = self.temp_dir
        other_repo_files = get_files(temp_config)
        for f in other_repo_files:
            files.append(f)
        return files

    def on_post_build(self, config: dict) -> None:
        if self.temp_dir and self.config.get("cleanup"):
            folder_name = self.config.get("folder_name")
            log.info(f"Multirepo plugin is cleaning up {folder_name}/")
            shutil.rmtree(str(self.temp_dir))
        
        
