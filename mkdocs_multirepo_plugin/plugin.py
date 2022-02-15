from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import get_files, Files
from mkdocs.config import config_options
from mkdocs.theme import Theme
from mkdocs.config import Config, defaults
from .structure import (
    Repo, DocsRepo, parse_import, parse_repo_url, batch_import
    )
from .util import ImportDocsException, log, get_src_path_root
from pathlib import Path
from copy import deepcopy
import shutil
import asyncio

IMPORT_STATEMENT = "!import"


class MultirepoPlugin(BasePlugin):

    config_scheme = (
        ("cleanup", config_options.Type(bool, default=True)),
        ("temp_dir", config_options.Type(str, default="temp_dir")),
        ("repos", config_options.Type(list, default=[])),
        ("url", config_options.Type(str, default=None)),
        # used when developing in repo that is imported
        ("custom_dir", config_options.Type(str, default=None)),
        ("yml_file", config_options.Type(str, default=None)),
        ("imported_repo", config_options.Type(bool, default=False)),
        ("dirs", config_options.Type(list, default=[])),
        ("branch", config_options.Type(str, default=None))
    )

    def __init__(self):
        self.temp_dir = None
        self.repos = {}

    def handle_imported_repo(self, config: Config) -> Config:
        """Imports necessary files for serving site in an imported repo"""
        repo = Repo(
            "importee", self.config.get("url"), self.config.get("branch"),
            self.temp_dir
        )
        repo.import_config_files(self.config.get("dirs"))
        new_config = repo.load_config(self.config.get("yml_file"))
        # remove nav
        if "nav" in new_config:
            del new_config["nav"]
        # update plugins
        if "plugins" in new_config:
            plugins_copy = deepcopy(new_config["plugins"])
            for p in plugins_copy:
                if "search" in p:
                    log.info("removing search")
                    new_config["plugins"].remove(p)
                if "multirepo" in p:
                    new_config["plugins"].remove(p)
                    new_config["plugins"].append({"multirepo": {"imported_repo": True}})
            # validate and provide PluginCollection object to config
            plugins = config_options.Plugins()
            plugin_collection = plugins.validate(new_config.get("plugins"))
            new_config["plugins"] = plugin_collection
        # update theme
        if "theme" in new_config:
            del new_config["theme"]["custom_dir"]
            new_config["theme"] = Theme(
                custom_dir=str(repo.location / self.config.get("custom_dir")),
                **new_config["theme"]
            )
        # update this repo's config with the main repo's config
        config.update(new_config)
        # needs to be a dict
        new_config = dict(config)
        # update dev address
        dev_addr = config_options.IpAddress()
        addr = dev_addr.validate(new_config.get("dev_addr"))
        config["dev_addr"] = (addr.host, addr.port)
        # create new config object
        config = Config(defaults.get_schema())
        config.load_dict(new_config)
        config.validate()
        return config

    def handle_nav_based_import(self, config: Config) -> Config:
        """Imports documentation in other repos based on nav configuration"""
        nav = config.get('nav')
        repo_instances = []
        for index, entry in enumerate(nav):
            (section_name, value), = entry.items()
            if type(value) is str:
                if value.startswith(IMPORT_STATEMENT):
                    import_stmt = parse_import(value)
                    repo = DocsRepo(
                        section_name, import_stmt.get("url"),
                        self.temp_dir,
                        import_stmt.get("docs_dir", "docs/*"),
                        import_stmt.get("branch", "master"),
                        bool(import_stmt.get("multi_docs", False))
                    )
                    repo_instances.append(repo)
        asyncio.run(batch_import(repo_instances))
        for repo in repo_instances:
            repo_config = repo.load_config("mkdocs.yml")
            if not repo_config.get("nav"):
                raise ImportDocsException(f"{repo.name}'s mkdocs.yml file doesn't have a nav section")
            repo.set_edit_uri(repo_config.get("edit_uri"))
            nav[index][section_name] = repo_config.get('nav')
            self.repos[repo.name] = repo
        return config

    def handle_repos_based_import(self, config: Config, repos: list) -> Config:
        """Imports documentation in other repos based on repos configuration"""
        repo_instances = []
        for repo in repos:
            import_stmt = parse_repo_url(repo.get("import_url"))
            repo = DocsRepo(
                repo.get("section"), import_stmt.get("url"),
                self.temp_dir, repo.get("docs_dir", "docs/*"),
                import_stmt.get("branch", "master"), repo.get("edit_uri"),
                bool(repo.get("multi_docs", False))
                )
            repo_instances.append(repo)
        asyncio.run(batch_import(repo_instances))
        for repo in repo_instances:
            log.info(f"Multirepo plugin is imported docs for section {repo.name}")
            self.repos[repo.name] = repo
        return config

    def on_config(self, config: Config) -> Config:

        docs_dir = Path(config.get('docs_dir'))
        self.temp_dir = docs_dir.parent / self.config.get("temp_dir")
        if not self.temp_dir.is_dir():
            self.temp_dir.mkdir()
        if self.config.get("imported_repo"):
            return self.handle_imported_repo(config)
        else:
            repos = self.config.get("repos")
            if not config.get('nav') and not repos:
                return config
            if config.get('nav') and repos:
                log.warning("Multirepo plugin is ignoring plugins.multirepo.repos. Nav takes precedence")
            # nav takes precedence over repos
            if config.get("nav"):
                return self.handle_nav_based_import(config)
            # navigation isn't defined but plugin section has repos
            if repos:
                return self.handle_repos_based_import(config, repos)

    def on_files(self, files: Files, config: Config) -> Files:
        if self.config.get("imported_repo"):
            return files
        else:
            temp_config = deepcopy(config)
            temp_config["docs_dir"] = self.temp_dir
            other_repo_files = get_files(temp_config)
            for f in other_repo_files:
                files.append(f)
            return files

    def on_nav(self, nav, config: Config, files: Files):
        if self.config.get("imported_repo"):
            return nav
        else:
            for f in files:
                root_src_path = get_src_path_root(f.src_path)
                if root_src_path in self.repos and f.page:
                    repo = self.repos.get(root_src_path)
                    f.page.edit_url = repo.get_edit_url(f.src_path)
            return nav

    def on_post_build(self, config: Config) -> None:
        if self.config.get("imported_repo") and self.config.get("cleanup"):
            shutil.rmtree(str(self.temp_dir))
        else:
            if self.temp_dir and self.config.get("cleanup"):
                temp_dir = self.config.get("temp_dir")
                log.info(f"Multirepo plugin is cleaning up {temp_dir}/")
                shutil.rmtree(str(self.temp_dir))
