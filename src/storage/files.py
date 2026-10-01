"""Save copies of original measurement files."""

from __future__ import annotations

import shutil
import stat
from os import PathLike
from pathlib import Path


_RAW_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "raw"


def save_original_file(
    source_path: str | PathLike[str], measurement_id: str
) -> Path:
    """Copy a file to the project's data/raw/<measurement_id>/<filename>.

    Keep the source unchanged and return the copied file's absolute path.
    The measurement ID must be a single directory name. Each call needs a
    new measurement directory, even if an existing directory is empty.

    Raises:
        ValueError: The measurement ID is empty or contains a path.
        FileNotFoundError: The source file does not exist.
        IsADirectoryError: The source is not a regular file.
        FileExistsError: The measurement directory or copied file exists.
        OSError: The source cannot be checked or the file cannot be copied.

    If copying fails, the new directory may contain an incomplete file.
    """
    if (
        not isinstance(measurement_id, str)
        or not measurement_id
        or measurement_id in {".", ".."}
        or "/" in measurement_id
        or "\\" in measurement_id
    ):
        raise ValueError("measurement_id must be a single directory name")

    source = Path(source_path)
    try:
        source_stat = source.stat()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Source file does not exist: {source}") from exc
    except OSError as exc:
        raise OSError(f"Could not check source file {source}: {exc}") from exc

    if not stat.S_ISREG(source_stat.st_mode):
        raise IsADirectoryError(f"Source path is not a regular file: {source}")

    directory = _RAW_DIRECTORY / measurement_id
    destination = directory / source.name
    try:
        _RAW_DIRECTORY.mkdir(parents=True, exist_ok=True)
        # Refuse an existing measurement directory, including an empty one.
        directory.mkdir()
        with source.open("rb") as original, destination.open("xb") as copied:
            # Create a new file and copy its bytes without changing the source.
            shutil.copyfileobj(original, copied)
    except FileExistsError as exc:
        raise FileExistsError(
            f"Measurement directory or destination already exists: {directory} "
            f"or {destination}"
        ) from exc
    except OSError as exc:
        raise OSError(f"Could not copy {source} to {destination}: {exc}") from exc

    return destination
