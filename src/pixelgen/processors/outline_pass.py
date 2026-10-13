"""Outline pass. Adds a 1px dark border around non-background pixels.

Background is inferred as the most common color in the corner 2x2 blocks.
This is the cheapest heuristic that works for sprite sheets where the
background is a flat fill.
"""
from __future__ import annotations

import numpy as np

from src.pixelgen.processors.base import Processor
from src.pixelgen.jobs import Job


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


class OutlinePass(Processor):
    def apply(self, job: Job) -> None:
        img = self._require_image(job)
        h, w, _ = img.shape
        corners = np.concatenate([
            img[0:2, 0:2].reshape(-1, 3),
            img[0:2, -2:].reshape(-1, 3),
            img[-2:, 0:2].reshape(-1, 3),
            img[-2:, -2:].reshape(-1, 3),
        ])
        vals, counts = np.unique(corners, axis=0, return_counts=True)
        bg = vals[counts.argmax()]
        mask = np.any(img != bg, axis=-1)
        outline = img.copy()
        color = np.array(_hex_to_rgb(self.cfg.color), dtype=np.uint8)
        t = self.cfg.thickness
        for dy in range(-t, t + 1):
            for dx in range(-t, t + 1):
                if dx == 0 and dy == 0:
                    continue
                shifted = np.roll(np.roll(mask, dy, axis=0), dx, axis=1)
                edge = shifted & ~mask
                outline[edge] = color
        job.artifacts["image"] = outline