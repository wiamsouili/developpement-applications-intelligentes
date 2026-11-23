# Compte rendu · TP5 : Suivi des expérimentations MLflow et versionnement des jeux de données avec DVC

**Module :** Développement et déploiement d'applications intelligentes (MLOps)  
**Projet :** MaintAI — Plateforme industrielle de maintenance prédictive  
**Étudiante :** YEKHLEF Aya  
**Groupe :** G3  
**Date :** 16/11/2026  

---

## 1. Contexte et objectifs de la séance

Dans les séances précédentes (TP1 à TP4), nous avons successivement développé le package `maintai`, mis en place l'API FastAPI, conçu le tableau de bord Streamlit et exploré les problématiques de sérialisation sécurisée (`skops` vs `pickle`).
Ce TP5 aborde le cœur des pratiques **MLOps** modernes :
1. **Le tracking d'expériences avec MLflow :** Enregistrer de manière systématique, auditable et reproductible l'ensemble des hyperparamètres, des métriques d'évaluation (rappel, précision, exactitude) et des artefacts de modèles générés.
2. **Le versionnement des données avec DVC (*Data Version Control*) :** Résoudre l'incompatibilité fondamentale entre Git et les volumes de données volumineux, en gérant le stockage physique des jeux de données dans un *remote* externe tout en consignant des pointeurs légers (`.dvc`) dans Git.
3. **L'établissement du lien de provenance de bout en bout (*Data & Model Lineage*) :** Lier chaque exécution MLflow à l'empreinte cryptographique MD5 de la version de données sous-jacente.

---

## 2. Mise en place dans `TP/TP5`

### 2.1 Diagnostic initial des tests
Après installation des dépendances spécifiques (`mlflow==3.18.0`, `dvc==3.67.1`) et passage en mode éditable via `pip install -e .` depuis le sous-répertoire `TP/TP5`, l'exécution du banc de test automatisé a révélé 5 échecs :

```powershell
python -m pytest
```

Sortie obtenue :
```text
======================= 5 failed, 27 passed, 4 warnings in 62.58s =======================
```

### 2.2 Analyse des défaillances
Les 5 échecs concernaient tous le fichier `tests/test_tracking.py` :
- `test_log_run_returns_run_id`
- `test_log_run_logs_params`
- `test_log_run_logs_metrics`
- `test_log_run_logs_model`
- `test_log_run_logs_data_md5`

**Cause racine :** La fonction `log_run()` dans `maintai/tracking.py` était un squelette vierge ne réalisant aucun appel à l'API MLflow et renvoyant une chaîne vide. L'absence de création de run et d'enregistrement des métadonnées bloquait les assertions de conformité MLOps.

### 2.3 Gestion du package éditable
Avant l'exécution de `pip install -e .`, l'interpréteur Python utilisait le package `maintai` résolu dans le dossier d'un TP précédent (TP4/TP1). Après l'installation éditable dans `TP/TP5`, le chemin est réassigné à `C:\Users\hp\Downloads\TP1_YEKHLEF_Aya\TP\TP5\maintai` (version 0.3.0), activant la prise en compte immédiate des modifications de tracking.

---

## 3. Sprint 1 : Suivi des expérimentations avec MLflow

### 3.1 Implémentation de `log_run`
Nous avons complété `maintai/tracking.py` en exploitant le contexte `mlflow.start_run()` pour journaliser les paramètres, le hachage MD5 du jeu de données, les métriques scalaires et la sérialisation du modèle :

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

### 3.2 Validation complète du banc de tests
Après implémentation, la suite complète de 32 tests est validée :
```text
======================= 32 passed, 4 warnings in 51.52s =======================
```

### 3.3 Résultats des entraînements tracés dans MLflow
Cinq entraînements ont été conduits avec des configurations variées :

