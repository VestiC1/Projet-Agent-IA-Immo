# ANALYSE DES SOURCES DE DONNÉES — AGENT IA IMMOBILIER

## 1. Informations générales

| | |
|:---|:---|
| **Titre du projet** | Agent IA Immobilier |
| **Équipe** | Jonathan, Steve, Cyril |
| **Date** | 09-03-2026 |

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

Trois sources alimentent l'agent, toutes ingérées en PostgreSQL et jointes sur le **code INSEE commune**.

### 4.1 Transactions immobilières — DVF+ Cerema

**Besoin** : recherche de ventes similaires filtrées par commune, surface, prix, date, rayon géographique.

**Source retenue** : DVF+ open data du Cerema, et non le brut DGFiP.

Le brut DGFiP présente des problèmes structurels qui rendent l'approche MCP non viable :

| Problème DVF brut | Nature | Impact sur un ETL LLM |
|:---|:---|:---|
| Structure disposition vs mutation | 1 ligne par disposition — une vente multi-lots génère N lignes avec la même `valeur_fonciere` répétée N fois | Doublons de valeur non détectables sans clé de mutation |
| Absence d'identifiant unique | `code_service_ch` et `refdoc` supprimés dans l'open data (décret 2018) [5] | Dédoublonnage impossible de manière déterministe |
| 8 champs manquants | Code SPF, référence document, articles CGI, identifiant local | Qualification des mutations incomplète |
| Volume | Plusieurs centaines de milliers de lignes par département et par an | Chargement intégral du CSV en contexte LLM |
| Statut MCP datagouv | **Expérimental** — explicitement signalé [6] | Déconseillé pour tout usage en production |

DVF+ Cerema résout ces problèmes structurellement : 1 ligne par mutation, identifiants reconstitués, fichiers SQL directement restaurables dans PostgreSQL [7].

| Axe | Métrique | Valeur |
|:---|:---|:---|
| Ingestion initiale | Durée (1-2 départements) | 1-2h (SQL prêt à l'emploi) |
| Refresh | Fréquence officielle | Semestrielle — avril (données N-1) et octobre (données S1 N) |
| Tool `search_transactions` | Paramètres | 5 : commune, surface ±20%, prix, date, rayon géographique |
| | Complexité SQL | ~30 lignes, 1 index spatial |
| | Testabilité | Unitaire, déterministe, reproductible |

**Limites de couverture** :
- Bas-Rhin, Haut-Rhin, Moselle, Mayotte — données dans le Livre Foncier (droit local), non disponibles en open data
- Transactions non géolocalisées si parcelle absente du millésime cadastral — tombent hors scope du filtre rayon (comportement acceptable en MVP)

---

### 4.2 Données démographiques — Communes France

**Besoin** : population, densité, superficie, statut urbain/rural — données absentes de geo.api.gouv.fr.

**Source retenue** : dataset "Communes et villes de France" sur data.gouv.fr [8]. 46 champs par commune incluant population, superficie, densité, coordonnées GPS, code INSEE, et statut dans l'unité urbaine (`H` hors unité urbaine, `C` ville-centre, `B` banlieue, `I` ville isolée). Disponible en CSV, mis à jour annuellement.

Aucune API REST disponible — téléchargement uniquement, ce qui exclut toute approche MCP.

| Axe | Valeur |
|:---|:---|
| Ingestion | Fichier CSV unique — < 30 min |
| Refresh | Annuel |
| Jointure | Code INSEE commune |
| Champs utilisés | `population`, `superficie`, `densite`, `statut_commune_unite_urbain` |

---

### 4.3 Équipements et services — BPE INSEE

**Besoin** : présence d'écoles, commerces, services de santé, transports — contexte indispensable pour qualifier une estimation de prix immobilier.

**Source retenue** : Base Permanente des Équipements (BPE) de l'INSEE [9], mise à jour annuellement. 229 types d'équipements répartis en 7 domaines : services pour les particuliers, commerces, enseignement, santé et action sociale, transports-déplacements, sports-loisirs-culture, tourisme.

La BPE **n'expose pas d'API REST** — disponible uniquement en téléchargement CSV. Une approche MCP via `download_and_parse_resource` chargerait un fichier national de plusieurs millions de lignes en contexte LLM, sans filtrage structuré possible — cas d'application directe du non-déterminisme documenté en section 3.

| Axe | Valeur |
|:---|:---|
| Ingestion | CSV, chargement PostgreSQL avec filtre sur code INSEE |
| Refresh | Annuel |
| Jointure | Code INSEE commune |
| Champs utilisés | Comptage d'équipements par type et par commune (agrégation à l'ingestion) |

---

## 5. Architecture des données résultante

Les trois sources convergent vers une architecture PostgreSQL unifiée, jointe sur le code INSEE :

```
transactions_dvf     ←→  communes_info  ←→  equipements_bpe
(code_insee)              (code_insee)        (code_insee)
DVF+ Cerema               Communes FR          BPE INSEE
refresh semestriel        refresh annuel       refresh annuel
```

Le tool `get_commune_info` agrège à la requête les données des tables `communes_info` et `equipements_bpe` via une jointure SQL sur le code INSEE, sans appel externe au moment de l'exécution.

---

## 6. Conclusion

Les trois décisions d'intégration sont contraintes structurellement :

- **DVF** : absence d'identifiant unique de mutation dans l'open data → ETL LLM non déterministe → PostgreSQL (DVF+ Cerema)
- **Communes** : données démographiques absentes de geo.api.gouv.fr, pas d'API REST → ingestion CSV locale
- **BPE** : pas d'API REST INSEE → ingestion CSV locale

Aucune de ces décisions n'est le résultat d'une préférence arbitraire. L'approche MCP aurait été retenue si les données sources avaient été propres et filtrables via une API structurée — ce n'est le cas pour aucune des trois sources.

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