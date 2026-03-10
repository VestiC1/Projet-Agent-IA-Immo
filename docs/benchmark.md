# RAPPORT DE BENCHMARK — AGENT IA IMMOBILIER

## 1. Informations générales

| | |
|:---|:---|
| **Titre du projet** | Agent IA Immobilier |
| **Équipe** | Jonathan, Steve, Cyril |
| **Date** | 09/03/2026 |

---

## 2. Objectif du benchmark

Ce benchmark ne porte pas sur l'ensemble de la stack technique, dont la plupart des choix sont contraints par l'existant (FastAPI, modèle ML) ou trivialement justifiables (Streamlit, PostgreSQL). Il se concentre sur les **deux décisions architecturales réellement incertaines** :

1. **Accès aux données DVF** : serveur MCP datagouv vs ingestion PostgreSQL locale
2. **Framework d'orchestration de l'agent** : LangChain vs Pydantic AI

---

## 3. Choix techniques non benchmarkés

Les décisions suivantes sont justifiées par les contraintes du projet sans nécessiter de comparaison formelle.

| Composant | Choix | Justification |
|:---|:---|:---|
| Modèle ML | Existant (FastAPI) | Déjà entraîné, validé, déployé |
| LLM | GPT-4o-mini | Support français fiable, tool calling stable, coût < 0,20€/1M tokens input, intégration triviale |
| Frontend | Templates Jinja | Intégration native avec FastAPI existant, rendu côté serveur, pas de dépendance supplémentaire |
| Géocodage | api-adresse.data.gouv.fr | API officielle gratuite, sans clé, retourne coordonnées GPS et code INSEE |
| Infos communes | geo.api.gouv.fr | API officielle, stable, couvre toutes les communes françaises |
| LlamaIndex | Écarté du MVP | Pertinent uniquement pour de la recherche sémantique sur texte non structuré. Pourrait être utile si une recherche par nom de rue approximatif est requise (correspondance floue sur les libellés DVF). Non retenu en MVP faute de temps, à réévaluer si ce besoin émerge |

---

## 4. Benchmark 1 — Accès aux données DVF

### 4.1 Contexte

Les données DVF (Demandes de Valeurs Foncières) constituent la source principale pour la fonctionnalité de recherche de transactions similaires. Deux stratégies sont envisageables.

### 4.2 Serveur MCP datagouv

