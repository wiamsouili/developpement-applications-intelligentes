# ADR 004 : Sélection du modèle MaintAI basé sur le suivi d'expériences MLflow et le versionnement DVC

**Statut :** Accepté  
**Date :** 16/11/2026  
**Décideuse / Auteure :** YEKHLEF Aya  
**Groupe :** G3  
**Projet :** MaintAI  

---

## Contexte et Problématique
Dans le cadre de la démarche MLOps de MaintAI, plusieurs architectures et réglages d'hyperparamètres ont été évalués et tracés de manière reproductible à l'aide de **MLflow**, sur des versions de données étiquetées par **DVC**. 
Le défi industriel impose d'anticiper les défaillances machines critiques sans saturer les équipes terrain. Comme établi depuis le début du projet, une panne non détectée (faux négatif) provoque un arrêt catastrophique de la chaîne de production dont le coût est disproportionnellement plus élevé qu'une visite d'inspection préventive superflue (faux positif). Le modèle retenu doit donc maximiser le **rappel (*recall*)** tout en maintenant une précision opérationnelle acceptable.

## Options étudiées et résultats comparatifs dans MLflow

| Architecture / Option | Run ID MLflow | data_md5 (DVC) | Recall | Précision | Accuracy |
|---|---|---|:---:|:---:|:---:|
| **Régression logistique standard ($C=1.0, \text{seuil}=0.3$)** | `13f5d4e0e5d847118e95ca1b3f2c7f6c` | `73e0b7cb3c6f795c...` (v1) | 0.750 | 0.622 | 0.904 |
| **Régression logistique forte régularisation ($C=0.01, \text{seuil}=0.3$)** | `435762d000dd48419a472311ba0385c9` | `73e0b7cb3c6f795c...` (v1) | 0.691 | 0.653 | 0.908 |
| **Régression logistique seuil sensible ($C=1.0, \text{seuil}=0.2$)** | `41d5da4541464a129650109e2cdba029` | `73e0b7cb3c6f795c...` (v1) | **0.838** | 0.543 | 0.882 |
| **Forêt Aléatoire (*Random Forest*, $\text{seuil}=0.3$)** | `e6b9c7c3f3ef4006aeaaa1a37540e951` | `73e0b7cb3c6f795c...` (v1) | 0.728 | 0.562 | 0.886 |
| **Régression logistique sur jeu étendu ($N=8000$, $\text{seuil}=0.3$)** | `d7d569d95df14233b6a87af266105abc` | `93fdeef2cac1893c...` (v2) | 0.741 | **0.650** | **0.916** |

## Décision retenue
Nous sélectionnons la **Régression Logistique standardisée avec un seuil de décision abaissé à 0,2** (correspondant au Run MLflow `41d5da4541464a129650109e2cdba029` sur les données v1 `data_md5: 73e0b7cb3c6f795c70c3ddf970b99c15`).

* **Pourquoi ce choix :** C'est le seul modèle qui franchit largement la barre des 80 % de détection avec un rappel de **83,8 %**. Il capture 84 pannes réelles sur 100, protégeant activement l'appareil productif contre les arrêts de ligne inopinés.
* **Ce que nous acceptons en échange :** Une baisse de précision à **54,3 %** (contre 62,2 % au seuil de 0,3). Cela se traduit par une proportion accrue de fausses alertes (environ 46 % des alertes nécessitent une levée de doute sans panne avérée), arbitrage pleinement consenti au vu des coûts d'arrêt machine.
* **Pourquoi la Forêt Aléatoire n'est pas retenue :** Malgré sa complexité et un temps d'inférence plus lourd, elle n'atteint qu'un rappel de 72,8 % avec une précision de 56,2 %, se faisant surclasser par la régression logistique linéaire tant sur la sensibilité que sur l'explicabilité des coefficients.

## Traçabilité et Gouvernance MLOps
- **Identifiant du run MLflow :** `41d5da4541464a129650109e2cdba029`
- **Empreinte des données DVC :** `73e0b7cb3c6f795c70c3ddf970b99c15` (version v1 issue du commit Git `970e9f3`).
- **Environnement logiciel certifié :** `scikit-learn==1.8.0`, consigné dans le `requirements.txt` archivé au sein des artefacts du run MLflow, éliminant tout risque d'`InconsistentVersionWarning`.
