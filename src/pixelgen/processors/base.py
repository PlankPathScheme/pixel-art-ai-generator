"""Base processor contract. Every processor reads/writes job.artifacts['image']."""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from src.pixelgen.config import ProcessorConfig
from src.pixelgen.jobs import Job


class Processor(ABC):
    def __init__(self, cfg: ProcessorConfig, device: str = "auto") -> None:
        self.cfg = cfg
        self.device = device

    @abstractmethod
    def apply(self, job: Job) -> None: ...

    @staticmethod
    def _require_image(job: Job) -> np.ndarray:
        img = job.artifacts.get("image")
        if img is None:
            raise RuntimeError("no image in job.artifacts — diffusion_sampler must run first")
        return img