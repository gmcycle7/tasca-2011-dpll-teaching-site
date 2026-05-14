"""Shared helpers for demo scripts: project paths, IO, plot styling."""
from __future__ import annotations
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_DIR = RESULTS_DIR / "data"
FIG_DIR = RESULTS_DIR / "figures"

DATA_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def behavioral_caption(ax, extra: str = ""):
    """Stamp a 'behavioral approximation' label on every plot."""
    msg = "Behavioral approximation — not a silicon measurement"
    if extra:
        msg = msg + " | " + extra
    ax.text(0.01, 0.02, msg, transform=ax.transAxes,
            fontsize=8, color="gray", alpha=0.85, va="bottom", ha="left")
