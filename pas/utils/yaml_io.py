from pathlib import Path
from typing import Any

import yaml

from pas.utils.log import logger


def read_yaml_file(file_path: Path | None) -> dict[str, Any] | None:
    if file_path is not None and file_path.exists() and file_path.is_file():
        logger.debug(f"Reading {file_path}")
        data_from_file = yaml.safe_load(file_path.read_text())
        if data_from_file is not None and isinstance(data_from_file, dict):
            return data_from_file
    raise FileExistsError(f"Failed to load YAML file {file_path=}")


def write_yaml_file(
    file_path: Path | None,
    data: dict[str, Any] | None,
    **kwargs,
) -> None:
    if file_path is not None and data is not None:
        logger.debug(f"Writing {file_path}")
        file_path.write_text(yaml.safe_dump(data, **kwargs))
