from pathlib import Path

# Anomaly Engine repo root (directory that contains src/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA = PROJECT_ROOT / "data"
RAW_DATA = DATA / "raw"
PROCESSED_DATA = DATA / "processed"
ARTIFACTS = PROJECT_ROOT / "artifacts"
MODEL_ARTIFACTS = ARTIFACTS / "models"
CONFIG = PROJECT_ROOT / "configs"
HYPERPARAMS = ARTIFACTS / "hyperparams"
