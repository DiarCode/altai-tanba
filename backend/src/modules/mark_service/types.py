from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PageImage:
	index: int  # 1-based
	path: Path
	width: int
	height: int


@dataclass
class Detection:
	category: str
	x: float
	y: float
	w: float
	h: float
	area: float
	confidence: float


__all__ = ["PageImage", "Detection"]

