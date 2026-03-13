# ANALYSE DES SOURCES DE DONNÉES — AGENT IA IMMOBILIER

## 1. Informations générales

| | |
|:---|:---|
| **Titre du projet** | Agent IA Immobilier |
| **Équipe** | Jonathan, Steve, Cyril |
| **Date** | 09/03/2026 |

---

## 2. Objectif du document

Ce document analyse les sources de données nécessaires à l'agent et justifie les décisions d'intégration. Il ne constitue pas un benchmark au sens strict — les comparaisons menées montrent que les décisions sont contraintes structurellement, et non le résultat d'un choix arbitraire entre options équivalentes.

Les choix techniques de stack (LLM, framework d'orchestration, frontend) sont documentés dans la note de cadrage.

---

## 3. Principe : pourquoi l'ETL via LLM est non déterministe

Avant d'analyser chaque source, il convient de poser le cadre théorique qui sous-tend toutes les décisions de ce document.

Une approche MCP délègue au LLM le traitement des données brutes à chaque appel : filtrage, dédoublonnage, normalisation. Cette approche est structurellement non déterministe pour deux raisons indépendantes et cumulatives.

**Non-déterminisme intrinsèque des LLM**

Les LLM sont des systèmes probabilistes : même à température zéro, les APIs commerciales ne garantissent pas un output identique pour un input identique, en raison de la non-associativité des opérations flottantes sur GPU et de l'exécution concurrente des kernels CUDA [1]. Les erreurs se cumulent dans les pipelines agentiques : *"if you're using reasoning models and AI agents, then those errors can compound when earlier mistakes are used in later steps"* [2].

Pour des tâches structurées à précision requise — filtrage, dédoublonnage, validation d'intégrité — la littérature est unanime : *"for financial transactions, scientific calculations, or any process where 100% accuracy and reproducibility are non-negotiable, the probabilistic nature of LLMs is a liability"* [3]. Les taux d'erreur mesurés sur des tâches d'extraction structurée atteignent 5 à 20 % sur GPT-4o et modèles équivalents [4].

**Non-déterminisme des données sources**

Indépendamment du LLM, les données DVF et BPE brutes présentent des ambiguïtés structurelles documentées — absence d'identifiant unique, doublons par disposition, champs manquants — qui ne peuvent pas être résolues de manière déterministe sans la clé de mutation, absente des fichiers open data depuis le décret 2018 [5]. Un LLM confronté à ces ambiguïtés produit des résolutions différentes selon le contexte — ce qui est précisément son comportement attendu, mais incompatible avec un tool d'agent dont la sortie doit être testable et reproductible.

La conclusion pratique formulée par RisingWave Engineering : *"use traditional ETL/ELT tools for initial data ingestion and pre-processing. Dispatch only the relevant data"* [3]. C'est exactement l'architecture retenue : ETL à l'ingestion, LLM uniquement pour l'orchestration conversationnelle.

---

## 4. Sources de données retenues

Trois sources alimentent l'agent, jointes sur le **code INSEE commune**. L'approche est API-first : seule la BPE nécessite un stockage local (DuckDB), faute d'API REST disponible.

### 4.1 Transactions immobilières — API DVF+ Cerema

**Besoin** : recherche de ventes similaires filtrées par commune, surface, prix, type de bien, date.

**Source retenue** : API DVF+ open data du Cerema (`apidf-preprod.cerema.fr`), accès libre sans authentification.

L'approche retenue est **API-only** — aucune ingestion locale, aucun stockage pour les transactions. Le tool `search_transactions` interroge directement l'API à chaque requête utilisateur, avec les paramètres filtrés.

**Stratégie de récupération — pagination parallèle asynchrone**

L'API pagine les résultats avec `page_size` maximal de 100. Pour une commune comme Tours (~900 transactions sur 2 ans), cela représente ~9 pages. La stratégie retenue :

1. Premier appel synchrone sur `page=1` pour récupérer `count` et les premières features
2. Calcul du nombre total de pages (`math.ceil(count / page_size)`)
3. Récupération concurrente des pages restantes via `asyncio.gather` avec un `asyncio.Semaphore(5)` pour limiter la pression sur l'API Cerema

**Cache disque — `diskcache`**

Ce qui est mis en cache est la **réponse brute de l'API** (liste des features GeoJSON), pas les transactions filtrées. La clé de cache est `cerema:{code_insee}:{type_bien}:{annee_min}:{annee_max}`. Le TTL est fixé à **30 jours** : les données DVF sont historiques et immuables — une mutation enregistrée ne change jamais. Le rafraîchissement semestriel de l'API (avril/octobre) est géré naturellement par l'expiration du cache. En production Docker, le cache est monté sur un volume nommé pour persister entre les redémarrages.

**Paramètres de filtrage disponibles sur l'endpoint `/dvf_opendata/geomutations/`** :

| Paramètre | Description |
|:---|:---|
| `code_insee` | Code INSEE communal — jusqu'à 10 communes séparées par virgule, même département |
| `codtypbien` | Type de bien — `11` maisons, `12` appartements (filtre par préfixe) |
| `anneemut_min` / `anneemut_max` | Filtre temporel par année |
| `valeurfonc_min` / `valeurfonc_max` | Fourchette de prix en euros |
| `sbati_min` / `sbati_max` | Surface bâtie en m² |
| `idnatmut` | Nature de mutation — `1` = vente |
| `page_size` | Pagination |

**Réponse** : GeoJSON avec géométrie de la parcelle cadastrale (polygone). Les coordonnées lat/lng sont obtenues en calculant le centroïde du polygone côté Python (`shapely`). Les adresses ne sont pas disponibles dans le tier open data — masquées depuis le décret 2018.

**Limites de couverture** :
- Bas-Rhin, Haut-Rhin, Moselle, Mayotte — données dans le Livre Foncier (droit local), non disponibles
- Parcelles absentes du cadastre vectoriel — géométrie null, centroïde non calculable, transaction ignorée

| Axe | Valeur |
|:---|:---|
| Authentification | Aucune |
| Latence premier appel | ~1-2s pour une commune moyenne (pagination parallèle) |
| Latence appel suivant | < 1ms (cache disque, TTL 30 jours) |
| Disponibilité | Beta — risque 502 documenté, géré par retry avec backoff |
| Refresh données | Semestriel (avril / octobre) côté Cerema, transparent pour l'agent |

---

### 4.2 Données démographiques — geo.api.gouv.fr

**Besoin** : population, superficie, densité, statut urbain/rural, coordonnées.

**Source retenue** : `geo.api.gouv.fr`, API REST officielle, accès libre, sans authentification, 50 appels/seconde.

Les champs disponibles via le paramètre `fields` couvrent l'ensemble des besoins : `nom`, `code`, `population`, `surface`, `centre`, `contour`, `departement`, `region`, `epci`. Le tool `get_commune_info` interroge cette API directement à chaque requête — aucun stockage local nécessaire.

| Axe | Valeur |
|:---|:---|
| Authentification | Aucune |
| Champs utilisés | `population`, `surface`, `centre`, `departement` |
| Arrondissements Paris/Lyon/Marseille | Gérés nativement par l'API via les codes INSEE d'arrondissement |

---

### 4.3 Équipements et services — BPE INSEE (dénombrement)

**Besoin** : présence et quantité d'écoles, commerces, services de santé, transports — contexte indispensable pour qualifier une estimation de prix immobilier.

**Source retenue** : fichier de **dénombrement par commune** de la Base Permanente des Équipements (BPE) INSEE [9], mis à jour annuellement. Ce fichier donne les comptages d'équipements par type pour chaque commune (une ligne = une commune) — il ne contient pas les adresses individuelles des équipements, ce qui est suffisant pour le `get_commune_info` tool.

La BPE **n'expose pas d'API REST**. Deux fichiers sont disponibles :
- **Fichier géolocalisé `Ensemble_xy`** — une ligne par équipement individuel, plusieurs millions de lignes France entière, nécessite nettoyage et agrégation → écarté
- **Fichier dénombrement par commune** — déjà agrégé par l'INSEE, ~35 000 lignes, propre, ingestion triviale → **retenu**

| Axe | Valeur |
|:---|:---|
| Ingestion | CSV unique — < 15 min, aucun nettoyage nécessaire |
| Stockage | DuckDB — fichier embarqué, pas de serveur, requêtes SQL standard |
| Volume | ~35 000 lignes (une par commune) |
| Refresh | Annuel |
| Jointure | Code INSEE commune — cohérent avec DVF+ et geo.api.gouv.fr, arrondissements Paris/Lyon/Marseille gérés nativement |
| Champs utilisés | Comptages par domaine : enseignement, santé, commerces, transports, sports-loisirs, services |

---

## 5. Architecture des données résultante

L'approche est **API-first** : seule la BPE nécessite un stockage local, faute d'API REST disponible. Les transactions DVF et les données communes sont interrogées à la volée.

```
search_transactions    →  API DVF+ Cerema          (accès libre, filtres natifs, pagination parallèle async, cache disque 30j)
get_commune_info       →  geo.api.gouv.fr           (accès libre)
                       +  DuckDB bpe_denombrement   (CSV INSEE, ~35k lignes)
geocode_address        →  api-adresse.data.gouv.fr  (accès libre)
estimate_price         →  FastAPI interne
```

Le tool `get_commune_info` combine les deux sources à l'exécution : appel `geo.api.gouv.fr` pour les données administratives, requête SQL sur `bpe_denombrement` pour les équipements.

---

## 6. Conclusion

L'architecture résultante est API-first avec un minimum de stockage local :

- **DVF** : API Cerema DVF+ open data — filtrage natif, accès libre, pagination parallèle async (`asyncio.gather` + `Semaphore(5)`), cache disque 30 jours → pas d'ingestion
- **Communes** : geo.api.gouv.fr — API REST officielle, couvre tous les besoins administratifs → pas de stockage local
- **BPE** : pas d'API REST INSEE → seul cas nécessitant un stockage local, limité au fichier dénombrement (~35k lignes, propre, ingestion < 15 min) dans **DuckDB** (fichier embarqué, zéro infrastructure)

La règle formulée en section 3 reste valide pour la BPE : sans API structurée, l'ingestion locale est préférable à un ETL LLM sur un CSV national de plusieurs millions de lignes.

---

## 7. Références

[1] Thinking Machines Lab — *Defeating Nondeterminism in LLM Inference* : https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/

[2] Stack Overflow Engineering — *Reliability for unreliable LLMs* : https://stackoverflow.blog/2025/06/30/reliability-for-unreliable-llms/

[3] RisingWave Engineering — *From Hype to Hybrid: A Pragmatic Guide to Integrating LLMs into Your Data Pipelines* : https://risingwave.com/blog/pragmatic-guide-llms-in-etl/

[4] Parseur — *The Capabilities and Limitations of Large Language Models in Document Automation* : https://parseur.com/blog/llms-document-automation-capabilities-limitations

[5] GnDVF — *Précautions techniques et qualité des données DVF* : http://www.groupe-dvf.fr/vademecum-fiche-n3-precautions-techniques-et-qualite-des-donnees-dvf/

[6] Annonce MCP datagouv : https://www.data.gouv.fr/posts/experimentation-autour-dun-serveur-mcp-pour-datagouv

[7] DVF+ open data Cerema : https://datafoncier.cerema.fr/donnees/autres-donnees-foncieres/dvfplus-open-data

[8] Communes France — data.gouv.fr : https://www.data.gouv.fr/datasets/communes-et-villes-de-france-en-csv-excel-json-parquet-et-feather

[9] BPE INSEE — data.gouv.fr : https://www.data.gouv.fr/datasets/base-permanente-des-equipements-1