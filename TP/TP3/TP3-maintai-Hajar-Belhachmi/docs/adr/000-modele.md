# ADR 000 : Choix de Streamlit pour l'interface utilisateur de MaintAI

**Date :** 09/11/2026 · **Auteur :** BELHACHMI Hajar

## Contexte

Le projet MaintAI permet de prédire les risques de panne d'équipements industriels à partir de données de capteurs. Il est nécessaire de proposer une interface simple permettant à l'utilisateur de saisir les valeurs des capteurs et de consulter le résultat de la prédiction sans avoir à utiliser directement le terminal.

## Options étudiées

1. **Streamlit :**
   - Avantages : facile à utiliser avec Python, rapide à développer et adapté aux applications de Machine Learning.
   - Inconvénients : personnalisation graphique limitée par rapport à un framework frontend classique.

2. **Flask avec HTML, CSS et JavaScript :**
   - Avantages : grande liberté de conception et personnalisation de l'interface.
   - Inconvénients : nécessite davantage de développement et la gestion de plusieurs technologies.

## Décision

Nous avons choisi Streamlit pour développer l'interface utilisateur de MaintAI.

La raison principale est sa simplicité d'intégration avec Python et les bibliothèques de Machine Learning utilisées dans le projet. Ce choix permet de développer rapidement une interface interactive sans ajouter une architecture frontend complexe.

## Conséquences

- Facilite la création d'une interface permettant de saisir les données des capteurs et d'afficher les prédictions.
- Permet de réutiliser directement le code Python du projet.
- Réduit le temps de développement et la complexité de l'application.
- Offre moins de possibilités de personnalisation graphique qu'une interface développée avec un framework frontend dédié.
- Nécessite de maintenir la cohérence entre l'interface Streamlit et le système de prédiction MaintAI.