# Compte rendu · TP5 : Suivi des modèles avec MLflow et gestion des données avec DVC

**Groupe :** G3  
**Fait par :** Hajar Belhachmi  
**Date :** 16/11/2026  


**Heure :** 12:15

---

## 1. Mise en place (dans `TP/TP5`)

**Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :**

```text
======================= 5 failed, 27 passed, 4 warnings in 62.58s =======================
```

**Quels tests échouent, et pourquoi ?**

Les 5 tests qui échouent sont situés dans `tests/test_tracking.py` :
- `test_log_run_returns_run_id`
- `test_log_run_logs_params`
- `test_log_run_logs_metrics`
- `test_log_run_logs_model`
- `test_log_run_logs_data_md5`

**Pourquoi :** La fonction `log_run` du fichier `maintai/tracking.py` n'était pas encore implémentée (c'était un squelette retournant une chaîne vide `""`). Aucun run MLflow n'était créé, donc ni les paramètres, ni les métriques, ni le modèle ou le hash MD5 des données n'étaient enregistrés dans le système de tracking.

**Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?**

- **Avant :** Le package `maintai` pointait sur l'installation des séances précédentes (TP4 ou TP1), sans le nouveau module de traçabilité `tracking.py`.
- **Après :** En mode éditable, le package pointe désormais directement sur `c:\Users\hp\Downloads\TP1_YEKHLEF_Aya\TP\TP5\maintai` (version `0.3.0`), intégrant toutes les fonctionnalités nécessaires pour ce TP5.

---

## 2. Sprint 1 : MLflow

**Notre fonction `log_run` (`maintai/tracking.py`) :**

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

**Dernière ligne de `python -m pytest` à la fin du sprint 1 :**

```text
======================= 32 passed, 4 warnings in 51.52s =======================
```

**Runs relevés dans `mlflow ui` (mode « Model training ») :**

| Commande | recall | precision | accuracy |
|---|:---:|:---:|:---:|
| `python -m maintai.train` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | **0.838** | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train` (sur v2, 8000 lignes) | 0.741 | **0.650** | **0.916** |

**Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)**

Pour MaintAI, nous choisissons le modèle avec **`--threshold 0.2`** (Run ID `41d5da4541464a129650109e2cdba029`).
Dans le domaine industriel, une panne non détectée (faux négatif) provoque l'arrêt immédiat d'une ligne de production et génère des coûts de réparation et d'arrêt considérables. À l'inverse, une fausse alerte (faux positif) ne demande qu'une vérification rapide par un technicien.
En baissant le seuil à 0.2, le **rappel (*recall*) monte à 83,8 %**, ce qui permet d'intercepter la grande majorité des pannes réelles. Même si la précision baisse à 54,3 %, c'est le meilleur compromis opérationnel pour garantir la continuité de service.

**Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?**

La version indiquée dans `artifacts/model/requirements.txt` est :
```text
scikit-learn==1.8.0
```
Dans le TP4, charger un modèle sérialisé sur une version différente de scikit-learn provoquait un avertissement `InconsistentVersionWarning` ou un dysfonctionnement. MLflow résout ce problème en sauvegardant automatiquement la liste exacte des dépendances nécessaires (`requirements.txt`), ce qui assure une parfaite reproductibilité en production.

**Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?**

MLflow stocke les données des runs dans le dossier local `TP/TP5/mlruns/` ainsi que dans la base SQLite `mlflow.db`.
Ces fichiers ne vont pas dans Git car ils sont ignorés par le fichier `.gitignore`. Les modèles sérialisés et les journaux de runs sont trop volumineux et changent à chaque entraînement ; les intégrer dans Git alourdirait inutilement le dépôt de code.

---

## 3. Sprint 2 : DVC

**Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :**

```yaml
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv
```

**Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?**

La valeur `md5` du fichier `data/sensors.csv.dvc` (`73e0b7cb3c6f795c70c3ddf970b99c15`) est exactement la même que la valeur du paramètre `data_md5` enregistrée dans MLflow.
Cela prouve le lien direct entre les données et le modèle : chaque run MLflow est traçable jusqu'à la version exacte des données gérées par DVC.

**Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?**

`data/sensors.csv` contient les données brutes (des milliers de lignes de mesures capteurs). Git n'est pas conçu pour stocker efficacement des fichiers volumineux qui changent souvent.
En revanche, `data/sensors.csv.dvc` est un petit fichier texte (quelques lignes) qui contient l'empreinte MD5, la taille et le chemin du jeu de données. Git versionne ce petit fichier sans difficulté, tandis que DVC gère le stockage physique des données dans un cache ou un serveur distant.

**Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?**

```text
data\sensors.csv.dvc:
	changed outs:
		modified:           data\sensors.csv
