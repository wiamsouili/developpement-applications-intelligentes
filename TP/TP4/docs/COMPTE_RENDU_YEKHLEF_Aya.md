# Compte rendu · TP4 : Packaging et industrialisation de MaintAI

**Module :** Développement et déploiement d'applications intelligentes  
**Projet :** MaintAI — Package Python d'inférence industrielle  
**Étudiante :** YEKHLEF Aya  
**Groupe :** G3  
**Date :** 09/11/2026  

---

## 1. Mise en place initiale et diagnostic des tests

### 1.1 Contexte du TP4
L'enjeu de cette séance est de transformer l'arborescence de scripts MaintAI en un véritable **package Python diffusable et installable** selon les standards modernes de packaging (`pyproject.toml`, PEP 517/518/621). Le package doit exposer une commande CLI native (`maintai-predict`) et pouvoir être distribué sous forme d'archive wheel (`.whl`).

### 1.2 Exécution avant installation du package
Dès la mise en place du TP4 et l'installation des dépendances de base, l'exécution de la suite de tests avec :
```powershell
python -m pytest
```
renvoie le résultat suivant :
```text
=================== 2 failed, 25 passed, 1 warning in 7.06s ===================
FAILED tests/test_package.py::test_installed_version_matches_the_code
FAILED tests/test_package.py::test_command_is_declared
```

### 1.3 Analyse des deux tests en échec
1. **`test_installed_version_matches_the_code` :** Ce test interroge `importlib.metadata.version("maintai")`. Il échoue avec une exception `PackageNotFoundError` car `maintai` n'a pas encore été installé comme distribution enregistrée dans l'environnement Python actif.
2. **`test_command_is_declared` :** Ce test vérifie la présence du point d'entrée `maintai-predict` parmi les `console_scripts`. L'exécutable n'étant pas encore déclaré dans l'environnement, l'assertion échoue.

Ces deux échecs sont strictement normaux à ce stade et constituent les objectifs cibles du premier sprint.

---

## 2. Sprint 1 : Standardisation avec `pyproject.toml` et mode éditable

### 2.1 Spécification des métadonnées et dépendances
Dans le fichier `pyproject.toml`, nous définissons les dépendances de base requises pour l'inférence ainsi que le script CLI :

