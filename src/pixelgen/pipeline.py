"""Pipeline runner — wires ingest handlers, processors, and output driver.

Execution model: single-threaded per Job, but the runner supports N parallel
workers via a ThreadPoolExecutor. Torch releases the GIL during inference so
threads are fine here (we are not CPU-bound on Python bytecode).
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.pixelgen.config import PipelineConfig
from src.pixelgen.jobs import Job, JobResult, JobState
from src.pixelgen.handlers import HANDLERS
from src.pixelgen.processors import PROCESSORS
from src.pixelgen.drivers import DRIVERS

log = logging.getLogger("pixelgen.pipeline")


class Pipeline:
    def __init__(self, cfg: PipelineConfig) -> None:
        self.cfg = cfg
        self._workers = int(cfg.pipeline.get("workers", 2))
        self._pool = ThreadPoolExecutor(max_workers=self._workers, thread_name_prefix="pixelgen")

    @classmethod
    def from_config(cls, cfg: PipelineConfig) -> "Pipeline":
        return cls(cfg)

    def run(self, job: Job) -> JobResult:
        t0 = time.perf_counter()
        try:
            self._ingest(job)
            self._process(job)
            out_path = self._output(job)
            job.transition(JobState.DONE)
        except Exception as exc:  # noqa: BLE001 — surface any processor fault to the job
            log.exception("job %s failed", job.id)
            job.fail(str(exc))
            raise
        return JobResult(
            job_id=job.id,
            output_path=out_path,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
            artifacts=dict(job.artifacts),
        )

    def run_batch(self, jobs: list[Job]) -> list[JobResult]:
        futures = [self._pool.submit(self.run, j) for j in jobs]
        return [f.result() for f in futures]

    def _ingest(self, job: Job) -> None:
        job.transition(JobState.INGESTING)
        for name, handler_cls in HANDLERS.items():
            if not self.cfg.ingest.model_dump().get(name, {}).get("enabled", True):
                continue
            handler = handler_cls(self.cfg.ingest.model_dump().get(name, {}))
            handler.ingest(job)

    def _process(self, job: Job) -> None:
        job.transition(JobState.PROCESSING)
        for pc in self.cfg.processors:
            if not pc.enabled:
                log.info("skip disabled processor %s", pc.id)
                continue
            proc_cls = PROCESSORS.get(pc.id)
            if proc_cls is None:
                raise KeyError(f"unknown processor id: {pc.id}")
            proc = proc_cls(pc, device=self.cfg.device)
            log.info("job=%s processor=%s", job.id, pc.id)
            proc.apply(job)

    def _output(self, job: Job) -> Path:
        job.transition(JobState.OUTPUTTING)
        driver_cls = DRIVERS[self.cfg.output.driver]
        driver = driver_cls(self.cfg.output)
        return driver.write(job)