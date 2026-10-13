"""Job model — the unit of work that flows through the pipeline.

A Job carries the raw request (prompt, optional reference, output target)
plus a mutable state machine. Processors read from Job.artifacts and write
back to it; the pipeline never mutates a Job's inputs after enqueue.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class JobState(str, Enum):
    QUEUED = "queued"
    INGESTING = "ingesting"
    PROCESSING = "processing"
    OUTPUTTING = "outputting"
    DONE = "done"
    FAILED = "failed"


@dataclass
class JobResult:
    job_id: str
    output_path: Path
    elapsed_ms: int
    artifacts: dict[str, Any] = field(default_factory=dict)


@dataclass
class Job:
    prompt: str
    reference: Path | None = None
    out: Path = Path("outputs/sprite.png")
    seed: int = -1
    batch: int = 1
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    state: JobState = JobState.QUEUED
    artifacts: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: float = field(default_factory=time.time)

    def transition(self, state: JobState) -> None:
        self.state = state

    def fail(self, reason: str) -> None:
        self.state = JobState.FAILED
        self.error = reason