# ADR 002 : Validation des entrées et comportement si le modèle est absent

Date : 26/10/2026 · Auteurs : Wian Souili

## Contexte
L'API MaintAI reçoit des relevés de capteurs envoyés par d'autres programmes (tableau de bord, application mobile, système de l'atelier). Une valeur impossible (500 °C) ne doit jamais atteindre le modèle, et l'API doit réagir proprement quand le fichier du modèle n'a pas été produit par l'entraînement.

## Options étudiées

### Décision A : les bornes de chaque variable
1. **Bornes copiées sur les données (min/max de `sensors.csv`)** : simples à calculer, mais elles reflètent un jeu de données synthétique ; une machine réelle un peu plus chaude, plus chargée ou plus ancienne serait refusée à tort (faux 422).
2. **Bornes physiques** : ce qu'un équipement réel peut afficher. Elles rejettent les valeurs absurdes (capteur défaillant) sans refuser les cas extrêmes mais réels, qui sont justement ceux à risque.

### Décision B : modèle absent
1. **Démarrer quand même et répondre 503** : l'API reste en ligne, `/health` indique `model_loaded: false`, les clients reçoivent un message clair ; en revanche le défaut n'est pas bloquant pour l'orchestrateur, qui peut croire le service sain.
2. **Refuser de démarrer** : échec visible immédiatement (« fail fast »), aucun risque de service à moitié fonctionnel ; en revanche, plus aucun endpoint ne répond (pas de `/health`, pas de `/docs`), ce qui complique le diagnostic et coupe aussi les routes qui n'ont pas besoin du modèle.

## Décision
**A : bornes physiques.**

| Variable | Min | Max | Justification |
|---|---|---|---|
| `temperature_c` | -40 | 150 | Plage industrielle usuelle ; au-delà de 150 °C l'isolation d'un moteur (classes F/H) est détruite : valeur de capteur défaillant. |
| `vibration_mm_s` | 0 | 50 | Vitesse efficace, jamais négative ; la zone « danger » des normes ISO 10816/20816 commence vers 11 à 18 mm/s, 50 laisse une large marge. |
| `load_pct` | 0 | 120 | 0 % à vide ; surcharge temporaire possible jusqu'à ~120 % de la charge nominale. |
| `runtime_hours` | 0 | 100000 | Jamais négatif ; une machine industrielle dure ~10 ans en continu (~ 90 000 h). |

Tous les champs sont des `float` (15000,5 heures doit être accepté) et le schéma refuse les champs inconnus (`extra="forbid"`).

**B : démarrer et répondre 503.** L'API reste disponible, `/health` signale `model_loaded: false`, et `/v1/predict` répond 503 avec un message qui dit quoi faire (lancer `python -m maintai.train`). Le 503 exprime exactement la situation : requête valide, service temporairement indisponible, et non pas un bug (500).

## Conséquences
- **Facilite** : l'API est documentée (`/docs`) et diagnostiquable même sans modèle ; les clients distinguent une erreur de leur part (422) d'une indisponibilité du service (503).
- **Perd** :
  - Bornes physiques : un relevé aberrant mais dans les bornes (ex. 140 °C avec une vibration nulle) est accepté ; la validation ne détecte pas l'incohérence entre variables.
  - 503 plutôt que refus de démarrer : une erreur de déploiement (modèle oublié) n'est pas bloquante et peut passer inaperçue si personne ne surveille `/health` ; refuser de démarrer l'aurait rendue immédiatement visible.
- **À surveiller** : ajouter une supervision de `/health` (alerte si `model_loaded` est faux) ; réévaluer les bornes avec des données réelles et un technicien de maintenance ; passer à `/v2` si le contrat des champs change.
