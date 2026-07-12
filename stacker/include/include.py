from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from stacker.error import IncludeError
from stacker.include.stk_file_read import readtxt
from stacker.syntax.parser import remove_start_end_quotes

if TYPE_CHECKING:
    from stacker.stacker import Stacker


# Files currently being included, used to detect circular includes
_including: set[Path] = set()


def resolve_include_path(filename: str | Path, base_dir: Path | None = None) -> Path:
    """Resolve an include target using the search order.

    Absolute paths are taken as-is. Relative paths are searched first in
    ``base_dir`` (the including file's directory), then the current
    working directory. A future library path becomes one more entry in
    the search list.

    Args:
        filename: Include target as written in the script.
        base_dir: Directory of the including file, or None when the
            includer has no file context (REPL, ``-e``).

    Returns:
        The first existing candidate path.

    Raises:
        IncludeError: If no candidate exists (the message lists every
            tried absolute path) or the match is not a ``.stk`` file.
    """
    path = Path(filename)
    if path.is_absolute():
        candidates = [path]
    else:
        search_dirs = [Path(base_dir)] if base_dir is not None else []
        search_dirs.append(Path.cwd())
        candidates = [directory / path for directory in search_dirs]

    for candidate in candidates:
        if candidate.is_file():
            if candidate.suffix != ".stk":
                raise IncludeError(f"File {filename} is not a stacker script.")
            return candidate

    tried = ", ".join(str(candidate.resolve()) for candidate in candidates)
    raise IncludeError(f"File {filename} not found. Tried: {tried}")


def include_stacker_script(
    filename: str | Path, base_dir: Path | None = None
) -> Stacker:
    """Import a stacker script and return the stacker object.

    Args:
        filename: Include target as written in the script.
        base_dir: Directory of the including file for relative
            resolution; None falls back to cwd-only search (keeps the
            pre-1.12.0 behavior for direct callers).

    Raises:
        IncludeError: If the file cannot be resolved, has a wrong
            extension, or is already being included (circular include).
    """
    if isinstance(filename, str):
        filename = remove_start_end_quotes(filename)

    found = resolve_include_path(filename, base_dir)
    resolved = found.resolve()
    if resolved in _including:
        raise IncludeError(f"Circular include detected: {filename}")

    script_content = readtxt(found)

    from stacker.stacker import Stacker

    _including.add(resolved)
    try:
        stacker = Stacker()
        # The included file becomes the child's file context, so its own
        # includes resolve relative to its directory (nested includes)
        stacker.current_file = str(resolved)
        stacker.process_expression(script_content)
    finally:
        _including.discard(resolved)
    return stacker
