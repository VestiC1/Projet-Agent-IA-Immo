from config import dvf_clean, MODEL_DIR, MODEL_CHARAC
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, root_mean_squared_error, mean_absolute_error
from pickle import dump, load
from datetime import datetime
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from scripts.setupmlflow import setup_mlflow, get_mlflow_config
import optuna
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.datasets import make_regression
from sklearn.metrics import make_scorer, mean_squared_error
from xgboost import XGBRegressor

def load_df(data_path):
    return pd.read_csv(data_path, low_memory=False)

def generate_Xy(df: pd.DataFrame):
    y = df['Valeur fonciere']
    X = df.drop(columns=['Valeur fonciere', 'Code departement'])
    return X, y

def generate_train_test(X, y, test_size, random_state):
    return train_test_split(X, y, test_size=test_size, random_state=random_state)

def export_pipeline(pipe, pipe_path):
    with open(pipe_path, "wb") as f:
        dump(pipe, f)

def load_pipeline(pipe_path):
    with open(pipe_path, "rb") as f:
        return load(f)

def model_path(dir, name, ext):
    now = datetime.now().strftime("%Y%m%d-%Hh%Mm%S")
    return dir / f'{now}_{name}.{ext}'

def objective(trial, X, y):
    # Définir les hyperparamètres à optimiser
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 80, 200),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.7, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 1.0),
        'gamma': trial.suggest_float('gamma', 0, 5),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
    }

    # Initialiser le modèle
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('xg', XGBRegressor(**params, objective='reg:squarederror', random_state=42))
    ])

    # Définir la validation croisée (k-fold)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    # Utiliser le score RMSE (Root Mean Squared Error) comme métrique
    scorer = make_scorer(mean_squared_error, greater_is_better=False)

    # Calculer le score moyen sur les folds
    scores = cross_val_score(pipe, X, y, cv=kf, scoring=scorer)
    rmse = (-scores.mean())**0.5  # Optuna minimise, donc on retourne le RMSE
    print(X.shape, params)
    return rmse

