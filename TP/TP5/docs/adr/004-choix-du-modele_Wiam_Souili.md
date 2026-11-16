# ADR 004 : Arbitrage et choix du modèle prédictif MaintAI via MLflow et DVC

**Statut :** Validé  
**Date d'effet :** 16/11/2026  
**Responsable technique :** SOUILI Wiam  
**Équipe :** Groupe G3  
**Projet :** MaintAI  

---

## 1. Contexte opérationnel
Au sein du projet MaintAI, l'industrialisation du cycle de vie des modèles nécessite une décision explicite concernant l'algorithme et le seuil d'alerte en production. Grâce à l'instrumentation MLflow et au versionnement des données sous DVC, chaque hypothèse d'architecture a été entraînée, tracée et comparée sur des versions immuables du jeu de données de capteurs.
Le critère décisionnel prépondérant est la prévention des avaries non détectées (minimisation stricte des faux négatifs).

## 2. Tableau comparatif des expérimentations tracées

| Modèle & Hyperparamètres | Identifiant MLflow | data_md5 DVC | Recall | Précision | Accuracy |
|---|---|---|:---:|:---:|:---:|
| Régression logistique ($C=1.0, \text{seuil}=0.3$) | `13f5d4e0e5d847118e95ca1b3f2c7f6c` | `73e0b7cb...` (v1) | 0.750 | 0.622 | 0.904 |
| Régression logistique ($C=0.01, \text{seuil}=0.3$) | `435762d000dd48419a472311ba0385c9` | `73e0b7cb...` (v1) | 0.691 | 0.653 | 0.908 |
| **Régression logistique ($C=1.0, \text{seuil}=0.2$)** | `41d5da4541464a129650109e2cdba029` | `73e0b7cb...` (v1) | **0.838** | 0.543 | 0.882 |
| Forêt aléatoire ($\text{seuil}=0.3$) | `e6b9c7c3f3ef4006aeaaa1a37540e951` | `73e0b7cb...` (v1) | 0.728 | 0.562 | 0.886 |
| Régression logistique étendu ($N=8000$) | `d7d569d95df14233b6a87af266105abc` | `93fdeef2...` (v2) | 0.741 | 0.650 | **0.916** |

## 3. Décision
Nous retenons la **Régression Logistique avec seuil de décision ajusté à 0.2** (Run MLflow `41d5da4541464a129650109e2cdba029`).

- **Motivation principale :** Ce modèle offre le rappel le plus élevé (**83,8 %**), garantissant la détection de la grande majorité des pannes avant dégradation irréversible de l'outil de production.
- **Compromis consenti :** Une précision de **54,3 %**, acceptée car le traitement des fausses alertes par les équipes de maintenance est économiquement infiniment moins pénalisant qu'un arrêt d'usine imprévu.
- **Écartement de la Forêt Aléatoire :** La complexité accrue n'apporte aucun gain de rappel (72,8 % contre 83,8 %) et induit un coût de calcul superflu à l'inférence.

## 4. Références MLOps
- **Run ID :** `41d5da4541464a129650109e2cdba029`
- **Hash DVC des données :** `73e0b7cb3c6f795c70c3ddf970b99c15` (commit Git `970e9f3`).
- **Dépendances gelées :** `scikit-learn==1.8.0`, archivé dans le dossier d'artefacts du run.
