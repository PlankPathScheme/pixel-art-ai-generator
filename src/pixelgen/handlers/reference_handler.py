"""Load a reference sprite, validate it, and stash as an RGB numpy array.

Gotcha: Pillow opens GIFs in palette mode by default. We force convert("RGBA")
then flatten alpha against white before handing to the sampler, otherwise
transparent regions turn into black blobs after diffusion.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from src.pixelgen.handlers.base import IngestHandler
from src.pixelgen.jobs import Job


class ReferenceHandler(IngestHandler):
    def ingest(self, job: Job) -> None:
        if job.reference is None:
            job.artifacts["reference_rgb"] = None
            return
        p = Path(job.reference)
        if not p.exists():
            raise FileNotFoundError(f"reference not found: {p}")
        max_size = int(self.options.get("max_size", 512))
        img = Image.open(p).convert("RGBA")
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.NEAREST)
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.alpha_composite(img)
        rgb = np.asarray(bg.convert("RGB"), dtype=np.uint8)
        job.artifacts["reference_rgb"] = rgb
        job.artifacts["reference_size"] = rgb.shape[:2]