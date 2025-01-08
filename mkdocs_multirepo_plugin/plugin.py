import shutil
import tempfile
from copy import deepcopy
from dataclasses import _MISSING_TYPE, dataclass, field, fields
from pathlib import Path
from typing import Dict, List, Optional

import dacite as dc
from mkdocs.config import Config, config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File, Files
from mkdocs.theme import Theme
from slugify import slugify
from typing_inspect import get_origin

from .structure import (
    DocsRepo,
    Repo,
    batch_execute,
    batch_import,
    get_files,
    get_import_stmts,
    is_yaml_file,
    parse_repo_url,
    resolve_nav_paths,
)
from .util import ImportDocsException, ImportSyntaxError, asyncio_run, is_windows, log

if is_windows():
    # allow for ASCII escape codes to be used in terminal
    import os

    os.system("")

IMPORT_STATEMENT = "!import"
DEFAULT_BRANCH = "master"


class ReposConfigException(Exception):
    pass


@dataclass
class RepoConfig:
    section: str
    import_url: str
    section_path: Optional[str] = None


@dataclass
class NavRepoConfig:
    name: str
    import_url: str
    imports: List[str] = field(default_factory=list)
    section_path: Optional[str] = None

@dataclass
class MultirepoConfig:
    cleanup: bool = True
    repos: List[RepoConfig] = field(default_factory=list)
    nav_repos: List[NavRepoConfig] = field(default_factory=list)
    imported_repo: bool = False
    temp_dir: str = "temp_dir"
    keep_docs_dir: bool = False
    section_name: str = "imported"
    url: Optional[str] = None
    dirs: Optional[List[str]] = None
    custom_dir: Optional[str] = None
    yml_file: Optional[str] = None
    branch: Optional[str] = None


