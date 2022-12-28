import yaml
from pathlib import Path
from typing import List, Dict, Any
from .plugin import MultirepoPlugin
from .util import log

class Multirepo:

    def __init__(self, config_file_path: str = "multirepo.yml"):
        self._plugin = MultirepoPlugin()
        with open(config_file_path, "r") as f:
            errors, warnings = self._plugin.load_config(yaml.safe_load(f))
        for warn in warnings:
            log.warn(warn)
        if errors:
            raise Exception(errors)
       
        
    def import_docs(self) -> None:
        self._plugin.on_config(self._plugin.config, skip_edit_url_derivation=True)
