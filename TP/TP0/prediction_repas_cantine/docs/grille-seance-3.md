# Séance 3 : grille de conception de CantineAI

**Groupe 3 :** SOUILI Wiam, ELAOUAZI Hafsa, YEKHLEF Aya, BELHACHMI Hajar

Cette grille reprend les sections 1 à 5 de l'étude de conception de CantineAI, les réglages de `config.py` qui en découlent et la réponse à la question finale. Le détail est développé dans `etude-de-conception.md` et `choix-modele.md`.

## 1. Sections 1 à 5

| Section | CantineAI |
|---|---|
| **1. Utilisateur principal** | Le gestionnaire de la cantine du lycée |
| **2. Décision et fréquence** | Choisir le nombre de repas à commander à la cuisine pour le lendemain, chaque jour d'école à 10 h (cinq fois par semaine) |
| **2. Coût d'une erreur** | Repas en trop : environ 15 DH de matière première jetés par repas, et du gaspillage, au détriment de la cantine. Repas manquant : un élève sans déjeuner ou un sandwich de remplacement acheté en urgence, et des plaintes de parents, au détriment des élèves, du gestionnaire et des parents. |
| **3. Approche** | ML de régression tabulaire (régression linéaire, arbre de décision, Random Forest, KNN). Pas plus simple : reprendre le chiffre de la semaine précédente ignore le menu, les examens, les sorties et les vacances (erreur moyenne de 79 repas sur le test, contre 23 pour le modèle retenu). Pas de deep learning (340 lignes) ni de LLM (pas de texte libre). |
| **4. Données** | `data/cantine_repas.csv` : données synthétiques générées pour le cours, licence non précisée, 340 jours d'école de septembre 2024 à juin 2026, une ligne par jour. Aucune donnée personnelle (effectifs agrégés). |
| **5. Baseline** | La reprise de la semaine précédente (méthode actuelle) : le chiffre du même jour, une semaine avant. Dans le code : `DummyRegressor(strategy="mean")`, qui prédit la moyenne des repas, et la méthode actuelle comme référence métier. |
| **5. Métrique principale** | MAE en repas : l'erreur moyenne, lisible par le gestionnaire. Chaque repas d'écart a un coût de l'ordre de 15 DH, proportionnel à l'écart. |
| **5. Critère d'acceptation** | Une MAE d'au plus 30 repas sur le jeu de test chronologique (68 derniers jours), et inférieure à la moitié de celle de la reprise de la semaine précédente sur les mêmes jours. |

Le critère contient bien une métrique (MAE), un nombre (30 repas), un jeu de données de mesure (les 68 derniers jours) et une condition (moins de la moitié de l'erreur de la méthode actuelle).

## 2. Réglages de `config.py`

| Réglage | CantineAI |
|---|---|
| `DATA_PATH` | `data/cantine_repas.csv` |
| `TARGET` | `repas_servis` |
| `TASK` | `regression` |
| `MAIN_METRIC` | `mae` |
| `SPLIT` | `chronologique` |
| `TIME_COLUMN` | `date` |

## 3. Question finale

**Pourquoi ne faut-il pas tirer les jours de test au hasard ?**

Le système doit prévoir demain à partir du passé. Un tirage au hasard place des jours du test au milieu de l'entraînement : le modèle voit la veille et le lendemain des jours qu'il doit prévoir. La colonne `repas_semaine_precedente` d'un jour de test est même la cible d'un jour d'entraînement, ce qui constitue une fuite d'information. Le test ne reproduit donc pas l'usage réel et donne des résultats trop optimistes. Mesure faite sur ce projet : avec un tirage au hasard, la MAE de la régression linéaire est de 18,3 repas, contre 22,2 en découpage chronologique ; pour la Random Forest, 24,1 contre 31,8. Le découpage chronologique garde les jours les plus récents pour le test.
