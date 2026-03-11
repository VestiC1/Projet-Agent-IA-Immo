import pickle
from pathlib import Path
from typing import Union


def load_pickle(model_path: Union[str, Path]):
    """Load a pickled model from the MODEL_DIR directory."""
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model