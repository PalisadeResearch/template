from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Env:
    """
    Data here will *not* be a part of a run history.
    """

    run_path: Path
    readme: str

    # TODO: add handles and capabilities here