def main():
    # === ÉTAPE 1 : Configuration de MLflow ===
    print("=== Configuration de MLflow ===")
    setup_mlflow()
    
    # === ÉTAPE 2 : Chargement et préparation des données ===
    print("\n=== Chargement des données ===")
    df = load_df(dvf_clean)
    X, y = generate_Xy(df)
    X_train, X_test, y_train, y_test = generate_train_test(X, y, test_size=0.3, random_state=8)
    
    print(f"Taille du jeu d'entraînement : {len(X_train)}")
    print(f"Taille du jeu de test : {len(X_test)}")
    
    # === ÉTAPE 3 : Définition des hyperparamètres ===
    params = {
        "max_depth": 6,
        "random_state": 0,
        "n_estimators": 100,  # Valeur par défaut de RandomForest
    }
    
    # Paramètres du split
    split_params = {
        "test_size": 0.3,
        "random_states": 8
    }
    
    # === ÉTAPE 4 : Démarrage du run MLflow ===
    print("\n=== Démarrage de l'entraînement avec MLflow ===")
    
    with mlflow.start_run(run_name=f"xgboost_{datetime.now().strftime('%Y%m%d_%H%M%S')}") as run:
        
        # Log des tags pour identifier le run
        mlflow.set_tags({
            "model_type": "xgboost",
            "pipeline": "StandardScaler + xgboost",
            "data_source": "DVF",
            "author": "Votre nom"
        })
        
        # Log des paramètres du modèle
        mlflow.log_params(params)
        mlflow.log_params(split_params)
        
        # Log des informations sur les données
        mlflow.log_param("n_features", X_train.shape[1])
        mlflow.log_param("n_samples_train", len(X_train))
        mlflow.log_param("n_samples_test", len(X_test))
        
        # === ÉTAPE 5 : Création et entraînement du pipeline (avec Optuna) ===
        
        pipe_path = model_path(MODEL_DIR, 'xg', 'pkl')

        # Créer une étude Optuna
        study = optuna.create_study(direction='minimize')
        study.optimize(lambda x:objective(x, X_train, y_train), n_trials=20, show_progress_bar=True)

        # Afficher les meilleurs paramètres et le meilleur score
        print("Meilleurs paramètres trouvés:")
        print(study.best_params)
        print(f"Meilleur RMSE: {study.best_value:.4f}")

        pipe = Pipeline([
            ('scaler', StandardScaler()),
            ('xg', XGBRegressor(**study.best_params, objective='reg:squarederror', random_state=42))
        ])

        # Entraîner le modèle final avec les meilleurs paramètres
        pipe.fit(X_train, y_train)

        '''
        try:
            print("Entraînement du modèle...")
            pipe.fit(X_train, y_train)
            print("Entraînement terminé.")
        except Exception as e:
            print(f"Erreur lors de l'entraînement : {e}")
            mlflow.log_param("training_status", "failed")
            raise
        '''
        
        # === ÉTAPE 6 : Sauvegarde locale du pipeline (comme avant) ===
        export_pipeline(pipe, pipe_path)
        mlflow.log_param("local_model_path", str(pipe_path))
        
        # === ÉTAPE 7 : Prédictions et calcul des métriques ===
        print("\n=== Évaluation du modèle ===")
        y_train_pred = pipe.predict(X_train)
        y_test_pred = pipe.predict(X_test)
        
        # Calcul des métriques
        r2_train = r2_score(y_train, y_train_pred)
        r2_test = r2_score(y_test, y_test_pred)
        
        rmse_train = root_mean_squared_error(y_train, y_train_pred)
        rmse_test = root_mean_squared_error(y_test, y_test_pred)
        
        mae_train = mean_absolute_error(y_train, y_train_pred)
        mae_test = mean_absolute_error(y_test, y_test_pred)
        
        # Affichage des résultats
        print(f'R² train = {r2_train:.4f}')
        print(f'R² test = {r2_test:.4f}')
        print(f'RMSE train = {rmse_train:.2f}')
        print(f'RMSE test = {rmse_test:.2f}')
        print(f'MAE train = {mae_train:.2f}')
        print(f'MAE test = {mae_test:.2f}')
        
        # === ÉTAPE 8 : Log des métriques dans MLflow ===
        mlflow.log_metric("r2_train", r2_train)
        mlflow.log_metric("r2_test", r2_test)
        mlflow.log_metric("rmse_train", rmse_train)
        mlflow.log_metric("rmse_test", rmse_test)
        mlflow.log_metric("mae_train", mae_train)
        mlflow.log_metric("mae_test", mae_test)
        
        # Calcul de l'overfitting (différence entre train et test)
        overfit_r2 = r2_train - r2_test
        mlflow.log_metric("overfit_r2", overfit_r2)
        
        # === ÉTAPE 9 : Inférence de la signature du modèle ===
        # La signature définit le schéma d'entrée/sortie du modèle
        signature = infer_signature(X_train, y_train_pred)
        
        # === ÉTAPE 10 : Log du modèle dans MLflow ===
        model_info = mlflow.sklearn.log_model(
            sk_model=pipe,
            artifact_path="model",  # Chemin dans le run MLflow
            signature=signature,
            input_example=X_train.iloc[:5],  # Exemple d'entrée pour la documentation
            registered_model_name="DVF_xgboost_Production",  # Nom dans le model registry
            metadata={
                "features": list(X_train.columns),
                "target": "Valeur fonciere"
            }
        )
        
        # === ÉTAPE 11 : Log d'artefacts supplémentaires ===
        # Sauvegarde de la liste des features
        feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': pipe.named_steps['xg'].feature_importances_
        }).sort_values('importance', ascending=False)
        
        feature_importance_path = model_path(MODEL_CHARAC, "feature_importance", "csv")
        feature_importance.to_csv(feature_importance_path, index=False)
        mlflow.log_artifact(feature_importance_path, artifact_path="analysis")
        
        print(f"\n=== Run MLflow terminé ===")
        print(f"Run ID : {run.info.run_id}")
        print(f"Model URI : {model_info.model_uri}")
        print(f"\nConsultez les résultats sur l'interface MLflow UI")

if __name__ == "__main__":
    main()