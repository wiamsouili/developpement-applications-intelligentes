# ADR 004 : Décision d'architecture et sélection du modèle de détection d'avaries MaintAI

**Statut :** Approuvé  
**Date :** 16/11/2026  
**Auteure :** ELAOUAZI Hafsa  
**Groupe :** G3  
**Système :** MaintAI  

---

## 1. Contexte du choix
Dans le déploiement opérationnel de la solution de maintenance prédictive MaintAI, l'utilisation conjointe de MLflow et de DVC a permis de mener un benchmark reproductible des modèles d'inférence. Le critère d'évaluation déterminant est le rappel (*recall*), afin de prévenir les ruptures de charge machine en milieu industriel.

## 2. Synthèse des runs tracés dans MLflow

| Algorithme / Paramétrage | Run ID MLflow | data_md5 DVC | Recall | Précision | Accuracy |
|---|---|---|:---:|:---:|:---:|
| Régression logistique ($C=1.0, \text{seuil}=0.3$) | `13f5d4e0e5d847118e95ca1b3f2c7f6c` | `73e0b7cb...` (v1) | 0.750 | 0.622 | 0.904 |
| Régression logistique ($C=0.01, \text{seuil}=0.3$) | `435762d000dd48419a472311ba0385c9` | `73e0b7cb...` (v1) | 0.691 | 0.653 | 0.908 |
| **Régression logistique ($C=1.0, \text{seuil}=0.2$)** | `41d5da4541464a129650109e2cdba029` | `73e0b7cb...` (v1) | **0.838** | 0.543 | 0.882 |
| Forêt aléatoire ($\text{seuil}=0.3$) | `e6b9c7c3f3ef4006aeaaa1a37540e951` | `73e0b7cb...` (v1) | 0.728 | 0.562 | 0.886 |
| Régression logistique étendu ($N=8000$) | `d7d569d95df14233b6a87af266105abc` | `93fdeef2...` (v2) | 0.741 | 0.650 | **0.916** |

## 3. Décision technique
Nous adoptons la **Régression Logistique avec abaissement du seuil d'alerte à 0.2** (Run MLflow `41d5da4541464a129650109e2cdba029`).

- **Justification :** Le rappel atteint **83,8 %**, maximisant le taux d'interception des défaillances réelles. Dans un atelier industriel, le coût induit par une intervention préventive inutile est négligeable comparativement au coût d'un arrêt de ligne non planifié.
- **Arbitrage :** La précision résultante de **54,3 %** est jugée tout à fait acceptable pour un système d'alerte précoce de premier niveau.
- **Forêt aléatoire non retenue :** Moins performante en rappel (72,8 %) tout en introduisant une opacité d'interprétation et une latence inutile.

## 4. Traçabilité
- **MLflow Run ID :** `41d5da4541464a129650109e2cdba029`
- **DVC Dataset Hash :** `73e0b7cb3c6f795c70c3ddf970b99c15` (commit `970e9f3`).
- **Reproductibilité logicielle :** `scikit-learn==1.8.0`, verrouillé dans l'artefact MLflow.
