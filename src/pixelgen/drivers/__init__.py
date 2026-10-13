"""Output drivers. Each driver takes an OutputConfig and writes job.artifacts
to disk in a specific layout.
"""
from src.pixelgen.drivers.single_driver import SingleDriver
from src.pixelgen.drivers.sheet_driver import SheetDriver
from src.pixelgen.drivers.atlas_driver import AtlasDriver

DRIVERS = {
    "single": SingleDriver,
    "sheet": SheetDriver,
    "atlas": AtlasDriver,
}

__all__ = ["DRIVERS"]