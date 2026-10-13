"""Config loader. YAML -> pydantic models with validation.

Gotcha: pydantic v2 rejects bare `- id: foo` in a list of dicts unless the
field is declared on the model. We declare every processor field explicitly
so users get a real error instead of a silent skip.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class IngestConfig(BaseModel):
    prompt_handler: dict = Field(default_factory=dict)
    reference_handler: dict = Field(default_factory=dict)


class ProcessorConfig(BaseModel):
    id: str
    enabled: bool = True
    model: str | None = None
    steps: int = 28
    guidance: float = 7.5
    scheduler: str = "dpmpp_2m"
    palette: str | None = None
    dither: Literal["none", "bayer4", "floyd_steinberg"] = "bayer4"
    strength: float = 0.85
    target_res: tuple[int, int] = (32, 32)
    snap_mode: Literal["nearest", "bilinear"] = "nearest"
    color: str = "#1a1410"
    thickness: int = 1


class OutputConfig(BaseModel):
    driver: Literal["single", "sheet", "atlas"] = "sheet"
    sheet_columns: int = 8
    tile_pad: int = 1
    png_optimize: bool = True
    metadata_sidecar: bool = True


class PipelineConfig(BaseModel):
    pipeline: dict = Field(default_factory=dict)
    ingest: IngestConfig = Field(default_factory=IngestConfig)
    processors: list[ProcessorConfig] = Field(default_factory=list)
    output: OutputConfig = Field(default_factory=OutputConfig)
    device: Literal["cuda", "cpu", "mps", "auto"] = "auto"
    seed: int = -1
    log_level: str = "INFO"

    @field_validator("processors")
    @classmethod
    def _unique_ids(cls, v: list[ProcessorConfig]) -> list[ProcessorConfig]:
        seen: set[str] = set()
        for p in v:
            if p.id in seen:
                raise ValueError(f"duplicate processor id: {p.id}")
            seen.add(p.id)
        return v


def load_config(path: Path | str) -> PipelineConfig:
    """Load and validate a pipeline config from YAML."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"config not found: {p}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    return PipelineConfig.model_validate(raw)