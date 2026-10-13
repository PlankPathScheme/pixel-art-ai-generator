"""Base output driver contract."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.pixelgen.config import OutputConfig
from src.pixelgen.jobs import Job


class OutputDriver(ABC):
    def __init__(self, cfg: OutputConfig) -> None:
        self.cfg = cfg

    @abstractmethod
    def write(self, job: Job) -> Path: ...