"""Normalize a text prompt into tokenizer-ready text.

Truncation is by character count approximating CLIP's 77-token window; the
diffusion sampler re-tokenizes downstream so exactness here isn't required.
"""
from __future__ import annotations

import re

from src.pixelgen.handlers.base import IngestHandler
from src.pixelgen.jobs import Job

_WS = re.compile(r"\s+")
_PIXEL_HINTS = "pixel art, 16-bit, sprite, limited palette, crisp edges"


class PromptHandler(IngestHandler):
    def ingest(self, job: Job) -> None:
        raw = job.prompt.strip()
        if not raw:
            raise ValueError("empty prompt")
        cleaned = _WS.sub(" ", raw)
        max_chars = int(self.options.get("max_tokens", 77)) * 4
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars].rsplit(" ", 1)[0]
        augmented = f"{cleaned}, {_PIXEL_HINTS}"
        negative = self.options.get("negative_prompt", "")
        job.artifacts["prompt_clean"] = cleaned
        job.artifacts["prompt_augmented"] = augmented
        job.artifacts["negative_prompt"] = negative