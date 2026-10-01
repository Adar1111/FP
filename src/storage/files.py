"""Save copies of original measurement files."""

import shutil
from pathlib import Path


_RAW_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "raw"


def save_original_file(source_path: str | Path, measurement_id: str) -> Path:  # Save original file copy
    """Copy a file to data/raw/<measurement_id>/<original_filename>.

    Return the copied file's path. Keep the source unchanged.
    Raise an error for an invalid source, an existing destination, or a
    failed copy. A failed copy may leave an incomplete destination file.
    """
    source = Path(source_path)

    if not source.exists():
        raise FileNotFoundError(f"Source file does not exist: {source}")
    if not source.is_file():
        raise IsADirectoryError(f"Source path is not a regular file: {source}")

    if measurement_id in ("", ".", ".."):
        raise ValueError("measurement_id must be a directory name")
    if "/" in measurement_id or "\\" in measurement_id:
        raise ValueError("measurement_id must not contain a path")

    directory = _RAW_DIRECTORY / measurement_id
    destination = directory / source.name
    try:
        _RAW_DIRECTORY.mkdir(parents=True, exist_ok=True)
        directory.mkdir()
        # "xb" creates a new file and refuses to overwrite an existing file.
        with source.open("rb") as original, destination.open("xb") as copied:
            shutil.copyfileobj(original, copied)
    except FileExistsError as exc:
        raise FileExistsError(f"Destination already exists: {directory} or {destination}") from exc #try to find out why it fail
    except OSError as exc:
        raise OSError(f"Could not copy {source} to {destination}: {exc}") from exc

    return destination
