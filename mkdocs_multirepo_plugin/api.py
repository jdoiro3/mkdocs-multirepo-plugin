import yaml
from pathlib import Path
from typing import List, Dict, Any
from .plugin import MultirepoPlugin
from .util import log

class Multirepo:

    def __init__(self, config_file_path: Path = Path() / "multirepo.yml", import_dir: Path = Path()):
        self.config_file_path = config_file_path
        self.import_dir = import_dir
        self._plugin = MultirepoPlugin()
        with open(config_file_path, "r") as f:
            errors, warnings = self._plugin.load_config(yaml.safe_load(f))
        for warn in warnings:
            log.warn(warn)
        if errors:
            raise Exception(errors)
       
        
    def import_docs(self) -> None:
        self._plugin.on_config(
            self._plugin.config, 
            skip_edit_url_derivation=True, 
            import_dir=self.import_dir
            )
        if self._plugin.config.get("cleanup"):
            self._plugin.on_post_build(self._plugin.config)

    def delete_docs(self) -> None:
        self._plugin.on_post_build(self._plugin.config)
