"""Base ingest handler contract."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.pixelgen.jobs import Job


class IngestHandler(ABC):
    """Reads one input channel and writes a normalized artifact onto the Job.

    Subclasses must not mutate job.prompt / job.reference — those are inputs.
    They write to job.artifacts only.
    """

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self.options = options or {}

    @abstractmethod
    def ingest(self, job: Job) -> None: ...