"""Downscale to the target pixel grid with nearest-neighbor sampling.

This is what actually makes the output *look* like pixel art — the diffusion
model produces a smooth 512px image and we crush it down to 32x32 without
interpolation. Any bilinear here would soften edges and defeat the whole point.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from src.pixelgen.processors.base import Processor
from src.pixelgen.jobs import Job


class PixelSnap(Processor):
    def apply(self, job: Job) -> None:
        img = self._require_image(job)
        tw, th = self.cfg.target_res
        pil = Image.fromarray(img)
        snapped = pil.resize((tw, th), Image.NEAREST)
        job.artifacts["image"] = np.asarray(snapped, dtype=np.uint8)
        job.artifacts["target_res"] = (tw, th)