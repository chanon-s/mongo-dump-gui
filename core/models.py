from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any

@dataclass
class DumpOptions:
    """Operational parameters for mongodump.
    
    IMPORTANT: Under no circumstance does this class hold Connection URIs,
    passwords, or secrets. URIs exist strictly in memory at runtime.
    """
    db: str = ""
    collection: str = ""
    output_mode: str = "dir"  # "dir" or "archive"
    output_path: str = "./dump"
    gzip: bool = True
    num_parallel_collections: int = 4
    read_preference: str = "primaryPreferred"
    exclude_collections: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DumpOptions":
        valid_keys = {k for k in cls.__dataclass_fields__.keys()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class BinaryInfo:
    """Status information for the mongodump binary."""
    path: str
    is_valid: bool = False
    version: Optional[str] = None
    error: Optional[str] = None