datagouv a publié le 25 février 2026 un serveur MCP expérimental ([lien](https://www.data.gouv.fr/posts/experimentation-autour-dun-serveur-mcp-pour-datagouv), code source : [github.com/datagouv/datagouv-mcp](https://github.com/datagouv/datagouv-mcp)).

Les tools exposés sont :

- `search_datasets` — recherche de jeux de données
- `get_dataset_info` — métadonnées d'un jeu de données
- `query_resource_data` — interrogation directe d'une ressource
- `download_and_parse_resource` — téléchargement et parsing à la volée

| Critère | Évaluation |
|:---|:---|
| Setup | Aucun — connexion directe au serveur MCP |
| Fraîcheur des données | Toujours à jour (source officielle) |
| Flexibilité des requêtes | Incertaine — `query_resource_data` ne garantit pas le filtrage par surface, date, périmètre |
| Nettoyage des données | Problématique — les fichiers CSV DVF bruts contiennent des encodages mixtes, des doublons, des lignes multi-lots et des valeurs manquantes. Le nettoyage se ferait dans le contexte LLM, de manière non déterministe |
| Périmètre maisons uniquement | Non garanti — les données brutes contiennent tous types de locaux, le filtrage dépendrait du LLM |
| Latence | Potentiellement élevée si `download_and_parse_resource` charge un CSV départemental complet |
| Statut | **Expérimental** — explicitement signalé comme tel par datagouv, déconseillé pour des usages fiables |

### 4.3 Ingestion PostgreSQL locale

Les données DVF sont disponibles en téléchargement par département sur data.gouv.fr. Le pipeline consiste à filtrer, nettoyer et charger les transactions dans une table PostgreSQL.

| Critère | Évaluation |
|:---|:---|
| Setup | Ingestion initiale : ~2-4h pour 1-2 départements |
| Fraîcheur des données | Snapshot au moment de l'ingestion (acceptable pour ce projet) |
| Flexibilité des requêtes | Totale — SQL complet, filtrage par commune, surface, date, prix, rayon géographique |
| Nettoyage des données | Réalisé une fois à l'ingestion, de manière déterministe. Pipeline partiellement réutilisable depuis le preprocessing du modèle ML |
| Périmètre maisons uniquement | Garanti — filtre `type_local = 'Maison'` appliqué à l'ingestion |
| Latence | Prévisible et rapide (requête SQL indexée) |
| Statut | Stable, standard, maîtrisé |

### 4.4 Décision retenue

**PostgreSQL est retenu.**

La principale limite du MCP datagouv est structurelle pour ce cas d'usage : les données DVF brutes nécessitent un nettoyage significatif (encodages, doublons, multi-lots, valeurs manquantes) qui ne peut pas être délégué de manière fiable au LLM. Par ailleurs, le périmètre maisons uniquement — imposé par le modèle ML — doit être garanti, ce qu'une approche MCP ne permet pas de façon déterministe.

L'ingestion PostgreSQL représente un coût initial maîtrisé, et une partie du pipeline de nettoyage est réutilisable depuis le preprocessing du modèle. La requête SQL est ensuite stable, rapide et testable unitairement.

Le serveur MCP datagouv reste une option intéressante pour des usages exploratoires (découverte de datasets, questions ad hoc sur des données ouvertes), mais pas pour des tools d'agent à comportement déterministe.

---

## 5. Benchmark 2 — Framework d'orchestration de l'agent

### 5.1 Contexte

L'agent doit orchestrer 4 tools, maintenir un historique de conversation et s'intégrer avec PostgreSQL et des APIs REST. Le critère discriminant est l'ergonomie d'intégration des tools, notamment dans un contexte de développement rapide (une semaine).

### 5.2 LangChain

| Critère | Évaluation |
|:---|:---|
| Maturité | Très mature — framework dominant depuis 2023 |
| Définition de tools | Décorateur `@tool` ou classe `BaseTool`, standard et bien documenté |
| Support MCP | Package `langchain-mcp-adapters` — convertit automatiquement les tools MCP en tools LangChain |
| Mémoire de session | `ConversationBufferMemory` ou `ChatMessageHistory`, intégré nativement |
| Intégration LLM | Compatible OpenAI, Anthropic, Mistral, HuggingFace et autres |
| Débogage | Verbose mais lisible avec `verbose=True` ; LangSmith pour le tracing |
| Complexité | Abstractions parfois opaques, mais gérables à 4 tools |
| Documentation française | Quelques ressources, documentation principale en anglais |
| Communauté | Très active, nombreux exemples immobilier / RAG / agents |

### 5.3 Pydantic AI

| Critère | Évaluation |
|:---|:---|
| Maturité | Récent (2024-2025), en croissance rapide |
| Définition de tools | Typage strict via Pydantic, validation automatique des inputs/outputs |
| Support MCP | Client MCP intégré nativement |
| Mémoire de session | Manuelle — à implémenter explicitement |
| Intégration LLM | OpenAI, Anthropic, Gemini, Groq |
| Débogage | Plus lisible que LangChain, moins de magie implicite |
| Complexité | Plus léger, mais moins d'exemples disponibles pour les cas avancés |
| Documentation française | Quasi inexistante |
| Communauté | Active mais plus petite |

### 5.4 Décision retenue

**LangChain est retenu.**

À 4 tools et une semaine de développement, LangChain offre le meilleur rapport entre disponibilité des exemples, support de la mémoire de session et intégration LLM. La validation des inputs des tools sera assurée par des schémas Pydantic définis manuellement, ce qui mitigue le principal avantage de Pydantic AI dans ce contexte.

Pydantic AI est une alternative sérieuse pour des projets plus longs ou des équipes souhaitant éviter les abstractions de LangChain, mais son écosystème reste moins mature pour un usage en production rapide.

---

## 6. Récapitulatif des choix

| Domaine | Technologie retenue | Benchmark réalisé |
|:---|:---|:---|
| Orchestration agent | LangChain | Oui — vs Pydantic AI |
| LLM | GPT-4o-mini | Non — justifié par contraintes |
| Accès données DVF | PostgreSQL (ingestion locale) | Oui — vs MCP datagouv |
| Backend prédiction | FastAPI (existant) | Non — existant |
| Frontend | Templates Jinja | Non — justifié par contraintes |
| Géocodage | api-adresse.data.gouv.fr | Non — seule API officielle française |
| Infos communes | geo.api.gouv.fr | Non — seule API officielle française |

---

## 7. Annexes

- Annonce serveur MCP datagouv : https://www.data.gouv.fr/posts/experimentation-autour-dun-serveur-mcp-pour-datagouv
- Code source MCP datagouv : https://github.com/datagouv/datagouv-mcp
- DVF sur data.gouv.fr : https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/
- Documentation LangChain tools : https://python.langchain.com/docs/concepts/tools/
- Documentation Pydantic AI : https://ai.pydantic.dev/
- API adresse : https://adresse.data.gouv.fr/api-doc/adresse
- API géo : https://geo.api.gouv.fr/decoupage-administratif/communes
