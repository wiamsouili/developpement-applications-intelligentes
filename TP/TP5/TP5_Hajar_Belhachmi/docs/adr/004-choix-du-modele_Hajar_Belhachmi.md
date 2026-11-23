# ADR 004 : Choix et validation du modèle de maintenance prédictive MaintAI (MLflow & DVC)

**Statut :** Accepté  
**Date :** 16/11/2026  
<<<<<<< HEAD
**Heure :** 12:14 
=======
**Heure :** 12:16  
>>>>>>> 29d265c4bf5d89ba807bd44a63b0f154a608b1b1
**Auteure :** Hajar Belhachmi  
**Groupe :** G3  
**Projet :** MaintAI  

---

## 1. Contexte
Pour le système MaintAI, nous avons comparé plusieurs architectures et réglages d'hyperparamètres enregistrés sous MLflow et reliés aux versions de données gérées par DVC.
La contrainte industrielle majeure est de maximiser la détection des pannes d'équipements afin d'éviter les arrêts imprévus d'usine, qui sont beaucoup plus coûteux que de simples vérifications techniques de précaution.

## 2. Résultats des expérimentations relevés dans MLflow

| Modèle & Paramètres | Run ID MLflow | data_md5 DVC | Recall | Precision | Accuracy |
|---|---|---|:---:|:---:|:---:|
| Régression logistique ($C=1.0, \text{seuil}=0.3$) | `13f5d4e0e5d847118e95ca1b3f2c7f6c` | `73e0b7cb...` (v1) | 0.750 | 0.622 | 0.904 |
| Régression logistique ($C=0.01, \text{seuil}=0.3$) | `435762d000dd48419a472311ba0385c9` | `73e0b7cb...` (v1) | 0.691 | 0.653 | 0.908 |
| **Régression logistique ($C=1.0, \text{seuil}=0.2$)** | `41d5da4541464a129650109e2cdba029` | `73e0b7cb...` (v1) | **0.838** | 0.543 | 0.882 |
| Forêt aléatoire ($\text{seuil}=0.3$) | `e6b9c7c3f3ef4006aeaaa1a37540e951` | `73e0b7cb...` (v1) | 0.728 | 0.562 | 0.886 |
| Régression logistique sur v2 ($N=8000$) | `d7d569d95df14233b6a87af266105abc` | `93fdeef2...` (v2) | 0.741 | 0.650 | **0.916** |

## 3. Décision
Nous retenons la **Régression Logistique avec un seuil de décision à 0.2** (Run MLflow `41d5da4541464a129650109e2cdba029`).

- **Raison principale :** C'est le seul modèle qui atteint un rappel élevé de **83,8 %**, assurant la capture d'un maximum d'avaries réelles.
- **Compromis :** La précision s'établit à 54,3 %, ce qui engendre des fausses alertes, mais ce coût reste largement inférieur à celui d'une panne manquée.
- **Forêt aléatoire écartée :** Elle n'obtient que 72,8 % de rappel tout en étant plus complexe et plus lente.

## 4. Traçabilité MLOps
- **Identifiant du run MLflow :** `41d5da4541464a129650109e2cdba029`
- **Empreinte DVC des données :** `73e0b7cb3c6f795c70c3ddf970b99c15` (commit `970e9f3`).
- **Environnement logiciel :** `scikit-learn==1.8.0`, consigné dans le `requirements.txt` archivé par MLflow.

