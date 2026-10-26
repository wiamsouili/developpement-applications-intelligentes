# Étude de conception · Système prédictif de détection des pannes industrielles

**Auteure :** YEKHLEF Aya · **Groupe :** G3  
**Projet :** MaintAI · **Version :** 2.0 · **Date :** 26/10/2026

---

## 1. Contexte Opérationnel et Utilisateurs

* **Utilisateur Principal :** Ingénieur en maintenance industrielle responsable de la disponibilité des lignes et de la planification des arrêts techniques.
* **Utilisateurs Secondaires :**
  * Techniciens de maintenance de terrain (exécutent les inspections préventives et les réparations mécaniques).
  * Responsables d'atelier / chefs de production (arbitrent la charge de production et les cadences machines).
* **Environnement Métier :** Les machines tournantes sont soumises à de fortes contraintes mécaniques et thermiques. Une charge excessive ou prolongée accélère l'usure des roulements, amplifie les vibrations et élève la température interne. L'anticipation prédictive des ruptures permet de basculer d'une maintenance corrective d'urgence subie à une maintenance prédictive planifiée.

---

## 2. Définition du Problème et Processus Décisionnel

* **Problématique :** Comment anticiper avec fiabilité l'imminence d'une rupture machine à partir de la télémétrie conjointe des capteurs de charge (`load_pct`), de température (`temperature_c`), de vibration (`vibration_mm_s`) et d'heures cumulées (`runtime_hours`) ?
* **Décision assistée :**
  * Classifier chaque équipement selon son niveau de criticité : *Vert* (fonctionnement normal), *Orange* (surveillance rapprochée), *Rouge* (intervention prioritaire immédiate sous 24h).
* **Temporalité et Fréquence :**
  * Ingestion continue des relevés télémétriques.
  * Inférence et calcul du score de défaillance actualisé toutes les minutes par l'API REST.
* **Matrice des Coûts d'Erreur :**
  * **Faux Négatif (Panne non détectée) :** Impact critique. Rupture brutale d'arbre ou casse moteur en pleine production. Arrêt d'urgence de la chaîne, pertes de production horaires chiffrées en milliers d'euros, coûts de réparation majeurs et risques d'accidents du travail.
  * **Faux Positif (Fausse alerte) :** Impact mineur à modéré. Déplacement d'un technicien pour un contrôle préventif non indispensable (vérification de lubrification ou thermographie). Coût maîtrisé sans arrêt de production.

---

## 3. Décomposition par Sous-Problèmes et Choix Technologiques

| Sous-Problème | Solution Retenue | Justification face à une approche plus simple |
|---|---|---|
| **Contrôle et validation des entrées** | Validation par schéma strict (Pydantic) | Des règles programmatiques simples et déterministes suffisent pour rejeter les valeurs physiquement absurdes (ex: température < -40°C ou > 150°C). |
| **Prétraitement des données** | Pipeline Scikit-Learn (`StandardScaler`) | Les modèles linéaires et les métriques de distance requièrent une standardisation stricte sans fuite d'information (*leakage*). |
| **Estimation du risque de défaillance** | Régression Logistique avec seuil à 0,3 | Une simple règle de seuil univariée (ex: alerte si T > 80°C) échoue à capturer les interactions combinées. La régression logistique pondère adéquatement chaque facteur tout en restant hautement explicable et légère. |
| **Exposition du service** | API REST haute performance (FastAPI + Uvicorn) | Standardisation HTTP universelle permettant à n'importe quel automate d'atelier ou dashboard web d'interroger le service avec une latence < 10 ms. |
| **Génération des alertes** | Règle de seuillage probabiliste ($P > 0,3$) | La logique de bascule est déterministe, auditable et directement configurable par variable d'environnement (`MAINTAI_THRESHOLD`). |

---

## 4. Données et Gouvernance

| Jeu de données | Source & Licence | Volume | Données Personnelles / RGPD |
|---|---|---|---|
| **Télémétrie d'atelier** (`sensors.csv` / `exemple_pannes.csv`) | Données synthétiques et industrielles d'équipements mécaniques | 5 000 observations tabulaires, 4 variables prédictives, 1 cible binaire | **Aucune donnée personnelle** (aucune donnée nominative, biométrique ou de géolocalisation d'opérateur). |

---

## 5. Analyse du Besoin Métier et Métriques d'Évaluation

1. **Priorité absolue au Rappel (*Recall*) :**
   En raison de l'asymétrie extrême du coût des erreurs industrielles, l'algorithme doit maximiser la détection des vrais incidents positifs. Un rappel minimal cible de **0,75 (75 %)** est requis par le cahier des charges.
2. **Contrôle de la Précision :**
   Un rappel de 100 % obtenu en déclenchant des alarmes permanentes provoquerait l'effet « Pierre et le loup » et le rejet du système par les techniciens. Un plancher de précision de **60 %** est fixé pour garantir la crédibilité opérationnelle des alertes.
3. **Seuil opérationnel à 0,3 :**
   Le passage du seuil théorique de 0,5 à 0,3 permet d'atteindre exactement ce compromis optimal (**Rappel = 75,0 %**, **Précision = 62,2 %**).

---

## 6. Architecture Cible et Perspectives

* **Architecture logicielle :** 
  * Microservice conteneurisé exposé en API REST (`/health` et `/v1/predict`).
  * Architecture découplée : le service web charge le modèle scikit-learn au démarrage (`lifespan`) pour éliminer la latence disque en production.
* **Perspectives et Évolution :**
  * Intégration d'un module de surveillance du *data drift* pour détecter les changements de distribution des capteurs au cours des saisons.
  * Enrichissement temporel futur (fenêtrage glissant sur les séries temporelles pour analyser la dynamique d'accélération des vibrations).
