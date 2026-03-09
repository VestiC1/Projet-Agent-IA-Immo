import optuna
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.datasets import make_regression
from sklearn.metrics import make_scorer, mean_squared_error

# Générer des données d'exemple
X, y = make_regression(n_samples=1000, n_features=20, noise=0.1, random_state=42)

def objective(trial):
    # Définir les hyperparamètres à optimiser
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 10, 200),
        'max_depth': trial.suggest_int('max_depth', 3, 20),
        'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 20),
        'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
        'bootstrap': trial.suggest_categorical('bootstrap', [True, False]),
    }

    # Initialiser le modèle
    model = RandomForestRegressor(**params, random_state=42)

    # Définir la validation croisée (k-fold)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    # Utiliser le score RMSE (Root Mean Squared Error) comme métrique
    scorer = make_scorer(mean_squared_error, greater_is_better=False)

    # Calculer le score moyen sur les folds
    scores = cross_val_score(model, X, y, cv=kf, scoring=scorer)
    rmse = (-scores.mean())**0.5  # Optuna minimise, donc on retourne le RMSE

    return rmse

# Créer une étude Optuna
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=10)

# Afficher les meilleurs paramètres et le meilleur score
print("Meilleurs paramètres trouvés:")
print(study.best_params)
print(f"Meilleur RMSE: {study.best_value:.4f}")

# Entraîner le modèle final avec les meilleurs paramètres
best_model = RandomForestRegressor(**study.best_params, random_state=42)
best_model.fit(X, y)