| Run | Commande / Configuration | Run ID MLflow | Recall | Precision | Accuracy |
|:---:|---|---|:---:|:---:|:---:|
| 1 | Baseline (`LogisticRegression`, $C=1.0$, seuil=0.3) | `13f5d4e0e5d847118e95ca1b3f2c7f6c` | 0.750 | 0.622 | 0.904 |
| 2 | Régularisation forte ($C=0.01$) | `435762d000dd48419a472311ba0385c9` | 0.691 | 0.653 | 0.908 |
| 3 | Seuil de sensibilité abaissé (`--threshold 0.2`) | `41d5da4541464a129650109e2cdba029` | **0.838** | 0.543 | 0.882 |
| 4 | Forêt Aléatoire (`--model forest`) | `e6b9c7c3f3ef4006aeaaa1a37540e951` | 0.728 | 0.562 | 0.886 |
| 5 | Données étendues v2 ($N=8000$, seuil=0.3) | `d7d569d95df14233b6a87af266105abc` | 0.741 | 0.650 | **0.916** |

### 3.4 Sélection opérationnelle pour MaintAI
Pour la plateforme industrielle MaintAI, le modèle retenu est le **Run 3 (`--threshold 0.2`)** :
- **Arbitrage industriel :** Une avarie machine non anticipée (faux négatif) provoque un arrêt brutal de production, des pannes en cascade et des coûts financiers colossaux. En contrepartie, une fausse alerte (faux positif) ne nécessite qu'un contrôle de routine peu coûteux.
- **Performance :** Ce run est le seul à dépasser 80 % de détection avec un **rappel exceptionnel de 83,8 %**. Bien que la précision descende à 54,3 %, ce compromis est parfaitement aligné avec les exigences de sécurité industrielle de MaintAI.

### 3.5 Traçabilité de l'environnement logiciel
L'examen du dossier `artifacts/model/requirements.txt` généré par MLflow confirme l'enregistrement strict des dépendances :
```text
mlflow==3.18.0
numpy==2.4.4
pandas==3.0.2
scikit-learn==1.8.0
skops==0.16.0
```
Cela résout le problème fondamental soulevé au TP4 (`InconsistentVersionWarning` et instabilités de désérialisation) en encapsulant la spécification exacte des bibliothèques nécessaires à l'inférence.

---

## 4. Sprint 2 : Versionnement des données avec DVC

### 4.1 Initialisation et gestion du jeu de données v1
DVC a été initialisé en mode sous-répertoire (`dvc init --subdir`). Le suivi de `data/sensors.csv` (5 000 lignes) a généré le fichier pointeur `data/sensors.csv.dvc` :

```yaml
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv
```

La signature MD5 (`73e0b7cb3c6f795c70c3ddf970b99c15`) correspond trait pour trait au paramètre `data_md5` enregistré lors de nos entraînements MLflow. Le stockage distant local a été configuré (`dvc remote add --local -d stockage "$env:USERPROFILE\dvc-stockage"`) puis les données ont été poussées via `dvc push`.

### 4.2 Évolution vers le jeu de données v2
Un nouveau dataset étendu de 8 000 lignes a été synthétisé (`python -m maintai.dataset --n 8000 --seed 7`).
La commande `dvc status` a immédiatement détecté la modification :
```text
data\sensors.csv.dvc:
	changed outs:
		modified:           data\sensors.csv
```

Après réindexation via `dvc add data/sensors.csv` et synchronisation sur le remote (`dvc push`), les caractéristiques des versions sont :

| Version | Commit Git | MD5 (8 car.) | Nombre de lignes | Taille (octets) |
|:---:|:---:|:---:|:---:|:---:|
| **v1** | `970e9f3` | `73e0b7cb` | 5 000 | 126 815 |
| **v2** | `cc3c356` | `93fdeef2` | 8 000 | 202 834 |

### 4.3 Démonstration de checkout et de restauration
1. **Retour en arrière vers v1 :**
   ```powershell
   git checkout 970e9f3 -- data/sensors.csv.dvc
   dvc checkout
   ```
   Vérification : `data/sensors.csv` compte à nouveau très exactement **5 000 lignes**.
