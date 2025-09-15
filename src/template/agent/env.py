from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Settings


@dataclass
class Env:
    """
    Data here will *not* be a part of a run history.
    """

    settings: Settings
    run_path: Path
    # TODO: add handles and capabilities here
