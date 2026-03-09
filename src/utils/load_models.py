import pickle
from config import MODEL_DIR
from pathlib import Path
from typing import Union


def load_pickle(model_name: Union[str, Path]):
    """Load a pickled model from the MODEL_DIR directory."""
    with open(MODEL_DIR / model_name, 'rb') as f:
        model = pickle.load(f)
    return model