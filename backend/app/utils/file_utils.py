# app/utils/file_utils.py
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def ensure_directory_exists(dir_path: Path) -> None:
    """
    Ensures that the specified directory exists. Creates it if it doesn't.

    Args:
        dir_path: The Path object representing the directory.

    Raises:
        OSError: If the directory cannot be created due to permission issues or other OS errors.
    """
    try:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        elif not dir_path.is_dir():
            logger.error(f"Path exists but is not a directory: {dir_path}")
            raise OSError(f"Path exists but is not a directory: {dir_path}")
    except OSError as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        raise  # Re-raise the exception after logging