import pickle

def load_model(model_path: str = "model/best_model3.pkl"):
    """
    Charge le modèle depuis un fichier pickle.

    Args:
        model_path (str): Chemin vers le fichier du modèle.

    Returns:
        pipeline: Le modèle chargé.
    """
    with open(model_path, "rb") as f:
        pipeline = pickle.load(f)
    return pipeline