# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** G3  ·  **Membres :** YEKHLEF Aya, SOUILI Wiam, ELAOUAZI Hafsa, BELHACHMI Hajar  ·  **Date :** 16/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP5.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```text
======================= 5 failed, 27 passed, 4 warnings in 62.58s =======================
```

Quels tests échouent, et pourquoi ?

Les 5 tests qui échouent sont situés dans `tests/test_tracking.py` :
- `test_log_run_returns_run_id`
- `test_log_run_logs_params`
- `test_log_run_logs_metrics`
- `test_log_run_logs_model`
- `test_log_run_logs_data_md5`

**Pourquoi :** Dans le starter fourni, la fonction `log_run` du module `maintai/tracking.py` n'était pas implémentée (c'était une fonction squelette retournant une chaîne vide `""`). En conséquence, aucune expérience MLflow n'était initialisée, aucun run n'était créé, et ni les hyperparamètres, ni les métriques, ni les artefacts de modèle ou le hash MD5 des données n'étaient enregistrés dans le tracking store.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

- **Avant `pip install -e .` :** Le package `maintai` pointait vers le dossier d'un TP précédent (TP4 ou TP1), installé en mode éditable dans l'environnement virtuel partagé. Ce code ne comportait pas encore le module `maintai.tracking`.
- **Après `pip install -e .` :** Le package en mode éditable pointe désormais directement sur `c:\Users\hp\Downloads\TP1_YEKHLEF_Aya\TP\TP5\maintai` (version `0.3.0`), intégrant ainsi toutes les fonctions de traçabilité MLflow requises pour la séance.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

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

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```text
======================= 32 passed, 4 warnings in 51.52s =======================
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train` (sur v2, 8000 lignes) | 0.741 | 0.650 | 0.916 |

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

Nous choisissons sans hésitation le modèle avec **`--threshold 0.2`** (Run ID `41d5da4541464a129650109e2cdba029`).
**Justification :** Dans un contexte de maintenance prédictive critique pour MaintAI, une panne non détectée (faux négatif) provoque un arrêt d'urgence catastrophique de l'usine, des pertes d'exploitation lourdes et un risque d'endommagement irréversible des équipements. À l'inverse, une fausse alerte (faux positif) n'engendre qu'un coût mineur d'inspection préventive par un technicien. 
En abaissant le seuil à 0.2, le **rappel (*recall*) grimpe à 83,8 %**, détectant près de 84 % des pannes réelles. Même si la précision fléchit à 54,3 % (induisant plus de vérifications préventives), cet arbitrage privilégie la sécurité industrielle maximale.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

La version indiquée dans `artifacts/model/requirements.txt` est :
```text
scikit-learn==1.8.0
```
Dans le TP4, la désérialisation d'un modèle avec pickle ou skops pouvait déclencher des alertes critiques (`InconsistentVersionWarning`) ou des incompatibilités d'exécution si l'environnement de production utilisait une version différente de scikit-learn. MLflow règle définitivement ce problème en empaquetant automatiquement le fichier `requirements.txt` figé avec la version exacte des dépendances au moment de l'entraînement, garantissant un environnement d'inférence 100 % reproductible et sécurisé.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

- **Emplacement sur le disque :** MLflow enregistre les runs localement dans le dossier `TP/TP5/mlruns/` (qui structure les identifiants d'expériences, les dossiers de runs, les paramètres, les métriques et les artefacts sérialisés dans `models/`) ainsi que dans la base SQLite `mlflow.db`.
- **Intégration dans Git :** Non, ces fichiers ne vont absolument pas dans Git. Ils sont explicitement répertoriés dans `.gitignore`.
- **Pourquoi :** Les artefacts de modèles de Machine Learning, les checkpoints, les poids binaires et les bases d'expériences sont volumineux et évoluent constamment. Les placer dans Git alourdirait considérablement l'historique et dégraderait les performances de versionnement. Git est dédié au code source et aux configurations textuelles légères ; la traçabilité des modèles relève de MLflow.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```yaml
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

La valeur `md5` présente dans `data/sensors.csv.dvc` (`73e0b7cb3c6f795c70c3ddf970b99c15`) est **strictement identique** au paramètre `data_md5` tracé dans MLflow.
**Constat :** Cela démontre la continuité de traçabilité MLOps entre les données et le modèle. Tout entraînement enregistré dans MLflow est relié de manière formelle et vérifiable au snapshot exact du jeu de données géré par DVC.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

