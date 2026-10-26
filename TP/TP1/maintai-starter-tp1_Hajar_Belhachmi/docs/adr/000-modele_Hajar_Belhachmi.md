# ADR 000 : Choix du modèle de prédiction de panne (régression logistique, seuil à 0,3)

Date : 26/10/2026 · Auteurs : Hajar Belhachmi

## Contexte
MaintAI doit estimer, à partir de quatre relevés de capteurs (température, vibration, charge, heures de fonctionnement), la probabilité qu'une machine tombe en panne. Les pannes sont rares (environ 14 % des relevés), donc une panne manquée coûte beaucoup plus cher qu'une fausse alerte, et le modèle doit être servi par une API qui répond vite et qui reste facile à expliquer à des techniciens de maintenance.

## Options étudiées
1. **Baseline « toujours pas de panne » (`DummyClassifier`)** : très simple et sert de point de comparaison, mais elle ne détecte aucune panne (rappel de 0), donc elle est inutile en pratique malgré une exactitude de 86,4 %.
2. **Régression logistique avec `StandardScaler`** : rapide à entraîner et à charger, fournit directement une probabilité, et ses coefficients sont interprétables (on voit quelle variable pèse le plus). Elle ne capture que des relations linéaires, ce qui peut limiter la précision si les interactions entre variables sont fortes.
3. **Modèle à base d'arbres (forêt aléatoire, gradient boosting)** : capture des relations non linéaires et des interactions, mais le modèle est plus lourd, moins lisible, et plus long à charger. Il demande aussi plus de réglages, sans bénéfice démontré sur ces données (le risque y est construit comme une combinaison linéaire des variables).

## Décision
Nous retenons la **régression logistique précédée d'un `StandardScaler`**, regroupés dans un seul `Pipeline` sauvegardé avec `joblib`, avec un **seuil de décision à 0,3** au lieu de 0,5. La raison principale est la contrainte métier : les pannes sont rares et coûteuses, donc on privilégie le rappel, et abaisser le seuil permet de détecter plus de pannes au prix de quelques fausses alertes. Sur le jeu de test (1 000 relevés), le modèle obtient un rappel de 0,75, une précision de 0,622 et une exactitude de 0,904, contre un rappel de 0 et une exactitude de 0,864 pour la baseline.

## Conséquences
- **Facilite** : un entraînement et un chargement rapides au démarrage de l'API, une probabilité directement exploitable, et un prétraitement qui ne peut pas être oublié puisqu'il est dans le pipeline sauvegardé. Le seuil est un paramètre (`MAINTAI_THRESHOLD`), donc on peut l'ajuster sans réentraîner.
- **Rend plus difficile** : le modèle ne gère pas les relations non linéaires. Avec un seuil de 0,3, environ 4 alertes sur 10 sont de fausses alertes (précision de 0,622), ce qui peut fatiguer les équipes.
- **À surveiller** : le rappel et la précision au fil du temps, notamment si les données réelles remplacent les données synthétiques (les performances actuelles ne le garantissent pas). Il faudra aussi comparer avec un modèle à base d'arbres si le rappel devient insuffisant, et vérifier que la version de scikit-learn utilisée pour charger le modèle est la même qu'à l'entraînement (elle est enregistrée dans `model_info.json`).