```

**Tableau récapitulatif des versions de données :**

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|:---:|
| v1 | `970e9f3` | `73e0b7cb` | 5000 |
| v2 | `cc3c356` | `93fdeef2` | 8000 |

**Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.**

- Après le retour à la v1, `data/sensors.csv` contient **5 000 lignes**.
- Après le retour à la v2 (`git checkout HEAD -- data/sensors.csv.dvc` et `dvc checkout`), le fichier revient à **8 000 lignes**. Le basculement se fait très rapidement.

**Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?**

DVC télécharge le fichier depuis le stockage distant (`dvc-stockage`) et réinstalle `data/sensors.csv` à l'identique dans le dossier `data/`.

---

## 4. Relier modèle et données

**Comparaison entre v1 et v2 :**

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|:---:|:---:|:---:|
| v1 | `73e0b7cb` | 4000 | 0.750 | 0.622 |
| v2 | `93fdeef2` | 6400 | 0.741 | 0.650 |

**Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?**

Non, on ne peut pas affirmer que le modèle v2 est systématiquement meilleur. Si la précision augmente un peu (0.650 contre 0.622), le rappel baisse légèrement (0.741 contre 0.750).
Surtout, les deux modèles ont été testés sur des jeux de test différents (1 000 données pour v1 contre 1 600 pour v2). Pour comparer rigoureusement deux modèles entraînés sur des données différentes, il faudrait les tester sur le même jeu de test de référence fixé à l'avance.

---

## 5. Décision : l'ADR 004

- Fichier : `docs/adr/004-choix-du-modele.md`
- Modèle choisi : **Régression Logistique avec seuil de décision à 0.2**
- Run ID MLflow : `41d5da4541464a129650109e2cdba029`
- `data_md5` DVC : `73e0b7cb3c6f795c70c3ddf970b99c15`
- Métriques : Rappel = 0.838, Précision = 0.543, Exactitude = 0.882

---

## 6. Questions de compréhension

1. **Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?**
   - **Git :** Versionne le code source, les fichiers de configuration et les documents texte du projet.
   - **DVC :** Versionne les données volumineuses et les fichiers lourds via des pointeurs `.dvc` tout en envoyant les données réelles sur un stockage distant.
   - **MLflow :** Enregistre et compare les expériences d'entraînement de machine learning (hyperparamètres, métriques, artefacts de modèles, environnement d'exécution).

2. **Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?**
   - L'option `--local` enregistre le chemin dans `.dvc/config.local` (ignoré par Git) parce que le dossier `%USERPROFILE%\dvc-stockage` est propre à la machine locale de l'étudiant.
   - Pour que tout le groupe partage les mêmes données, il faudrait configurer un remote centralisé partagé (par exemple un bucket cloud AWS S3 ou Google Cloud Storage) et l'enregistrer dans `.dvc/config` (sans `--local`), afin que toute l'équipe puisse faire `dvc pull` et `dvc push`.

3. **Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?**
   - 1. Le code de pipeline et d'inférence : dans le dépôt Git (package `maintai/`).
   - 2. L'artefact du modèle entraîné : dans le dossier d'artefacts MLflow (format skops).
   - 3. L'environnement d'exécution exact : dans le fichier `requirements.txt` généré automatiquement par MLflow avec le modèle.

---

## 7. Le rendu Git

- Lien du dépôt : `https://github.com/wiamsouili/developpement-applications-intelligentes`
- Le tag `tp5` existe sur GitHub : oui
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` n'apparaissent pas car ils sont exclus par `.gitignore` et `.dvcignore`.

---

## 8. Ce qui reste flou

La façon d'orchestrer automatiquement les pipelines DVC (`dvc repro`) directement dans un workflow d'intégration continue (GitHub Actions) en connectant les logs à un serveur MLflow partagé en ligne.

