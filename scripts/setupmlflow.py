"""
Script de configuration et d'initialisation de MLflow pour le tracking des modèles
"""
import mlflow
from pathlib import Path

# Configuration des chemins
MLFLOW_TRACKING_URI = "./mlruns"  # Dossier local pour stocker les runs
EXPERIMENT_NAME = "DVF_Price_Prediction"  # Nom de votre expérience

def setup_mlflow():
    """
    Configure MLflow avec un tracking URI local et crée l'expérience si elle n'existe pas
    """
    # Créer le dossier mlruns s'il n'existe pas
    Path(MLFLOW_TRACKING_URI).mkdir(exist_ok=True)
    
    # Configurer l'URI de tracking (où MLflow stocke les données)
    mlflow.set_tracking_uri(f"file://{Path(MLFLOW_TRACKING_URI).absolute()}")
    
    print(f"✓ MLflow tracking URI configuré : {mlflow.get_tracking_uri()}")
    
    # Créer ou récupérer l'expérience
    try:
        experiment_id = mlflow.create_experiment(
            EXPERIMENT_NAME,
            tags={
                "project": "DVF",
                "model_type": "regression",
                "description": "Prédiction des valeurs foncières"
            }
        )
        print(f"✓ Nouvelle expérience créée : {EXPERIMENT_NAME} (ID: {experiment_id})")
    except Exception as e:
        # L'expérience existe déjà
        experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
        print(f"✓ Expérience existante récupérée : {EXPERIMENT_NAME} (ID: {experiment.experiment_id})")
    
    # Définir l'expérience active
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    return EXPERIMENT_NAME

def get_mlflow_config():
    """
    Retourne la configuration MLflow pour l'utiliser dans d'autres scripts
    """
    return {
        "tracking_uri": MLFLOW_TRACKING_URI,
        "experiment_name": EXPERIMENT_NAME
    }

if __name__ == "__main__":
    print("=== Configuration de MLflow ===\n")
    setup_mlflow()
    print("\n=== Configuration terminée ===")
    print(f"\nPour visualiser l'interface MLflow, lancez :")
    print(f"  mlflow ui --backend-store-uri file://{Path(MLFLOW_TRACKING_URI).absolute()}")
    print(f"\nPuis ouvrez votre navigateur sur : http://127.0.0.1:5000")