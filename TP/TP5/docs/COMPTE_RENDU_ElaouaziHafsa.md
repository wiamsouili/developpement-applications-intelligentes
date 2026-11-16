# Compte rendu d'ingénierie · TP5 : Suivi d'expériences (MLflow) et versionnement de données (DVC)

**Formation :** Cycle d'Ingénieur — MLOps & Applications Intelligentes  
**Projet :** MaintAI — Système de détection précoce d'anomalies industrielles  
**Étudiante :** ELAOUAZI Hafsa  
**Groupe :** G3  
**Date de réalisation :** 16/11/2026  

---

## 1. Objectifs techniques de la séance

Ce TP5 a pour vocation de structurer le cycle de vie des modèles et des données de la plateforme MaintAI autour des standards de l'ingénierie logicielle appliquée au machine learning (MLOps) :
1. **Instrumenter le code d'entraînement avec MLflow** pour consigner de manière automatisée chaque expérience (paramètres, métriques de performance, signatures, artefacts).
2. **Adopter DVC** pour versionner les fichiers de données massifs (`data/sensors.csv`) en découplant le stockage binaire lourd du versionnement léger sous Git.
3. **Assurer l'auditabilité totale (*Lineage*)** en indexant chaque modèle sauvegardé dans MLflow sur l'empreinte cryptographique MD5 du jeu de données tracé par DVC.

---

## 2. Démarrage et diagnostic du banc de test

### 2.1 Évaluation initiale
Après installation des packages `mlflow==3.18.0` et `dvc==3.67.1` et mise à jour du lien d'installation en mode éditable (`pip install -e .`) dans le répertoire `TP/TP5`, nous avons lancé les tests unitaires et d'intégration :

```powershell
python -m pytest
```

La sortie terminal affichait :
```text
======================= 5 failed, 27 passed, 4 warnings in 62.58s =======================
```

### 2.2 Identification de la source des erreurs
Les 5 échecs provenaient tous de la suite `tests/test_tracking.py` :
- `test_log_run_returns_run_id`
- `test_log_run_logs_params`
- `test_log_run_logs_metrics`
- `test_log_run_logs_model`
- `test_log_run_logs_data_md5`

**Origine :** La fonction `log_run()` dans `maintai/tracking.py` n'était pas encore codée (squelette d'origine renvoyant `""`). En l'absence de session MLflow active, aucun paramètre ni artefact n'était persisté.

### 2.3 Point d'ancrage du package éditable
L'exécution de `pip install -e .` au sein de `TP/TP5` a permis de rediriger le package `maintai` depuis l'arborescence du TP précédent vers l'espace de travail local `C:\Users\hp\Downloads\TP1_YEKHLEF_Aya\TP\TP5\maintai` (v0.3.0), rendant immédiatement opérationnelles les nouvelles fonctionnalités de tracking.

---

## 3. Sprint 1 : Traçabilité des expérimentations avec MLflow

### 3.1 Implémentation du tracking
La fonction `log_run` a été finalisée dans `maintai/tracking.py` afin d'enregistrer de façon atomique l'ensemble des données d'exécution au sein d'un contexte `mlflow.start_run()` :

```python
def log_run(
    run_name: str,
    params: dict[str, Any],
    metrics: dict[str, float],
    model: Pipeline,
    data_path: Path,
) -> str:
    """Enregistre un entraînement complet dans MLflow."""
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            sk_model=model,
            name=MODEL_ARTIFACT_PATH,
            skops_trusted_types=TRUSTED_TYPES,
        )
        return run.info.run_id
```

### 3.2 Validation du banc de test complet
Une fois le code de tracking complété, tous les tests réussissent avec succès :
```text
======================= 32 passed, 4 warnings in 51.52s =======================
```

### 3.3 Synthèse des runs et comparaison des performances
Dans l'interface graphique de MLflow (`mlflow ui`), les résultats suivants ont été constatés :

| Configuration expérimentée | Identifiant Run MLflow | Recall (Rappel) | Précision | Accuracy |
|---|---|:---:|:---:|:---:|
| Entraînement par défaut (`C=1.0, seuil=0.3`) | `13f5d4e0e5d847118e95ca1b3f2c7f6c` | 0.750 | 0.622 | 0.904 |
| Forte régularisation (`--C 0.01`) | `435762d000dd48419a472311ba0385c9` | 0.691 | 0.653 | 0.908 |
| Seuil optimisé sécurité (`--threshold 0.2`) | `41d5da4541464a129650109e2cdba029` | **0.838** | 0.543 | 0.882 |
| Architecture Forêt Aléatoire (`--model forest`) | `e6b9c7c3f3ef4006aeaaa1a37540e951` | 0.728 | 0.562 | 0.886 |
| Entraînement sur données massives (v2, 8000 lignes) | `d7d569d95df14233b6a87af266105abc` | 0.741 | 0.650 | **0.916** |

### 3.4 Choix du modèle pour l'application MaintAI
Nous sélectionnons la **Régression Logistique avec un seuil abaissé à 0.2** (Run ID `41d5da4541464a129650109e2cdba029`).
**Argumentation industrielle :** Dans une chaîne industrielle, le coût d'une fausse alerte (visite d'inspection préventive non suivie de panne) est minime en regard du coût dévastateur d'une panne réelle non interceptée (casse machine, arrêt prolongé de la ligne de fabrication). Le seuil à 0.2 privilégie résolument le **rappel (83,8 %)**, maximisant la détection des anomalies critiques.

