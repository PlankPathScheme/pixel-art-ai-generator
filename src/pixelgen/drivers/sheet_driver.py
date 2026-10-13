"""Tile a batch of sprites into a sprite sheet with a fixed column count.

Layout: row-major, left-to-right, top-to-bottom. Each tile padded by
`tile_pad` pixels of transparent background so engines that sample with
bleed don't pull neighbor pixels.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from src.pixelgen.drivers.base import OutputDriver
from src.pixelgen.jobs import Job


class SheetDriver(OutputDriver):
    def write(self, job: Job) -> Path:
        batch = job.artifacts.get("image_batch") or [job.artifacts.get("image")]
        batch = [np.asarray(b, dtype=np.uint8) for b in batch if b is not None]
        if not batch:
            raise RuntimeError("no images to write")
        th, tw, _ = batch[0].shape
        cols = max(1, self.cfg.sheet_columns)
        rows = (len(batch) + cols - 1) // cols
        pad = self.cfg.tile_pad
        cell_w, cell_h = tw + pad * 2, th + pad * 2
        sheet = np.zeros((rows * cell_h, cols * cell_w, 4), dtype=np.uint8)
        for i, tile in enumerate(batch):
            r, c = divmod(i, cols)
            y0 = r * cell_h + pad
            x0 = c * cell_w + pad
            sheet[y0:y0 + th, x0:x0 + tw, :3] = tile
            sheet[y0:y0 + th, x0:x0 + tw, 3] = 255
        out = Path(job.out)
        if out.suffix.lower() != ".png":
            out = out.with_suffix(".png")
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(sheet, mode="RGBA").save(out, format="PNG", optimize=self.cfg.png_optimize)
        if self.cfg.metadata_sidecar:
            meta = {
                "job_id": job.id,
                "columns": cols,
                "rows": rows,
                "tile_size": [tw, th],
                "pad": pad,
                "count": len(batch),
                "seed": job.artifacts.get("seed"),
            }
            out.with_suffix(".sheet.json").write_text(json.dumps(meta,