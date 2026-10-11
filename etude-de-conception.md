# Étude de conception – Prédiction du retard de livraison (Olist)

**Groupe :** SOUILI Wiam  – ELAOUAZI Hafsa  – YEKHLEF Aya – BELHACHMI Hajar 
**Version :** Brouillon  
**Date :** 11/10/2026


## 1. Contexte et utilisateurs

- Organisation ou situation : une marketplace e-commerce brésilienne de type Olist, qui met en relation de petits vendeurs et des clients, la livraison étant assurée par des transporteurs. À l'achat, le client reçoit une date de livraison estimée. Sur les commandes livrées du jeu de données, **6,8 % arrivent après cette date** (6 534 sur 96 470), ce qui dégrade l'expérience client et génère des réclamations.
- Utilisateur principal (un rôle précis) : le **responsable logistique / opérations** de la marketplace, chargé de suivre les livraisons et de traiter les commandes problématiques.

## 2. Problème et décision

- Décision que l'utilisateur prend avec le système : pour chaque nouvelle commande, décider s'il la **signale « à risque de retard »** et déclenche une action : repousser la date promise affichée au client, relancer le vendeur ou le transporteur, prévenir le client de façon proactive. Le système fournit aussi un **délai de livraison prévu en jours** pour proposer une date plus réaliste.
- Fréquence : à chaque commande, soit plusieurs centaines par jour (environ 6 500 commandes par mois sur 2018). Les commandes à risque sont revues chaque jour.
- Conséquence d'une erreur, et pour qui :
  - **Faux négatif** (retard non détecté) : le client reçoit son colis en retard sans avoir été prévenu, avec risque de réclamation, de mauvaise évaluation et de perte de confiance. Le coût retombe sur le client et sur la marketplace.
  - **Faux positif** (alerte inutile) : temps opérateur perdu et date promise repoussée pour rien, ce qui peut réduire l'attractivité de l'offre. Le coût retombe sur l'équipe logistique et la marketplace.
  - Comme les retards sont rares, un faux positif coûte peu, alors qu'un retard manqué coûte plus cher : on privilégie le **rappel** de la classe « retard », sous contrainte de précision minimale.

## 3. Approche par sous-problème

| Sous-problème | Approche (règles / ML / DL / LLM / RAG) | Pourquoi pas une approche plus simple |
|---|---|---|
| Définition de la cible et nettoyage (commandes livrées, dates incohérentes, exclusion de 2016) | Règles (pandas, jointures entre tables) | Déjà déterministe, le ML n'apporte rien ici |
| Construction des variables connues à l'achat (poids, volume, frais de port, États, mois, délai estimé, **distance vendeur-client** via la géolocalisation) | Règles et calculs (agrégation par code postal, distance haversine) | Calcul direct, sans apprentissage |
| Classification : retard oui/non | ML : régression logistique (baseline) puis gradient boosting (LightGBM / XGBoost) | Une règle simple comme « vendeur et client dans des États différents » est trop grossière (8,0 % de retard contre 4,5 % si même État). Les données sont tabulaires, donc le DL n'est pas justifié. |
| Régression : délai de livraison en jours (`delivery_days`) | ML : régression linéaire (baseline) puis gradient boosting | La date estimée par Olist seule a une MAE d'environ 13 jours (elle est volontairement prudente), et une prédiction constante environ 6,2 jours |
| Déséquilibre des classes et choix du seuil | `class_weight='balanced'` ou SMOTE (train uniquement) et réglage du seuil de décision | Sans traitement, un modèle qui prédit toujours « à l'heure » atteint 93 % d'accuracy sans rien détecter |
| Explicabilité des prédictions | SHAP sur le modèle final | Le responsable logistique doit comprendre pourquoi une commande est signalée |

Pas de LLM ni de RAG : le problème repose sur des données tabulaires, sans texte à exploiter. Les avis clients sont écartés, car ils sont postérieurs à la livraison (fuite de données).

## 4. Données

| Jeu de données | Source et licence | Volume | Données personnelles ? |
|---|---|---|---|
| Brazilian E-Commerce Public Dataset by Olist, 9 fichiers CSV dont 6 utilisés (commandes, articles, produits, clients, vendeurs, géolocalisation) | Kaggle, `olistbr/brazilian-ecommerce` : https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce. Licence : CC BY-NC-SA 4.0 (à vérifier sur la page Kaggle) | 99 441 commandes (2016-2018), dont 96 470 livrées avec date de livraison exploitable. 112 650 lignes d'articles, environ 126 Mo | Pas de données directement identifiantes : identifiants clients et vendeurs pseudonymisés (hash), codes postaux tronqués à 5 chiffres, pas de noms ni d'adresses |
| Fichiers non utilisés : avis clients, paiements | Idem | Avis : 14 Mo ; paiements : 6 Mo | Les avis contiennent du texte libre, d'où leur exclusion (fuite de données et données plus sensibles) |

Limites connues : pas de données transporteur, météo ni jours fériés. 2016 est quasi vide. Le retard varie fortement selon la période (12 % en novembre 2017, 19 % en mars 2018, 1 % en juin 2018).

## 5. Métriques, baseline et critères d'acceptation

- Baseline et son résultat :
  - Classification, baseline naïve (toujours « pas de retard ») : accuracy 93 %, mais rappel nul, donc inutile.
  - Classification, premier modèle (gradient boosting, variables simples, split temporel 80/20 par date) : AUC 0,68, PR-AUC 0,063 (taux de base 0,035), F1 ≈ 0,10, rappel 45 %, précision 6 %. Avec un split aléatoire stratifié, on obtient AUC 0,79 et PR-AUC 0,25, mais ce score est gonflé par la fuite temporelle : la référence retenue est le split temporel.
  - Régression, prédiction constante (médiane ou moyenne) : MAE ≈ 6,2-6,4 jours. Premier modèle (gradient boosting) : MAE 4,3 jours en split temporel (R² 0,06) et 4,8 jours en split aléatoire (R² 0,35).
- Métrique principale et pourquoi :
  - Classification : **PR-AUC**, accompagnée du rappel et du F1 sur la classe « retard ». La classe est rare, donc l'accuracy est trompeuse et l'AUC-ROC trop optimiste.
  - Régression : **MAE en jours**, lisible par le responsable logistique et moins sensible que le RMSE aux livraisons extrêmes (jusqu'à 209 jours).
- Critères d'acceptation (un nombre, un jeu de données, une condition), à confirmer après ajout de la distance vendeur-client :
  - Classification : **PR-AUC ≥ 0,12** sur le jeu de test temporel (les 20 % de commandes les plus récentes), avec un rappel ≥ 40 % à précision ≥ 10 %.
  - Régression : **MAE ≤ 4,0 jours** sur le même jeu de test, c'est-à-dire au moins 35 % mieux que la prédiction constante.


