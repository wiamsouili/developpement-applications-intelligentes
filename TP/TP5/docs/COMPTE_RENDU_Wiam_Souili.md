# Compte rendu · TP5 : Traçabilité des expérimentations avec MLflow et gestion des versions de données avec DVC

**Filière / Module :** Développement et déploiement d'applications d'intelligence artificielle  
**Projet Industriel :** MaintAI — Solution de maintenance prédictive  
**Étudiante :** SOUILI Wiam  
**Groupe :** G3  
**Date :** 16/11/2026  

---

## 1. Introduction et enjeux de la séance

Lors des précédents travaux pratiques, nous avons construit le cœur de l'application MaintAI : l'entraînement initial (TP1), le service d'inférence sécurisé avec FastAPI (TP2), l'interface graphique interactive avec Streamlit (TP3) et la sérialisation des modèles via skops (TP4).
Ce TP5 introduit deux piliers incontournables des opérations d'apprentissage automatique (**MLOps**) :
- **MLflow Tracking :** pour consigner de manière systématique les métriques, hyperparamètres et modèles lors de chaque itération d'entraînement.
- **DVC (Data Version Control) :** pour versionner les données massives de télémétrie capteurs sans encombrer l'historique du dépôt Git.
- **La chaîne de traçabilité complète :** relier de manière univoque chaque run MLflow à la version exacte du jeu de données tracé par DVC.

---

## 2. Phase préliminaire : Configuration et exécution des tests dans `TP/TP5`

### 2.1 Installation et exécution du banc de test initial
Après avoir installé les modules requis (`mlflow==3.18.0` et `dvc==3.67.1`) et configuré le package en mode développement via `pip install -e .` au sein du dossier `TP/TP5`, nous avons exécuté la suite de tests :

```powershell
python -m pytest
```

Sortie obtenue dans la console :
```text
======================= 5 failed, 27 passed, 4 warnings in 62.58s =======================
```

### 2.2 Analyse des tests en échec
Les 5 échecs constatés concernent le module `tests/test_tracking.py` :
- `test_log_run_returns_run_id`
- `test_log_run_logs_params`
- `test_log_run_logs_metrics`
- `test_log_run_logs_model`
- `test_log_run_logs_data_md5`

**Explication :** La fonction `log_run()` dans `maintai/tracking.py` n'était pas encore complétée. En l'absence de l'appel aux primitives de MLflow (`mlflow.set_experiment`, `mlflow.start_run`, `mlflow.log_params`, `mlflow.log_metrics`, etc.), aucune métadonnée ni aucun run_id n'étaient générés.

### 2.3 Rôle de l'installation éditable (`pip install -e .`)
Avant cette commande, l'interpréteur Python exécutait la version de `maintai` enregistrée lors du TP précédent. Après `pip install -e .`, le package actif est explicitement pointé vers `C:\Users\hp\Downloads\TP1_YEKHLEF_Aya\TP\TP5\maintai` (v0.3.0), assurant la prise en charge immédiate du nouveau module de traçabilité.

---

## 3. Sprint 1 : Mise en œuvre du suivi des entraînements avec MLflow

### 3.1 Implémentation de la fonction `log_run`
Nous avons implémenté la journalisation dans `maintai/tracking.py` de la façon suivante :

```python
def log_run(
    run_name: str,
    params: dict[str, Any],
    metrics: dict[str, float],
    model: Pipeline,
    data_path: Path,
) -> str:
    """Enregistre un run complet dans MLflow."""
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

### 3.2 Validation du Sprint 1
La commande `python -m pytest` valide désormais l'intégralité des 32 tests sans aucune défaillance :
```text
======================= 32 passed, 4 warnings in 51.52s =======================
```

### 3.3 Synthèse des runs enregistrés dans MLflow
À l'aide de l'interface `mlflow ui`, nous avons relevé les indicateurs clés pour différentes variantes :

| Configuration du modèle | Run ID MLflow | Rappel (*Recall*) | Précision | Exactitude (*Accuracy*) |
|---|---|:---:|:---:|:---:|
| `python -m maintai.train` (Standard) | `13f5d4e0e5d847118e95ca1b3f2c7f6c` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` (Régularisé) | `435762d000dd48419a472311ba0385c9` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` (Sensible) | `41d5da4541464a129650109e2cdba029` | **0.838** | 0.543 | 0.882 |
| `python -m maintai.train --model forest` (Forêt) | `e6b9c7c3f3ef4006aeaaa1a37540e951` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train` (sur dataset v2) | `d7d569d95df14233b6a87af266105abc` | 0.741 | 0.650 | **0.916** |

### 3.4 Analyse et sélection du modèle
Le modèle optimal pour MaintAI est la **Régression Logistique avec seuil de décision abaissé à 0.2**.
Dans notre domaine (maintenance industrielle critique), une panne non anticipée entraîne l'arrêt complet de la chaîne d'assemblage, provoquant des pertes financières dramatiques. À l'opposé, une fausse alerte ne mobilise qu'une brève intervention de maintenance de niveau 1. Le seuil 0.2 permet d'atteindre un **rappel de 83,8 %**, interceptant le maximum de pannes potentielles, ce qui prime sur la perte de précision (54,3 %).

