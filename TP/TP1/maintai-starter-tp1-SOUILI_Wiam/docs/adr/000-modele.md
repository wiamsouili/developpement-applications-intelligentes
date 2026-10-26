# ADR 000 : Choix du modèle de prédiction de panne

Date : 26/10/2026 · Auteurs : Wian Souili

## Contexte
MaintAI doit estimer la probabilité de panne d'une machine à partir de 4 capteurs (`temperature_c`, `vibration_mm_s`, `load_pct`, `runtime_hours`). Une panne manquée arrête une ligne de production, donc le **rappel** compte plus que la précision, et le modèle doit renvoyer une **probabilité** (pour appliquer un seuil d'alerte) et rester assez rapide et simple à expliquer pour être exposé dans une API.

## Options étudiées
1. **Baseline (toujours « pas de panne »)** : aucun apprentissage, sert de référence. Accuracy de 0,864 sur le jeu de test uniquement parce que les pannes sont rares (13,6 % des relevés), mais rappel de 0 : elle ne détecte aucune panne. Inutilisable.
2. **Régression logistique (avec normalisation des variables)** : rapide à entraîner et à prédire, produit directement une probabilité, coefficients interprétables, fichier de modèle très léger. Limite : suppose une relation linéaire entre les capteurs et le risque (log-odds).
3. **Modèles plus complexes (forêt aléatoire, gradient boosting)** : captent des relations non linéaires et des interactions, mais sont plus lourds, plus difficiles à expliquer, et rien ne prouve ici qu'ils soient nécessaires.

## Décision
**Régression logistique, dans un `Pipeline` scikit-learn (`StandardScaler` + `LogisticRegression`), avec un seuil de décision de 0,3.**

Raison principale : elle respecte la contrainte du projet (détecter les pannes, avec une probabilité exploitable) tout en restant simple et rapide. Sur le jeu de test (1000 relevés), au seuil de 0,3 : accuracy 0,904, **rappel 0,750**, précision 0,622, contre un rappel de 0 pour la baseline. Le seuil est abaissé de 0,5 à 0,3 volontairement : on accepte plus de fausses alertes pour rater moins de pannes. Le scaler est sauvegardé avec le classifieur, ce qui garantit le même prétraitement à l'entraînement et en production.

Le contrat d'entrée (variables, cible, seuil) est écrit à l'entraînement dans `models/model_info.json` ; l'API le relit au démarrage.

## Conséquences
- **Facilite** : entraînement et prédiction très rapides, modèle léger chargé une seule fois en mémoire, résultats faciles à expliquer, probabilité directement comparable au seuil.
- **Rend plus difficile** : les relations non linéaires ou les interactions entre capteurs ne sont pas captées ; abaisser le seuil augmente les fausses alertes (précision de 0,622, donc environ 4 alertes sur 10 sont fausses).
- **À surveiller** : le rappel sur des données réelles (les données actuelles sont synthétiques) ; le choix du seuil avec l'atelier (coût d'une fausse alerte contre coût d'une panne manquée) ; comparer à une forêt aléatoire ou un gradient boosting si le rappel baisse en production.
