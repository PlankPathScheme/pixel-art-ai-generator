"""Write a single sprite PNG plus optional JSON sidecar."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from src.pixelgen.drivers.base import OutputDriver
from src.pixelgen.jobs import Job


class SingleDriver(OutputDriver):
    def write(self, job: Job) -> Path:
        img = job.artifacts.get("image")
        if img is None:
            raise RuntimeError("no image to write")
        out = Path(job.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(np.asarray(img, dtype=np.uint8)).save(
            out, format="PNG", optimize=self.cfg.png_optimize
        )
        if self.cfg.metadata_sidecar:
            sidecar = out.with_suffix(".json")
            sidecar.write_text(json.dumps({
                "job_id": job.id,
                "prompt": job.artifacts.get("prompt_clean"),
                "seed": job.artifacts.get("seed"),
                "palette": job.artifacts.get("palette_used"),
                "target_res": job.artifacts.get("target_res"),
            }, indent=2), encoding="utf-8")
        return out