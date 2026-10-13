"""Ingest handlers. Each handler reads one kind of input and populates
job.artifacts with a normalized payload for downstream processors.
"""
from src.pixelgen.handlers.prompt_handler import PromptHandler
from src.pixelgen.handlers.reference_handler import ReferenceHandler

HANDLERS = {
    "prompt_handler": PromptHandler,
    "reference_handler": ReferenceHandler,
}

__all__ = ["HANDLERS", "PromptHandler", "ReferenceHandler"]