### 3.5 Résolution des incompatibilités d'environnement (lien TP4)
L'artefact de modèle stocké par MLflow intègre un fichier `requirements.txt` explicitant formellement :
```text
scikit-learn==1.8.0
skops==0.16.0
```
Cela élimine l'aléa rencontré lors du TP4 relatif aux avertissements `InconsistentVersionWarning` et aux incompatibilités de désérialisation binaire, en garantissant un environnement d'exécution parfaitement conforme.

### 3.6 Persistance des runs MLflow et gestion Git
Les métadonnées et fichiers de runs sont enregistrés dans `TP/TP5/mlruns/` et dans `mlflow.db`. Ces dossiers sont exclus du contrôle de version de code via `.gitignore` pour prévenir toute inflation excessive de la taille du dépôt Git.

---

## 4. Sprint 2 : Versionnement des jeux de données avec DVC

### 4.1 Première version des données (v1)
DVC a été configuré au niveau du sous-répertoire via `dvc init --subdir`. L'indexation du jeu initial (`dvc add data/sensors.csv`) a créé le fichier pointeur `data/sensors.csv.dvc` :
```yaml
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv
```
La clé `md5` (`73e0b7cb3c6f795c70c3ddf970b99c15`) correspond rigoureusement à l'empreinte `data_md5` enregistrée dans les métadonnées de nos runs MLflow.
Un remote de stockage local a été associé (`dvc remote add --local -d stockage "$env:USERPROFILE\dvc-stockage"`), puis les données y ont été sauvegardées (`dvc push`).

### 4.2 Deuxième version des données (v2)
Après génération du jeu de données étendu à 8 000 lignes (`python -m maintai.dataset --n 8000 --seed 7`), l'état a été immédiatement signalé par DVC :
```text
data\sensors.csv.dvc:
	changed outs:
		modified:           data\sensors.csv
```

Récapitulatif des versions versionnées :

| Version | Commit Git associé | MD5 (8 premiers car.) | Lignes | Taille |
|:---:|:---:|:---:|:---:|:---:|
| **v1** | `970e9f3` | `73e0b7cb` | 5 000 | 126 815 o |
| **v2** | `cc3c356` | `93fdeef2` | 8 000 | 202 834 o |

### 4.3 Validation des fonctionnalités de restauration
- **Restauration de la v1 :** La commande `git checkout 970e9f3 -- data/sensors.csv.dvc` couplée à `dvc checkout` reconstitue le jeu de données v1 à très exactement **5 000 lignes**.
- **Retour à la v2 :** En appliquant le pointeur le plus récent via `git checkout HEAD -- data/sensors.csv.dvc` et `dvc checkout`, le fichier repasse à **8 000 lignes**.
- **Résilience et pull distant :** La suppression locale du fichier `data/sensors.csv` et du cache `.dvc/cache` est résolue par la commande `dvc pull`, qui télécharge le fichier manquant depuis le remote sans faire intervenir Git dans le transit des données.

---

## 5. Corrélation entre modèles et données

| Version du jeu de données | data_md5 | Données d'entraînement | Recall | Precision | Accuracy |
|---|---|:---:|:---:|:---:|:---:|
| v1 (5 000 lignes) | `73e0b7cb` | 4 000 | 0.750 | 0.622 | 0.904 |
| v2 (8 000 lignes) | `93fdeef2` | 6 400 | 0.741 | 0.650 | 0.916 |

**Précautions méthodologiques :**
Bien que la précision globale progresse sur la v2, le rappel observe un léger fléchissement. Il est scientifiquement incorrect de qualifier un modèle de "meilleur" en se basant sur des données d'évaluation différentes (1 000 exemples de test sur v1 contre 1 600 sur v2). Une évaluation comparative rigoureuse requiert un banc de test figé et indépendant (*Golden Evaluation Set*).

---

## 6. Questions d'ingénierie et de compréhension

1. **Rôles distinctifs de Git, DVC et MLflow :**
   - **Git :** Contrôle de version du code source, de la configuration et des documents textes.
   - **DVC :** Gestion des volumes massifs de données et d'artefacts binaires via des fichiers métadonnées de pointage.
   - **MLflow :** Traçabilité, comparaison des expériences d'apprentissage automatique et gestion du registre de modèles.
2. **Usage du flag `--local` pour le remote DVC :**
   - Le drapeau `--local` cantonne la configuration au fichier `.dvc/config.local` ignoré par Git, préservant ainsi la portabilité du dépôt face aux chemins absolus de la machine hôte. Pour une équipe, un stockage mutualisé de type S3/GCS configuré dans `.dvc/config` est nécessaire.
3. **Les trois composantes de la livraison d'un modèle :**
   - 1. Le code de pipeline et de prédiction (hébergé dans le dépôt Git).
   - 2. L'artefact sérialisé du modèle (hébergé dans le store d'artefacts MLflow au format skops).
   - 3. L'environnement logiciel certifié (défini par les fichiers `requirements.txt` et `conda.yaml` de MLflow).

---

## 7. Synthèse architecturale

La décision relative au modèle a été formalisée dans l'ADR 004 (`docs/adr/004-choix-du-modele.md`), entérinant le choix de la Régression Logistique avec seuil à 0.2 (Run ID `41d5da4541464a129650109e2cdba029`) sur les données v1 (`data_md5: 73e0b7cb3c6f795c70c3ddf970b99c15`).
Ce TP établit un cadre robuste pour le déploiement fiable et auditable des modèles au sein de l'architecture MaintAI.