### 3.5 Gestion de l'environnement d'inférence
Dans les artefacts du modèle, MLflow génère automatiquement un fichier `requirements.txt` contenant :
```text
scikit-learn==1.8.0
skops==0.16.0
```
Cela résout un problème majeur identifié au TP4 : les divergences de versions entre l'environnement d'entraînement et l'environnement de production provoquaient des erreurs de chargement ou des alertes d'incompatibilité (`InconsistentVersionWarning`). MLflow garantit un déploiement déterministe et reproductible.

### 3.6 Stockage local et politique Git
MLflow stocke les données dans le sous-dossier local `mlruns/` et dans la base relationnelle `mlflow.db`. Ces éléments sont exclus de Git via `.gitignore` car les artefacts binaires et les logs volumineux alourdiraient inutilement le référentiel de code sans valeur ajoutée pour le versionnement textuel.

---

## 4. Sprint 2 : Gestion des versions de données avec DVC

### 4.1 Mise en place de la v1
Après initialisation de DVC dans le sous-répertoire du projet (`dvc init --subdir`), l'ajout du fichier de capteurs initial (`dvc add data/sensors.csv`) a généré le pointeur `data/sensors.csv.dvc` :
```yaml
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv
```
La valeur MD5 (`73e0b7cb3c6f795c70c3ddf970b99c15`) est exactement la même que le paramètre `data_md5` enregistré dans MLflow.
Un remote local a été configuré via `dvc remote add --local -d stockage "$env:USERPROFILE\dvc-stockage"` puis synchronisé (`dvc push`).

### 4.2 Passage à la v2 et vérification des états
La génération d'un jeu de données de 8 000 lignes (`python -m maintai.dataset --n 8000 --seed 7`) a entraîné la modification détectée par DVC :
```text
data\sensors.csv.dvc:
	changed outs:
		modified:           data\sensors.csv
```

Après réenregistrement (`dvc add data/sensors.csv`) et commit Git :

| Version | Commit Git | MD5 (8 car.) | Nombre de lignes |
|---|---|---|:---:|
| **v1** | `970e9f3` | `73e0b7cb` | 5 000 |
| **v2** | `cc3c356` | `93fdeef2` | 8 000 |

### 4.3 Validation des retours en arrière et restauration
- **Checkout v1 :** En extrayant l'ancien pointeur (`git checkout 970e9f3 -- data/sensors.csv.dvc`) et en exécutant `dvc checkout`, le fichier `data/sensors.csv` est ramené à très exactement 5 000 lignes.
- **Retour v2 :** En réappliquant le commit HEAD et `dvc checkout`, le fichier repasse fidèlement à 8 000 lignes.
- **Restauration depuis le remote :** La suppression de `data/sensors.csv` et de `.dvc/cache` suivie d'un `dvc pull` télécharge automatiquement les données depuis le remote `%USERPROFILE%\dvc-stockage` sans aucune dépendance envers Git pour les données brutes.

---

## 5. Corrélation entre modèles et données

| Version des données | data_md5 (8 car.) | Échantillons d'entraînement | Rappel | Précision |
|---|---|:---:|:---:|:---:|
| v1 | `73e0b7cb` | 4 000 | 0.750 | 0.622 |
| v2 | `93fdeef2` | 6 400 | 0.741 | 0.650 |

**Analyse comparative :**
On ne peut pas affirmer hâtivement que le modèle v2 surpasse le modèle v1. Même si la précision progresse, le rappel enregistre un léger recul. Plus fondamentalement, les jeux de test sont structurellement différents (1 000 données d'évaluation pour la v1, 1 600 pour la v2). Pour comparer valablement des modèles entraînés sur des données dissemblables, il est indispensable de les confronter à un jeu de test de référence immuable (*golden evaluation dataset*).

---

## 6. Questions de synthèse

1. **Rôles distincts de Git, DVC et MLflow :**
   - **Git :** Contrôle de version du code, de la configuration et de la documentation textuelle.
   - **DVC :** Contrôle de version des volumes de données et des artefacts binaires massifs via des fichiers métadonnées `.dvc`.
   - **MLflow :** Plateforme de traçabilité des expérimentations, des métriques, des hyperparamètres et des registres de modèles.
2. **Utilisation de `--local` pour le remote DVC :**
   - L'argument `--local` isole la configuration dans `.dvc/config.local` pour éviter d'inscrire dans Git des chemins de stockage locaux à la machine hôte. Pour une équipe, un remote cloud commun (S3, GCS) configuré dans `.dvc/config` est requis.
3. **Composants nécessaires à la livraison d'un modèle :**
   - Le code applicatif et de transformation (dépôt Git).
   - L'artefact binaire du modèle (store d'artefacts MLflow).
   - Les spécifications de l'environnement d'exécution (fichiers `requirements.txt` et `conda.yaml` de MLflow).

---

## 7. Décision architecturale et conclusion

La décision MLOps a été rédigée dans l'ADR 004 (`docs/adr/004-choix-du-modele.md`), confirmant le choix du modèle à seuil 0.2 (Run ID `41d5da4541464a129650109e2cdba029`) sur les données v1.
Ce TP démontre la puissance de la synergie entre MLflow et DVC pour assurer une traçabilité rigoureuse, condition sine qua non de toute démarche d'intelligence artificielle industrielle pérenne.
