# Projet Immo - Prédiction de Prix Immobiliers

Application de prédiction du prix de biens immobiliers basée sur l'apprentissage automatique.

## Description

Ce projet vise à mettre à disposition une application permettant d'estimer le prix d'un bien immobilier en fonction de ses caractéristiques (localisation, surface, nombre de pièces, etc.).

## Fonctionnalités

- Prédiction du prix d'un bien immobilier
- Interface utilisateur pour saisir les caractéristiques du bien
- Modèle d'apprentissage automatique entraîné sur des données réelles
- API REST pour l'intégration dans d'autres applications

## Technologies utilisées

- **Python** : Langage principal
- **Scikit-learn / XGBoost** : Modèles de machine learning
- **FastAPI** : Framework API REST
- **Pandas** : Manipulation des données
- **Docker** : Conteneurisation

## Installation

### Prérequis

- Python 3.10+
- uv

### Étapes

```bash
# Cloner le dépôt
git clone https://github.com/VestiC1/Projet-immo.git
cd Projet-immo


# Installer les dépendances
uv sync

# Activer un environnement virtuel
source venv/bin/activate  # Sur Windows: venv\Scripts\activate


```

## Utilisation

### Entraîner un modèle

```bash
python -m scripts.model_training_mlflow
```

### Lancer l'API

```bash
python -m scripts.run_api
```

L'API sera accessible à l'adresse `http://localhost:8000`

### Documentation de l'API

La documentation interactive est disponible à `http://localhost:8000/docs`

## Déploiement avec Docker

### Construire l'image Docker

```bash
# Construire l'image
docker build -t projet-immo:latest .
```

### Exécuter le conteneur

```bash
# Lancer le conteneur
docker run -d -p 8000:8000 --name immo-api projet-immo:latest
```

### Arrêter et supprimer le conteneur

```bash
# Arrêter le conteneur
docker stop immo-api

# Supprimer le conteneur
docker rm immo-api
```

### 

## Structure du projet

```
Projet-immo/
├── data/               # Données brutes et traitées
├── docs/               # Documentation
├── model/             # Modèles entraînés
├── notebooks/          # Notebooks Jupyter d'exploration
├── src/                # Code source
├── tests/              # Tests unitaires
├── pyproject.toml     # Dépendances Python
└── README.md          # Ce fichier
```

## Données

Le projet utilise les données DVF (Demandes de Valeurs Foncières) fournies par le gouvernement français, qui recensent l'ensemble des ventes immobilières des 5 dernières années.

Source : [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/)