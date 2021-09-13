from dataclasses import dataclass
from pathlib import Path


@dataclass
class VinaPublicOptions:
    receptor: Path
    center_x: float
    center_y: float
    center_z: float
    size_x: float
    size_y: float
    size_z: float
    flex: str = None
    cpu: int = None
    seed: int = None
    exhaustiveness: int = None
    num_modes: int = None
    energy_range: int = None
    weight_hydrogen: float = None


@dataclass
class VinaOptions:
    public: VinaPublicOptions
    ligand: Path
    out: Path
    log: Path
