"""Small helpers shared by the PCT GeoGuesser test suite."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType


def load_module(path: Path, name: str) -> ModuleType:
    """Load a Python file under a test-only module name."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def extract_embedded_photos(html: str) -> list[dict]:
    """Read the JSON array assigned to `const photos` in a generated game page."""
    match = re.search(r"const photos = (\[.*?\]);\s*\n", html, re.DOTALL)
    if not match:
        raise AssertionError("Generated page did not contain an embedded photo array")
    return json.loads(match.group(1))
