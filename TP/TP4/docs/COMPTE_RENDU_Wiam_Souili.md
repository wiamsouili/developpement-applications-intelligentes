# Compte rendu · TP4 : Construction et distribution du package MaintAI

**Module :** Développement et déploiement d'applications intelligentes  
**Projet :** MaintAI — Distribution autonome du service d'inférence  
**Étudiante :** SOUILI Wiam  
**Groupe :** G3  
**Date :** 09/11/2026  

---

## 1. Initialisation de l'environnement et diagnostic initial

### 1.1 Contexte technique
Le but de ce quatrième travail pratique est de structurer la solution logicielle MaintAI sous la forme d'un **paquetage Python standardisé**, géré par le fichier `pyproject.toml`. L'objectif est de rendre le modèle de prédiction consommable de manière autonome par des applications tierces, soit via l'import de la librairie Python, soit via une interface en ligne de commande (CLI).

### 1.2 Évaluation initiale avec `pytest`
À l'issue de l'installation des dépendances brutes du projet, le lancement des tests :
```powershell
python -m pytest
```
renvoie **2 échecs sur 27 tests** (`2 failed, 25 passed, 1 warning`) :
- `test_installed_version_matches_the_code` : Échoue en soulevant `importlib.metadata.PackageNotFoundError: No package metadata was found for maintai`. Cela s'explique par l'absence d'enregistrement préalable du package dans les métadonnées de l'interpréteur Python.
- `test_command_is_declared` : Échoue car le script exécutable `maintai-predict` n'est pas encore enregistré dans le groupe `console_scripts` du système.

Ces deux tests ciblent spécifiquement la phase de packaging du Sprint 1.

---

## 2. Sprint 1 : Configuration du packaging et installation éditable

### 2.1 Déclaration des métadonnées dans `pyproject.toml`
Nous configurons le manifeste de distribution moderne :

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

### 2.2 Gestion des dépendances obligatoires vs optionnelles
Les dépendances déclarées dans `dependencies` se limitent au strict nécessaire pour charger le modèle et produire une prédiction (calcul matriciel avec NumPy, manipulation tabulaire avec Pandas, pipeline Scikit-Learn et désérialisation Joblib). 
Les bibliothèques comme `pytest` (tests unitaires), `fastapi` / `uvicorn` (serveur HTTP) ou `streamlit` (interface utilisateur) sont exclues du cœur de distribution et reléguées dans `optional-dependencies`. Ainsi, un déploiement embarqué ou scripté n'installe pas de frameworks superflus.

### 2.3 Installation en mode développement (`pip install -e .`)
L'exécution de la commande :
```powershell
pip install -e .
```
enregistre le package en mode éditable. 
- La commande `pip show maintai` atteste de la détection de la version `0.2.0`.
- Le relancement des tests valide les **27 tests au vert** :
```text
======================== 27 passed, 1 warning in 5.47s ========================
```

### 2.4 Utilisation du binaire CLI `maintai-predict`
La commande générée est testée avec succès dans le terminal :
```powershell
maintai-predict 72 6 85 15000
```
Sortie obtenue :
```text
Probabilité de panne : 95 % (ALERTE)
```
Grâce à l'installation éditable, toute modification apportée au code source de `maintai/cli.py` est immédiatement prise en compte lors de l'exécution suivante, facilitant considérablement le cycle d'itération et de débogage.

---

## 3. Sprint 2 : Construction et portabilité du format Wheel

### 3.1 Création des paquets de distribution
La commande de build standardisée :
```powershell
python -m build
```
génère deux fichiers dans le répertoire `dist/` :
- `maintai-0.2.0.tar.gz` (archive source sdist).
- `maintai-0.2.0-py3-none-any.whl` (paquet binaire universel wheel).

### 3.2 Contrôle de l'archive binaire
L'analyse des fichiers archivés dans le wheel démontre que seuls les modules du package `maintai` et les métadonnées `dist-info` sont intégrés. Les répertoires de tests, de données d'entraînement et l'interface `ui/` en sont exclus. Cette étanchéité préserve la légèreté du package et garantit le découplage entre le code exécutable et les ressources externes.

### 3.3 Déploiement dans un environnement vierge
L'installation du wheel via :
```powershell
python -m pip install dist\maintai-0.2.0-py3-none-any.whl
```
permet de valider l'autonomie du package :
- **Sans chemin de modèle :** L'application signale logiquement l'absence du fichier d'artefact.
- **Avec la variable d'environnement :**
  ```powershell
  $env:MAINTAI_MODELS_DIR = "chemin/vers/models"
  maintai-predict 72 6 85 15000
  ```
  Le calcul s'exécute avec succès (`Probabilité de panne : 95 % (ALERTE)`).

### 3.4 Compatibilité binaire Scikit-learn
L'éventuel avertissement `InconsistentVersionWarning` signale un écart de version entre l'environnement d'entraînement de Joblib et celui d'inférence. Le fichier `models/model_info.json` consigne la version de référence (`"sklearn_version": "1.8.0"`), ce qui permet de verrouiller l'environnement cible pour garantir l'intégrité prédictive.

---

## 4. Questions de compréhension

### 4.1 Pourquoi distinguer `requirements.txt` et `dependencies` de `pyproject.toml` ?
`requirements.txt` est un fichier d'environnement opérationnel : il verrouille précisément chaque dépendance (ex: `scikit-learn==1.8.0`) pour reproduire un environnement à l'identique. À l'inverse, `dependencies` dans `pyproject.toml` déclare des contraintes sémantiques plus larges (ex: `scikit-learn>=1.5`) pour assurer la portabilité de la bibliothèque lorsqu'elle est installée par des tiers.

### 4.2 Quelle différence entre `pip install -e .` et l'installation d'un `.whl` ?
`pip install -e .` utilise un mode lien dynamique vers le répertoire source : tout changement du code est instantanément visible sans réinstallation. L'installation d'un fichier wheel copie les fichiers empaquetés de manière figée et définitive dans `site-packages`, garantissant l'immuabilité en production.

### 4.3 Qu'est-ce qu'un `console_script` et où se situe l'exécutable sous Windows ?
C'est un mécanisme standard de Python permettant de mapper une commande système vers une fonction Python (`maintai-predict = "maintai.cli:main"`). Lors de l'installation, pip génère automatiquement l'exécutable `maintai-predict.exe` dans le dossier `.venv\Scripts\`.

---

## 5. Bilan du TP

Ce TP4 concrétise l'industrialisation logicielle de MaintAI :
- Modularisation de l'application selon les standards modernes de l'écosystème Python.
- Mise à disposition d'une interface en ligne de commande performante.
- Distribution validée par les 27 tests unitaires du projet.
