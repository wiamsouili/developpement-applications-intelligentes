# Compte rendu · TP4 : Packaging et distribution du projet MaintAI

**Module :** Développement et déploiement d'applications intelligentes  
**Projet :** MaintAI — Industrialisation du modèle prédictif  
**Étudiante :** ELAOUAZI Hafsa  
**Groupe :** G3  
**Date :** 09/11/2026  

---

## 1. Contexte et état des tests à l'initialisation

### 1.1 Objectifs de la séance
Ce TP4 vise à industrialiser le code source de MaintAI pour en faire un **package Python réutilisable** structuré autour de `pyproject.toml`. Le projet doit fournir à la fois une bibliothèque Python importable et une commande autonome en console (`maintai-predict`).

### 1.2 Diagnostic initial avec pytest
Avant la configuration du package, la commande de test :
```powershell
python -m pytest
```
renvoie **2 tests en échec sur 27 tests** (`2 failed, 25 passed, 1 warning`) :
- `test_installed_version_matches_the_code` : Échoue car le package `maintai` n'a pas encore été installé dans l'environnement virtuel et ses métadonnées sont introuvables.
- `test_command_is_declared` : Échoue car le point d'entrée `maintai-predict` n'est pas encore déclaré.

Ces deux échecs constituent les livrables du Sprint 1.

---

## 2. Sprint 1 : Standardisation via `pyproject.toml` et mode éditable

### 2.1 Configuration du fichier `pyproject.toml`
Nous déclarons les métadonnées et dépendances de base :

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

### 2.2 Rôle des dépendances optionnelles
Seules les bibliothèques requises pour l'inférence (NumPy, Pandas, Scikit-Learn, Joblib) sont incluses dans les dépendances principales. Les packages tels que `pytest` (tests), `fastapi` (API) et `streamlit` (UI) sont configurés comme dépendances optionnelles afin d'alléger l'installation pour les utilisateurs n'utilisant que la commande CLI ou le cœur algorithmique.

### 2.3 Installation éditable (`pip install -e .`)
L'installation en mode éditable permet de lier le package directement au dossier source :
```powershell
pip install -e .
```
- La commande `pip show maintai` confirme la version `0.2.0`.
- L'ensemble des **27 tests passe avec succès** :
```text
======================== 27 passed, 1 warning in 5.47s ========================
```

### 2.4 Test de la commande `maintai-predict`
Exécution en terminal :
```powershell
maintai-predict 72 6 85 15000
```
Résultat :
```text
Probabilité de panne : 95 % (ALERTE)
```
Grâce au mode éditable, toute modification dans `maintai/cli.py` est directement prise en compte sans devoir réinstaller le package.

---

## 3. Sprint 2 : Construction et portabilité du Wheel

### 3.1 Génération des archives
La commande :
```powershell
python -m build
```
produit dans le dossier `dist/` :
- Le fichier source `maintai-0.2.0.tar.gz`.
- Le binaire `maintai-0.2.0-py3-none-any.whl`.

### 3.2 Vérification de l'archive wheel
L'archive binaire contient uniquement les modules Python de `maintai` et les métadonnées `dist-info`. Le dossier `tests/`, les modèles entraînés et l'interface `ui/` ne sont pas inclus dans le wheel pour respecter la séparation entre code distribué et artefacts de données.

### 3.3 Test d'installation isolé
Le wheel a été installé dans un environnement neuf :
```powershell
python -m pip install dist\maintai-0.2.0-py3-none-any.whl
```
En configurant la variable d'environnement `$env:MAINTAI_MODELS_DIR = "chemin/vers/models"`, la commande fonctionne parfaitement :
```text
Probabilité de panne : 95 % (ALERTE)
```

### 3.4 Suivi des versions de Scikit-learn
L'avertissement `InconsistentVersionWarning` apparaît si la version de Scikit-learn utilisée pour charger le modèle diffère de celle de l'entraînement. La version exacte est documentée dans `models/model_info.json` (`"sklearn_version": "1.8.0"`).

---

## 4. Questions de réflexion

### 4.1 Différence entre `requirements.txt` et `dependencies` ?
`requirements.txt` permet de reproduire un environnement exact avec des versions strictes (`==`), tandis que `dependencies` dans `pyproject.toml` spécifie les dépendances minimales abstraites requises pour qu'un utilisateur puisse installer et utiliser la bibliothèque.

### 4.2 Différence entre `pip install -e .` et l'installation d'un `.whl` ?
`pip install -e .` installe le package avec un lien direct vers le code source pour faciliter le développement. L'installation d'un fichier wheel copie les fichiers de manière définitive dans `site-packages` pour la production.

### 4.3 Qu'est-ce qu'un point d'entrée et où se trouve l'exécutable ?
Un point d'entrée associe une commande console à une fonction Python. Sous Windows, pip crée le binaire `maintai-predict.exe` dans le dossier `.venv\Scripts\`.

---

## 5. Conclusion

Le TP4 a permis de concrétiser le déploiement de MaintAI :
- Packaging complet et moderne avec `pyproject.toml`.
- Commande CLI `maintai-predict` opérationnelle.
- Validation intégrale confirmée par 27 tests réussis.
