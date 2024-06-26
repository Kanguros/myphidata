import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict
from typer import get_app_dir

from pas.utils.log import logger
from pas.utils.yaml_io import read_yaml_file

APP_NAME = "pas"
APP_DIR = Path(get_app_dir(APP_NAME, roaming=False))

LOG_FILE_NAME = "debug.log"
LOG_FILE_PATH = APP_DIR / LOG_FILE_NAME

CONFIG_ENV_NAME = "PAS_CONFIG_PATH"
"""Environment variable to config file."""
CONFIG_FILE_NAME = "config.yaml"
"""Default name of the configuration file."""
CONFIG_DEFAULT_PATH = APP_DIR / CONFIG_FILE_NAME
"""Default configuration path."""
CONFIG_PATH = Path(os.getenv(CONFIG_ENV_NAME, CONFIG_DEFAULT_PATH))


class Config(BaseModel):
    name: str
    description: str
    instructions: Optional[list[str]] = None
    model: str = "llama3"
    markdown: bool = True
    add_storage: bool = True

    file_path: Optional[Path] = None
    dir_path: Optional[Path] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_file(cls, file_path: str) -> "Config":
        file_path = Path(file_path)
        config_kwargs = {}
        if file_path.exists():
            logger.debug(f"Loading config from: {file_path}")
            config_kwargs = read_yaml_file(file_path)

        file_path.parent.mkdir(exist_ok=True)
        return cls(**config_kwargs, file_path=file_path, dir_path=file_path.parent)
