# Choix du modèle · Détection prédictive des pannes industrielles

**Date :** 26/10/2026 · **Groupe :** G3  
**Auteure :** YEKHLEF Aya

---

## 1. Contexte et Objectif

L'objectif de cette étude est d'évaluer et de sélectionner le modèle d'apprentissage supervisé le plus pertinent pour anticiper les défaillances d'équipements industriels à partir de mesures de capteurs physiques.

* **Nature du problème :** Classification binaire. La variable cible `failure` vaut :
  * `0` : fonctionnement nominal (machine saine).
  * `1` : incident mécanique ou défaillance imminente.
* **Enjeu industriel :** Une panne non anticipée stoppe net la chaîne de montage, entraînant des pertes économiques considérables et des risques humains. Une fausse alerte, en comparaison, ne coûte qu'un contrôle de maintenance planifié. La métrique décisionnelle prioritaire est donc le **rappel (*recall*)**, complétée par la précision et le F1-score pour éviter la saturation des équipes terrain.

---

## 2. Données et Protocole Expérimental

* **Source des données :** `data/exemple_pannes.csv` comprenant 5 000 observations sans aucune valeur manquante.
* **Variables prédictives (4 capteurs) :**
  * `temperature_c` : Température interne du moteur (°C).
  * `vibration_mm_s` : Vitesse vibratoire RMS (mm/s).
  * `load_pct` : Pourcentage de charge mécanique (%).
  * `runtime_hours` : Heures de fonctionnement cumulées (h).
* **Déséquilibre des classes :**
  * 4 122 observations saines (82,4 %).
  * 878 observations avec défaillance (17,6 %).
* **Protocole de validation :**
  * Découpage 80 % entraînement (4 000 échantillons) et 20 % test (1 000 échantillons).
  * Échantillonnage aléatoire stratifié (`seed=42`) pour conserver la proportion exacte de pannes dans le jeu de test (176 pannes réelles).
  * Pipeline scellé avec imputation médiane de précaution et centrage-réduction (`StandardScaler`) ajusté strictement sur le jeu d'entraînement pour bannir toute fuite d'information (*data leakage*).

---

## 3. Résultats Comparatifs sur le Jeu de Test

| Algorithme | Accuracy | Rappel (*Recall*) | Précision | F1-Score |
|---|:---:|:---:|:---:|:---:|
| **Baseline (Majoritaire)** | 0,824 | 0,000 | 0,000 | 0,000 |
| **Régression Logistique** | **0,889** | 0,574 | **0,737** | **0,645** |
| **Arbre de Décision** | 0,839 | **0,597** | 0,538 | 0,566 |
| **Forêt Aléatoire (*Random Forest*)** | 0,873 | 0,545 | 0,671 | 0,602 |
| **K-Plus Proches Voisins (*KNN*)** | 0,878 | 0,540 | 0,699 | 0,609 |

---

## 4. Analyse et Discussion

1. **La fausseté de l'exactitude de la baseline :**
   Le classifieur majoritaire affiche une exactitude de 82,4 % simplement en prédisant systématiquement « 0 ». Cependant, son rappel est de 0 % : il laisse passer 100 % des pannes réelles. Dans un environnement industriel critique, l'exactitude globale est un piège et ne peut pas servir de critère unique.
2. **Arbre de décision :**
   Il atteint le rappel brut le plus élevé par défaut (0,597), mais au détriment d'une précision dégradée (0,538) : près d'une alerte sur deux est fausse, ce qui engendre une défiance des techniciens face aux alarmes intempestives. De plus, il est sujet au surapprentissage.
3. **Modèles ensemblistes et à mémoire (Random Forest & KNN) :**
   Le Random Forest et le KNN offrent de bons scores globaux (F1 > 0,60), mais leurs rappels restent inférieurs à la régression logistique et à l'arbre, tout en imposant une surcharge de calcul et une complexité de déploiement plus élevée.
4. **Régression logistique :**
   Elle obtient la meilleure exactitude (88,9 %), la meilleure précision (73,7 %) et le meilleur score F1 (0,645). Avec le seuil conventionnel de 0,5, son rappel est de 0,574.

---

## 5. Décision Métier Retenue

Nous retenons la **Régression Logistique standardisée**, combinée à un **ajustement opérationnel du seuil de décision à 0,3** (au lieu de 0,5) :
* **Justification technique et métier :** La régression logistique fournit directement une probabilité bien calibrée de panne $P(\text{panne} \mid X)$. En abaissant le seuil d'intervention à 0,3, le rappel grimpe à **0,750** (détectant ainsi 3 pannes sur 4), tout en conservant une précision très satisfaisante de **62,2 %**.
* **Interprétabilité et Déploiement :** Les coefficients sont immédiatement compréhensibles pour l'ingénieur de maintenance (la charge et la température étant les variables les plus prédictives). Le modèle s'exécute en une fraction de milliseconde sous FastAPI, assurant une intégration optimale en production.

---

## 6. Limites et Recommandations

* **Absence d'historique chronologique :** Les données ne comportent pas de variable temporelle continue permettant de mesurer l'effet de fatigue cyclique.
* **Conditions hors distribution :** Si de nouvelles machines fonctionnant à des vitesses ou charges supérieures sont ajoutées au parc, le modèle devra être réétalonné avec détection active de dérive de distribution.
