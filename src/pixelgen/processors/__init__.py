"""Processor registry. Each processor takes a ProcessorConfig and a device,
and mutates job.artifacts['image'] in place.
"""
from src.pixelgen.processors.diffusion_sampler import DiffusionSampler
from src.pixelgen.processors.palette_quantizer import PaletteQuantizer
from src.pixelgen.processors.pixel_snap import PixelSnap
from src.pixelgen.processors.outline_pass import OutlinePass

PROCESSORS = {
    "diffusion_sampler": DiffusionSampler,
    "palette_quantizer": PaletteQuantizer,
    "pixel_snap": PixelSnap,
    "outline_pass": OutlinePass,
}

__all__ = ["PROCESSORS"]