```toml
[project]
name = "maintai"
version = "0.2.0"
description = "Package Python de prédiction des pannes de maintenance industrielle"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "numpy>=2.0",
    "pandas>=2.2",
    "scikit-learn>=1.5",
    "joblib>=1.4",
]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

### 2.2 Ségrégation des dépendances (`dependencies` vs groupes optionnels)
* **Pourquoi `pytest` et `fastapi` ne figurent pas dans `dependencies` :**
  Un utilisateur final souhaitant uniquement intégrer le moteur de prédiction MaintAI dans un script ou l'exécuter en ligne de commande n'a pas besoin de l'infrastructure web FastAPI ni du framework de test pytest.
* **Architecture modulaire :** Ces dépendances sont reléguées dans des extras optionnels :
  - `dev` : outils de linting et de test (`pytest`).
  - `api` : framework et serveur REST (`fastapi`, `uvicorn`).
  - `ui` : interface interactive (`streamlit`).
  Cela garantit une empreinte d'installation minimale et préserve la légèreté du package.

### 2.3 Installation en mode éditable et validation
Nous lions le package au `.venv` local via :
```powershell
pip install -e .
```

* **Vérification des métadonnées (`pip show maintai`) :**
```text
Name: maintai
Version: 0.2.0
Summary: Package Python de prédiction des pannes de maintenance industrielle
Home-page:
```

* **Exécution de la suite complète des 27 tests :**
```text
======================== 27 passed, 1 warning in 5.47s ========================
```
Les 27 tests sont validés sans aucune régression.

### 2.4 Test de la commande en ligne de commande (`maintai-predict`)
Exécution d'un relevé d'avarie typique :
```powershell
maintai-predict 72 6 85 15000
```
Résultat obtenu :
```text
Probabilité de panne : 95 % (ALERTE)
```

* **Prise en compte dynamique des modifications :**
  Lorsqu'on édite le texte ou la logique dans `maintai/cli.py`, les changements sont immédiatement effectifs à l'appel de `maintai-predict`, sans réinstallation. C'est l'atout majeur du mode éditable (`-e`), qui insère un fichier `.pth` pointant directement vers les sources en cours d'édition.

---

## 3. Sprint 2 : Construction, inspection et portabilité du Wheel

### 3.1 Génération des artefacts de distribution
À l'aide de l'outil standard `build` :
```powershell
python -m build
```
Les archives générées dans le sous-dossier `dist/` sont :
- `maintai-0.2.0.tar.gz` : Archive source complète (*sdist*).
- `maintai-0.2.0-py3-none-any.whl` : Archive binaire pré-construite universelle (*wheel*).

### 3.2 Audit du contenu du Wheel
L'inspection de l'archive binaire (`tar -tf dist\maintai-0.2.0-py3-none-any.whl`) révèle l'arborescence :
```text
maintai/__init__.py
maintai/cli.py
maintai/client.py
maintai/config.py
maintai/data.py
maintai/dataset.py
maintai/predict.py
maintai/train.py
maintai/api/__init__.py
maintai/api/main.py
maintai/api/schemas.py
maintai/api/security.py
maintai-0.2.0.dist-info/METADATA
maintai-0.2.0.dist-info/WHEEL
maintai-0.2.0.dist-info/entry_points.txt
maintai-0.2.0.dist-info/RECORD
```

* **Absence des tests, du modèle et de `ui/` :**
  Le fichier `.whl` ne contient strictement que le code du package Python `maintai`. 
  - Les tests unitaires n'ont pas vocation à être distribués en production.
  - Le dossier `ui/` relève d'une application cliente séparée.
  - Les poids du modèle sérialisé (`model.joblib`) ne doivent jamais être figés dans le code binaire du package (séparation stricte code / données / modèles préconisée en MLOps).

### 3.3 Test de déploiement dans un environnement neuf
L'installation du wheel dans un environnement virtuel temporaire isolé :
```powershell
python -m pip install dist\maintai-0.2.0-py3-none-any.whl
```
* **Comportement sans configuration :** L'inférence échoue si le modèle est introuvable, car le package attend l'emplacement des poids.
* **Comportement avec variable d'environnement :**
  En définissant `$env:MAINTAI_MODELS_DIR = "chemin\vers\models"`, l'inférence CLI s'exécute parfaitement :
  ```text
  Probabilité de panne : 95 % (ALERTE)
  ```

### 3.4 Analyse de la traçabilité des versions Scikit-learn
* **Origine de l'alerte `InconsistentVersionWarning` :**
  Cet avertissement survient lorsque Scikit-learn désérialise un objet `joblib` créé avec une version différente de la bibliothèque (ex: entraîné sous `1.8.0` et relu sous `1.9.x`).
* **Source de vérité :**
  Dans le fichier `models/model_info.json`, la ligne `"sklearn_version": "1.8.0"` permet d'identifier formellement la version de dépendance exacte requise pour une inférence exempte d'instabilité numérique.

---

## 4. Questions de réflexion technique

### 4.1 Quelle est la distinction clé entre `requirements.txt` et `dependencies` de `pyproject.toml` ?
* `requirements.txt` est un fichier de verrouillage d'environnement. Il est destiné au développeur ou au serveur d'exécution pour figer des versions exactes (`==`) et garantir une reproductibilité stricte.
* `dependencies` dans `pyproject.toml` est une spécification déclarative abstraite de distribution. Elle indique aux gestionnaires de paquets (pip, uv, poetry) les contraintes de compatibilité minimales ou souples (`>=`) nécessaires au bon fonctionnement du package sans restreindre inutilement l'utilisateur.

### 4.2 Quelle différence entre `pip install -e .` et l'installation d'un `.whl` ?
* `pip install -e .` met en place un lien symbolique vers le dossier source local. C'est l'environnement idéal de développement : toute retouche de code est immédiatement active sans reconstruction.
* `pip install ...whl` copie les fichiers figés du paquet dans le dossier `site-packages` de Python. C'est le mode de distribution autonome utilisé en intégration continue et en déploiement de production.

### 4.3 Comment fonctionne un point d'entrée (`[project.scripts]`) et où est-il généré sous Windows ?
La déclaration `maintai-predict = "maintai.cli:main"` demande à setuptools de générer un wrapper exécutable autonome.
Sous Windows, lors de l'installation, pip génère automatiquement le binaire :
```text
.venv\Scripts\maintai-predict.exe
```
qui lance l'interpréteur Python et invoque la méthode `main()` sans exiger la syntaxe `python -m maintai.cli`.

---

## 5. Bilan et synthèse

Ce TP4 concrétise le cycle de vie industriel de MaintAI :
- Normalisation du projet selon les normes PEP modernes avec `pyproject.toml`.
- Automatisation de la commande CLI `maintai-predict`.
- Construction d'un artefact wheel indépendant, léger et déployable sur n'importe quel serveur ou conteneur d'atelier.
- Validation intégrale confirmée par 27 tests automatisés réussis.
