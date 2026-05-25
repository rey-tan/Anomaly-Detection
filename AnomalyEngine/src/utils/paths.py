from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]

# Anomaly Engine repo root (directory that contains src/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA = PROJECT_ROOT / "data"
ARTIFACTS = PROJECT_ROOT / "artifacts"
MODEL_ARTIFACTS = ARTIFACTS / "models"
CONFIG = PROJECT_ROOT / "configs"
HYPERPARAMS = ARTIFACTS / "hyperparams"
