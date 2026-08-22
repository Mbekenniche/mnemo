from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True, kw_only=True)
class Config:
    model: str
    temperature: float
    corpus_dir: Path
    timeout_secondes: float