class MultirepoPlugin(BasePlugin):

    config_scheme = tuple(
        (
            f.name,
            config_options.Type(
                get_origin(f.type) or f.type,
                default=f.default
                if not isinstance(f.default, _MISSING_TYPE)
                else f.default_factory(),
            ),
        )
        for f in fields(MultirepoConfig)
    )

    def __init__(self):
        self.temp_dir: Path = None
        self.repos: Dict[str, DocsRepo] = {}
        self.nav_repos: Dict[str, DocsRepo] = {}

    def derive_config_edit_uri(
        self, repo_name: str, repo_url: str, config: Config
    ) -> str:
        """returns the derived edit_uri based on the imported repo's url"""
        repo_url_key = f"{repo_name}_repo_url"
        # temporarily set a new config value b/c EditURI uses it
        config[repo_url_key] = repo_url
        edit_uri_obj = config_options.EditURI(repo_url_key)
        # sets the mkdocs edit_uri in place
        edit_uri_obj.post_validation(config, "edit_uri")
        derived_edit_uri = config.get("edit_uri", "")
        # we just used mkdocs machinery to get the derived value and
        # now we can delete these two config entries
        del config["edit_uri"]
        del config[repo_url_key]
        return derived_edit_uri

    def setup_imported_repo(self, config: Config) -> Path:
        temp_dir = tempfile.mkdtemp(prefix="multirepo_")
        temp_section_dir = Path(temp_dir) / "docs" / self.config.get("section_name")
        temp_section_dir.mkdir(parents=True)
        shutil.copytree(
            config.get("docs_dir"), str(temp_section_dir), dirs_exist_ok=True
        )
        return temp_dir

    def handle_imported_repo(self, config: Config) -> Config:
        """Imports necessary files for serving site in an imported repo"""
        temp_dir = Path(self.setup_imported_repo(config))
        parent_repo = Repo(
            "importee", self.config.get("url"), self.config.get("branch"), temp_dir
        )
        parent_repo.temp_dir.mkdir(exist_ok=True)
        asyncio_run(parent_repo.sparse_clone(self.config.get("paths")))
        shutil.copytree(
            str(parent_repo.location / "docs"),
            str(temp_dir / "docs"),
            dirs_exist_ok=True,
        )

        new_config = parent_repo.load_config(self.config.get("yml_file"))
        # remove parent nav
        if "nav" in new_config:
            del new_config["nav"]
        # update plugins
        if "plugins" in new_config:
            plugins_copy = deepcopy(new_config["plugins"])
            for p in plugins_copy:
                if "search" in p:
                    log.info("Multirepo removing search")
                    new_config["plugins"].remove(p)
                if "multirepo" in p:
                    new_config["plugins"].remove(p)
            # validate and provide PluginCollection object to config
            plugins = config_options.Plugins()
            plugin_collection = plugins.validate(new_config.get("plugins"))
            plugin_collection["multirepo"] = self
            new_config["plugins"] = plugin_collection
        # update theme
        if "theme" in new_config:
            del new_config["theme"]["custom_dir"]
            new_config["theme"] = Theme(
                custom_dir=str(parent_repo.location / self.config.get("custom_dir")),
                **new_config["theme"],
            )
        # update docs dir to point to temp_dir
        new_config["docs_dir"] = str(temp_dir / "docs")
        # resolve the nav paths
        if config.get("nav"):
            resolve_nav_paths(config.get("nav"), self.config.get("section_name"))
        # update this repo's config with the main repo's config
        config.update(new_config)
        # update markdown externsions
        option = config_options.MarkdownExtensions()
        config["markdown_extensions"] = option.validate(config["markdown_extensions"])
        # update dev address
        dev_addr = config_options.IpAddress()
        addr = dev_addr.validate(new_config.get("dev_addr") or "127.0.0.1:8000")
        config["dev_addr"] = (addr.host, addr.port)
        return config, temp_dir

    def handle_nav_import(self, config: Config) -> Config:
        """Imports documentation in other repos based on nav configuration"""
        keep_docs_dir: bool = self.config.get("keep_docs_dir")
        nav: List[Dict] = config.get("nav")
        nav_imports = get_import_stmts(nav, self.temp_dir, DEFAULT_BRANCH)
        repos: List[DocsRepo] = [nav_import.repo for nav_import in nav_imports]
        asyncio_run(batch_import(repos, keep_docs_dir=keep_docs_dir))
        need_to_derive_edit_uris = config.get("edit_uri") is None

        for nav_import, repo in zip(nav_imports, repos):
            repo_config = repo.load_config()
            if not repo_config.get("nav"):
                raise ImportDocsException(
                    f"{repo.name}'s {repo.config} file doesn't have a nav section"
                )
            # mkdocs config values edit_uri and repo_url aren't set
            if need_to_derive_edit_uris:
                derived_edit_uri = self.derive_config_edit_uri(
                    repo.name, repo.url, config
                )
            repo.set_edit_uri(
                repo_config.get("edit_uri")
                or config.get("edit_uri")
                or derived_edit_uri
            )
            # Change the section title value from '!import {url}' to the imported repo's nav
            # Note: this changes config.nav in place
            nav_import.set_section_value(repo_config.get("nav"))
            self.repos[repo.name] = repo
        return config

    def handle_repos_import(self, config: Config, repos: List[RepoConfig]) -> Config:
        """Imports documentation in other repos based on repos configuration"""
        need_to_derive_edit_uris: bool = config.get("edit_uri") is None
        docs_repo_objs: List[DocsRepo] = []
        for repo in repos:
            import_stmt = parse_repo_url(repo.import_url)
            if "!import" in import_stmt.get("url"):
                raise ImportSyntaxError(
                    "import_url should only contain the url with plugin accepted params. You included '!import'."
                )
            section_slug = slugify(text=repo.section, lowercase=False)
            path = repo.section_path
            repo_name = f"{path}/{section_slug}" if path is not None else section_slug
            # mkdocs config values edit_uri and repo_url aren't set
            if need_to_derive_edit_uris:
                derived_edit_uri = self.derive_config_edit_uri(
                    repo_name, import_stmt.get("url"), config
                )
            docs_repo_objs.append(
                DocsRepo(
                    name=repo_name,
                    url=import_stmt.get("url"),
                    temp_dir=self.temp_dir,
                    docs_dir=import_stmt.get("docs_dir", "docs/*"),
                    branch=import_stmt.get("branch", DEFAULT_BRANCH),
                    edit_uri=import_stmt.get("edit_uri")
                    or config.get("edit_uri")
                    or derived_edit_uri,
                    multi_docs=bool(import_stmt.get("multi_docs", False)),
                    extra_imports=import_stmt.get("extra_imports", []),
                    keep_docs_dir=import_stmt.get("keep_docs_dir"),
                )
            )
        asyncio_run(batch_import(docs_repo_objs))
        for dr in docs_repo_objs:
            self.repos[dr.name] = dr
        return config

    def handle_nav_repos_import(
        self, config: Config, nav_repos: List[NavRepoConfig]
    ) -> Config:
        need_to_derive_edit_uris = config.get("edit_uri") is None
        docs_repo_objs: List[DocsRepo] = []
        for nr in nav_repos:
            import_stmt = parse_repo_url(nr.import_url)
            section_slug: str = slugify(nr.name)
            path = repo.section_path
            name = f"{path}/{section_slug}" if path is not None else section_slug
            
            # mkdocs config values edit_uri and repo_url aren't set
            if need_to_derive_edit_uris:
                derived_edit_uri = self.derive_config_edit_uri(
                    name, import_stmt.get("url"), config
                )
            repo: DocsRepo = DocsRepo(
                name=name,
                url=import_stmt.get("url"),
                temp_dir=self.temp_dir,
                branch=import_stmt.get("branch", DEFAULT_BRANCH),
                paths=nr.imports,
                edit_uri=import_stmt.get("edit_uri")
                or config.get("edit_uri")
                or derived_edit_uri,
            )
            if repo.cloned:
                repo.delete_repo()
            docs_repo_objs.append(repo)
            self.repos[repo.name] = repo
        asyncio_run(batch_execute(repos=docs_repo_objs, method=Repo.sparse_clone))
        return config

    def on_config(self, config: Config) -> Config:
        try:
            multi_config: MultirepoConfig = dc.from_dict(
                data_class=MultirepoConfig,
                data=self.config,
                config=dc.Config(strict=True),
            )
        except dc.UnexpectedDataError as e:
            formatted_keys = ", ".join(f'"{key}"' for key in e.keys)
            raise ReposConfigException(
                f"unknown config key(s), {formatted_keys}, for MultirepoConfig"
            )
        if multi_config.imported_repo:
            config, temp_dir = self.handle_imported_repo(config)
            self.temp_dir = temp_dir
            return config
        else:
            docs_dir = Path(config.get("docs_dir"))
            self.temp_dir = docs_dir.parent / multi_config.temp_dir
            if not self.temp_dir.is_dir():
                self.temp_dir.mkdir()
            repos: RepoConfig = multi_config.repos
            nav_repos: NavRepoConfig = multi_config.nav_repos
            nav: Optional[Dict[str, ...]] = config.get("nav")
            if not nav and not repos and not nav_repos:
                return config
            if nav and repos:
                log.warning(
                    "Multirepo plugin is ignoring plugins.multirepo.repos. Nav takes precedence."
                )
            if not nav and nav_repos:
                log.warning(
                    "Multirepo plugin has nav_repos configuration without a nav section."
                )
            log.info("Multirepo plugin importing docs...")
            # nav takes precedence over repos
            if nav:
                config = self.handle_nav_import(config)
                if nav_repos:
                    return self.handle_nav_repos_import(config, nav_repos)
                return config
            # navigation isn't defined but plugin section has repos
            return self.handle_repos_import(config, repos)

    def on_files(self, files: Files, config: Config) -> Files:
        if self.config.get("imported_repo"):
            return files
        else:
            repo_files: List[File]
            for repo in self.repos.values():
                repo_files = get_files(config, repo)
                repo_config_path = repo.config_path
                for f in repo_files:
                    if f.src_path == repo_config_path:
                        log.info(
                            f"Multirepo plugin is not copying config file: {f.src_path}"
                        )
                    else:
                        # the file needs to know about the repo it belongs to
                        f.repo = repo
                        files.append(f)
            return files

    def on_nav(self, nav, config: Config, files: Files):
        if self.config.get("imported_repo"):
            return nav
        else:
            for f in files:
                repo = f.repo if hasattr(f, "repo") else None
                if repo and f.page:
                    f.page.edit_url = repo.get_edit_url(
                        f.src_path,
                        self.config.get("keep_docs_dir"),
                        self.config.get("nav_repos"),
                    )
            return nav

    def on_post_build(self, config: Config) -> None:
        if self.config.get("imported_repo"):
            config["docs_dir"] = "docs"
            shutil.rmtree(str(self.temp_dir))
        elif self.temp_dir and self.config.get("cleanup"):
            temp_dir = self.config.get("temp_dir")
            log.info(f"Multirepo plugin is cleaning up {temp_dir}/")
            shutil.rmtree(str(self.temp_dir))

    def on_build_error(self, error):
        if self.temp_dir:
            shutil.rmtree(str(self.temp_dir))
