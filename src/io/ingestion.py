""" Geting raw data check if the log is propr and return:
{
    "path": "",
    "original_name": "",
    "size": 
}
"""

from __future__ import annotations

import hashlib
from os import PathLike
from pathlib import Path
from typing import Dict, Union


PathInput = Union[str, PathLike[str]]
"""A filesystem path accepted by the ingestion helpers."""

# Keep file handling limited to validation and hashing: measurement contents
# must remain opaque here and must not be interpreted during ingestion.
_HASH_CHUNK_SIZE = 1024 * 1024


def _as_path(path: PathInput) -> Path:
    """Convert a path-like value to :class:`pathlib.Path`."""

    try:
        return Path(path)
    except TypeError as exc:
        raise TypeError("path must be a string or path-like object") from exc


def inspect_file(path: PathInput) -> Dict[str, Union[str, int]]:
    """Validate a file and return basic metadata about it.

    The file must exist, be a regular file, contain at least one byte, and be
    readable as binary data. The returned ``path`` is the path supplied after
    conversion to a string; ``original_name`` is its final path component and
    ``size`` is its size in bytes.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        IsADirectoryError: If ``path`` is not a regular file.
        ValueError: If the file is empty.
        PermissionError: If the file cannot be opened or read.
        OSError: If another filesystem error prevents validation.
    """

    file_path = _as_path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")
    if not file_path.is_file():
        raise IsADirectoryError(f"Path is not a regular file: {file_path}")

    try:
        size = file_path.stat().st_size
    except OSError as exc:
        raise OSError(f"Could not inspect file metadata for {file_path}: {exc}") from exc

    if size == 0:
        raise ValueError(f"File is empty: {file_path}")

    try:
        with file_path.open("rb") as file_handle:
            file_handle.read(1)
    except PermissionError as exc:
        raise PermissionError(f"File is not readable: {file_path}") from exc
    except OSError as exc:
        raise OSError(f"Could not read file {file_path}: {exc}") from exc

    return {
        "path": str(file_path),
        "original_name": file_path.name,
        "size": size,
    }


def calculate_file_hash(path: PathInput) -> str:
    """Return the SHA-256 hash of a file as a hexadecimal string.

    The file is opened in binary mode and read incrementally, allowing files
    larger than available memory to be hashed without loading them all at once.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        IsADirectoryError: If ``path`` is not a regular file.
        PermissionError: If the file cannot be read.
        OSError: If another filesystem error prevents hashing.
    """

    file_path = _as_path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")
    if not file_path.is_file():
        raise IsADirectoryError(f"Path is not a regular file: {file_path}")

    digest = hashlib.sha256()
    try:
        with file_path.open("rb") as file_handle:
            # Chunked binary reads keep memory use bounded for large files and
            # ensure the hash is calculated from the original bytes unchanged.
            for chunk in iter(lambda: file_handle.read(_HASH_CHUNK_SIZE), b""):
                digest.update(chunk)
    except PermissionError as exc:
        raise PermissionError(f"File is not readable: {file_path}") from exc
    except OSError as exc:
        raise OSError(f"Could not read file {file_path}: {exc}") from exc

    return digest.hexdigest()
