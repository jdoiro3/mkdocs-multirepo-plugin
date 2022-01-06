from logging import root
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import get_files, Files
from mkdocs.config import config_options
from mkdocs.theme import Theme
from .structure import (
    DocsRepo, import_serve_files, parse_import, 
    parse_repo_url, get_src_path_root
    )
from .util import log, remove_parents
from pathlib import Path
from copy import deepcopy
import shutil
import os

IMPORT_STATEMENT = "!import"

class MultirepoPlugin(BasePlugin):

    config_scheme = (
        ("cleanup", config_options.Type(bool, default=True)),
        ("temp_dir", config_options.Type(str, default="temp_docs")),
        ("repos", config_options.Type(list, default=[])),
        ("included_repo", config_options.Type(bool, default=False)),
        ("url", config_options.Type(str, default=None)),
        ("custom_dir", config_options.Type(str, default=None)),
        ("yml_file", config_options.Type(str, default=None)),
        ("branch", config_options.Type(str, default=None))
    )

    def __init__(self, included_repo=False):
        self.temp_dir = None
        self.repos = {}
        self.included_repo = included_repo

    def on_config(self, config: dict) -> dict:

        docs_dir = Path(config.get('docs_dir'))
        self.temp_dir = docs_dir.parent / self.config.get("temp_dir")

        if self.config.get("included_repo"):
            config_path, imported_config = import_serve_files(docs_dir.parent, self.config)
            for p in imported_config["plugins"]:
                if "multirepo" in p:
                    imported_config["plugins"].remove(p)
            config.update(imported_config)
            # update plugins
            plugins = config_options.Plugins(default=imported_config.get("plugins"))
            plugin_collection = plugins.validate(None)
            config["plugins"] = plugin_collection
            config["plugins"]["multirepo"] = MultirepoPlugin(included_repo=True)
            # update markdown extensions
            md_exts = config_options.MarkdownExtensions()
            config['markdown_extensions'] = md_exts.validate(config.get("markdown_extensions"))
            # update dev_addr
            dev_addr = config_options.IpAddress()
            dev_addr = dev_addr.validate(config.get("dev_addr"))
            config["dev_addr"] = (dev_addr.host, dev_addr.port)
            # update theme
            if imported_config.get("theme"):
                del imported_config["theme"]["custom_dir"]
                name = imported_config["theme"]["name"]
                del imported_config["theme"]["name"]
                config["theme"] = Theme(
                    name = name,
                    custom_dir = self.config.get("custom_dir"),
                    **imported_config["theme"]
                )
            return config
        else:
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
                    edit_uri = repo.get("edit_uri")
                    repo = DocsRepo(
                        repo.get("section"), repo_url, docs_dir=repo.get("docs_dir", "docs"), 
                        branch=branch, edit_uri=edit_uri
                        )
                    log.info(f"Multirepo plugin is importing docs for section {repo.name}")
                    repo.import_docs(self.temp_dir)
                    self.repos[repo.name] = repo
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
                        log.info(f"Multirepo plugin is importing docs for section {repo.name}")
                        repo.import_docs(self.temp_dir)
                        repo_config = repo.load_mkdocs_yaml(self.temp_dir)
                        repo.set_edit_uri(repo_config.get("edit_uri"))
                        nav[index][section_name] = repo_config.get('nav')
                        self.repos[repo.name] = repo
            return config


    def on_files(self, files: Files, config: dict) -> Files:
        if self.included_repo:
            return files
        else:
            temp_config = deepcopy(config)
            temp_config["docs_dir"] = self.temp_dir
            other_repo_files = get_files(temp_config)
            for f in other_repo_files:
                files.append(f)
            return files


    def on_nav(self, nav, config, files):
        if self.included_repo:
            return nav
        else:
            for f in files:
                root_src_path = get_src_path_root(f.src_path)
                if root_src_path in self.repos and f.page:
                    repo = self.repos.get(root_src_path)
                    src_path = remove_parents(f.src_path, 1)
                    f.page.edit_url = repo.url + repo.edit_uri + repo.docs_dir + src_path
            return nav
        

    def on_post_build(self, config: dict) -> None:
        if self.included_repo:
            shutil.rmtree("overrides")
            os.remove("multirepo.yml")
        else:
            if self.temp_dir and self.config.get("cleanup"):
                temp_dir = self.config.get("temp_dir")
                log.info(f"Multirepo plugin is cleaning up {temp_dir}/")
                shutil.rmtree(str(self.temp_dir))
        
        