`data/sensors.csv` est un fichier de données tabulaires volumineux pouvant atteindre des centaines de milliers de lignes. Git est inefficace pour stocker les fichiers volumineux modifiés fréquemment, car il enregistre une copie complète à chaque changement.
En revanche, `data/sensors.csv.dvc` est un fichier pointeur textuel minuscule de quelques lignes (~100 octets). Il contient l'empreinte MD5, la taille et le chemin relatif du jeu de données. Git versionne très rapidement ce pointeur léger, tandis que DVC gère le stockage physique des données dans son cache ou son stockage distant (*remote*).

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```text
data\sensors.csv.dvc:
	changed outs:
		modified:           data\sensors.csv
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | `970e9f3` | `73e0b7cb` | 5000 |
| v2 | `cc3c356` | `93fdeef2` | 8000 |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

- Après avoir restauré le pointeur de la v1 (`git checkout 970e9f3 -- data/sensors.csv.dvc && dvc checkout`), le fichier `data/sensors.csv` contient exactement **5000 lignes**.
- Après être revenu à la v2 (`git checkout HEAD -- data/sensors.csv.dvc && dvc checkout`), `data/sensors.csv` repasse immédiatement à **8000 lignes**. Le basculement entre versions de données est transparent et instantané.

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

DVC interroge le stockage distant configuré (`stockage` situé dans `%USERPROFILE%\dvc-stockage`), télécharge l'objet correspondant au hash MD5 du pointeur courant, reconstitue le cache local et restaure complètement le fichier `data/sensors.csv`. Les données sont récupérées sans jamais avoir encombré le dépôt Git.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 | `73e0b7cb` | 4000 | 0.750 | 0.622 |
| v2 | `93fdeef2` | 6400 | 0.741 | 0.650 |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

**Non, on ne peut pas conclure directement que le modèle v2 est supérieur au modèle v1.**
Bien que la précision s'améliore (65,0 % contre 62,2 %) et que l'accuracy progresse (91,6 % contre 90,4 %), le rappel est en légère baisse (74,1 % contre 75,0 %).
**Pourquoi la prudence s'impose :** Les deux modèles ont été évalués sur des jeux de test différents. Sur la v1, le test set compte 1000 observations ; sur la v2, il en compte 1600. Les métriques d'évaluation dépendent de la difficulté et de la répartition spécifique des pannes au sein de chaque échantillon de test. Pour comparer rigoureusement l'effet de l'augmentation du jeu d'entraînement, il est impératif d'évaluer les deux modèles sur un jeu de test de référence fixe et immuable (*golden evaluation dataset*).

## 5. Décision : l'ADR 004

Dans `docs/adr/004-choix-du-modele.md` : le modèle et le seuil retenus, à partir de votre tableau MLflow. Indiquez l'identifiant du run et le `data_md5` de la version des données utilisée.

- **Décision consignée dans :** `docs/adr/004-choix-du-modele.md`
- **Modèle sélectionné :** Régression logistique standardisée avec abaissement du seuil de décision à **0.2**
- **Identifiant du run MLflow :** `41d5da4541464a129650109e2cdba029`
- **Empreinte DVC des données (`data_md5`) :** `73e0b7cb3c6f795c70c3ddf970b99c15` (version v1)
- **Métriques clés :** Rappel = **0.838**, Précision = **0.543**, Accuracy = **0.882**

## 6. Questions de compréhension

1. **Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?**
   - **Git :** Versionne le code source, les fichiers de configuration textuels (`pyproject.toml`, scripts Python) et la documentation. Il est conçu pour les fichiers textes légers et l'historique des modifications de code.
   - **DVC (Data Version Control) :** Versionne les volumes de données volumineux (datasets bruts et transformés) et les artefacts de grande taille via des fichiers pointeurs légers (`.dvc`) commités dans Git, en déléguant le stockage réel à un remote de stockage dédié.
   - **MLflow :** Versionne et suit les expériences de Machine Learning : hyperparamètres d'entraînement, métriques scalaires au fil du temps, métadonnées, graphes de performance, environnements logiciels certifiés (`requirements.txt`) et artefacts de modèles exportés.

2. **Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?**
   - L'option `--local` enregistre la configuration du remote dans `.dvc/config.local` (fichier exclu de Git). Cela permet d'utiliser un chemin absolu propre à la machine locale de l'étudiant (`%USERPROFILE%\dvc-stockage`) sans polluer le dépôt Git commun avec des chemins locaux non portables.
   - Pour partager les données entre tous les membres du groupe, il faudrait configurer un remote centralisé partagé (tel qu'un bucket cloud AWS S3, Google Cloud Storage, Azure Blob Storage ou un serveur SFTP/réseau commun) et enregistrer ce remote sans `--local` dans `.dvc/config`. Tous les collaborateurs pourraient alors exécuter `dvc pull` et `dvc push` de manière transparente.

3. **Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?**
   - **1. Le code de pipeline et d'inférence :** Il est versionné dans Git au sein du module Python `maintai/`.
   - **2. L'artefact binaire du modèle :** Il est stocké et journalisé dans le registre d'artefacts de MLflow (`mlruns/1/.../artifacts/model`) au format sécurisé skops.
   - **3. L'environnement d'exécution exact et ses dépendances :** Il est consigné dans les artefacts MLflow sous forme de fichiers déclaratifs `requirements.txt` (`scikit-learn==1.8.0`, `skops==0.16.0`, etc.) et `conda.yaml`.

## 7. Le rendu Git

- Lien de la pull request : `https://github.com/wiamsouili/developpement-applications-intelligentes`
- Le tag `tp5` existe sur GitHub : **oui**
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? **non** (tous correctement filtrés par `.gitignore` et `.dvcignore`).

## 8. Ce qui reste flou

La synchronisation automatisée entre le déclenchement d'un pipeline DVC (`dvc repro`) et la journalisation native dans MLflow sans devoir exécuter manuellement chaque commande d'entraînement pourrait être explorée plus avant pour un déploiement continu en CI/CD.
