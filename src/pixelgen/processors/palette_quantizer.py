"""Palette quantizer. Snaps every pixel to the nearest color in a fixed LUT.

Uses a precomputed KD-tree over the palette in RGB space for O(log N) lookup
per pixel. For a 32x32 sprite that's ~1k lookups — negligible. For a 512x512
intermediate it's ~260k lookups, still under 30ms on a modern CPU.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml
from scipy.spatial import cKDTree

from src.pixelgen.processors.base import Processor
from src.pixelgen.jobs import Job


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


class PaletteQuantizer(Processor):
    _tree_cache: dict[str, tuple[cKDTree, np.ndarray]] = {}

    def _palette(self) -> tuple[cKDTree, np.ndarray]:
        path = self.cfg.palette or "config/palettes/db16.yaml"
        if path in PaletteQuantizer._tree_cache:
            return PaletteQuantizer._tree_cache[path]
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        colors = np.array([_hex_to_rgb(c) for c in data["colors"]], dtype=np.float32)
        tree = cKDTree(colors)
        PaletteQuantizer._tree_cache[path] = (tree, colors)
        return tree, colors

    def apply(self, job: Job) -> None:
        img = self._require_image(job)
        tree, colors = self._palette()
        h, w, _ = img.shape
        flat = img.reshape(-1, 3).astype(np.float32)
        _, idx = tree.query(flat, k=1)
        quant = colors[idx].astype(np.uint8).reshape(h, w, 3)
        job.artifacts["image"] = quant
        job.artifacts["palette_used"] = self.cfg.palette