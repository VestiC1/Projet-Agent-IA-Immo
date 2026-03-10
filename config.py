from pathlib import Path



# Projecty root directory
ROOT = Path(__file__).parent

# Data directory
DATA_DIR = ROOT / "data"
DATA_CLEAN = DATA_DIR / "clean"
dvf_clean=DATA_CLEAN / "dvf.csv"

# Model directory
MODEL_DIR = ROOT / "model"
MODEL_CHARAC = MODEL_DIR / "characterization"

DEPLOYED_MODEL_PATH = MODEL_DIR / "model.onnx"
# DVF file
DVF = DATA_DIR / "valeursfoncieres-2025-s1.txt.zip"

# Token database
TOKENDB = DATA_DIR / "tokendb.json"

API_CONFIG = {
    "host": "localhost",
    "port": 8222
}