2. **Retour vers v2 :**
   ```powershell
   git checkout HEAD -- data/sensors.csv.dvc
   dvc checkout
   ```
   Vérification : le fichier revient instantanément à **8 000 lignes**.
3. **Restauration depuis le remote :** Après suppression physique de `data/sensors.csv` et vidage de `.dvc/cache`, la commande `dvc pull` extrait sans faille les données depuis le stockage distant et les remet en place dans l'arborescence de travail.

---

## 5. Corrélation modèles-données et synthèse critique

### 5.1 Comparaison v1 vs v2
| Version | MD5 (8 car.) | Données train ($n_{train}$) | Recall | Precision | Accuracy |
|:---:|:---:|:---:|:---:|:---:|:---:|
| v1 | `73e0b7cb` | 4 000 | 0.750 | 0.622 | 0.904 |
| v2 | `93fdeef2` | 6 400 | 0.741 | 0.650 | 0.916 |

### 5.2 Pourquoi comparer des métriques sur des jeux de données différents est trompeur
Bien que la précision et l'exactitude globale progressent sur v2, le rappel diminue de 75 % à 74,1 %. Il est méthodologiquement incorrect d'en déduire que le modèle v2 est « supérieur » ou « inférieur », car **les ensembles de test sont différents** (1 000 lignes pour v1 contre 1 600 lignes pour v2). 
Dans une démarche MLOps rigoureuse, pour isoler l'impact de l'augmentation du volume de données, il convient d'évaluer tous les modèles sur un même jeu de test de référence figé (*Golden Test Dataset*).

---

## 6. Réponses aux questions de compréhension

1. **Rôles respectifs de Git, DVC et MLflow :**
   - **Git :** Gère l'historique et les branches du code source, de la documentation et des fichiers pointeurs légers (`.dvc`, `.gitignore`).
   - **DVC :** Gère le cycle de vie et le stockage des jeux de données lourds et des modèles dans des magasins d'objets (S3, GCS ou dossier distant), en découplant le contenu binaire du contrôle de version textuel.
   - **MLflow :** Enregistre la traçabilité fine des entraînements : hyperparamètres, séries temporelles de métriques, signatures d'entrées/sorties, spécifications de dépendances et modèles sérialisés prêts pour l'inférence.

2. **Justification de l'option `--local` et partage en équipe :**
   - L'argument `--local` restreint l'écriture de la configuration du remote au fichier local `.dvc/config.local` (exclu de Git). Cela évite de versionner un chemin absolu Windows propre à un utilisateur particulier.
   - Pour collaborer à l'échelle du groupe, le remote doit être configuré vers un stockage mutualisé (ex. bucket AWS S3, Google Cloud Storage, ou répertoire réseau partagé) et inscrit dans le fichier `.dvc/config` versionné sous Git.

3. **Les trois piliers de la livraison d'un modèle :**
   - **Le code d'inférence et de transformation :** Présent dans le dépôt Git (`maintai/`).
   - **L'artefact entraîné du modèle :** Conservé dans le store d'artefacts MLflow au format skops.
   - **L'environnement d'exécution strict :** Spécifié dans les métadonnées déclaratives MLflow (`requirements.txt` et `conda.yaml`).

---

## 7. Décision architecturale et conclusion personnelle

La décision formelle de sélection du modèle a été actée dans le document `docs/adr/004-choix-du-modele.md`. Le modèle retenu (Régression Logistique avec seuil à 0.2) répond idéalement à l'impératif de sécurité de MaintAI en interceptant 83,8 % des défaillances.

**Perspectives / Points d'approfondissement :**
L'association de DVC et MLflow au sein d'un pipeline automatisé CI/CD (avec GitHub Actions ou DVC Pipelines `dvc repro`) constitue l'étape suivante pour industrialiser totalement le réentraînement et le déploiement continu sans intervention manuelle.
