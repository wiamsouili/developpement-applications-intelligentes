# ADR 000 : [titre de la décision]

Date : [26/10/2026] · Auteurs : [EL AOUAZI]

## Contexte
Dans MaintAI, l’API reçoit des valeurs provenant des capteurs avant de les transmettre au modèle de prédiction. Des valeurs incohérentes ou l’absence du modèle peuvent empêcher une prédiction fiable ; il faut donc définir comment l’API doit réagir dans ces cas.

## Options étudiées
1. - Valider les mesures dès leur réception et refuser les valeurs hors limites. Cela évite de transmettre au modèle des données manifestement invalides et rend les erreurs visibles pour le client. En revanche, les limites doivent être définies et maintenues correctement.
2. - Accepter les valeurs sans contrôle strict et laisser le modèle les traiter. Cette solution demande moins de validation au départ, mais elle risque de produire des prédictions peu fiables ou des erreurs difficiles à diagnostiquer.

Pour le modèle indisponible, deux comportements sont
 également possibles : arrêter le démarrage de l’API tant que le modèle n’est pas chargé, ou démarrer l’API et retourner une erreur explicite lorsqu’une prédiction est demandée.

## Décision
J’ai choisi de vérifier les mesures avec un schéma Pydantic et de définir des limites pour chaque champ : température, vibration, taux de charge et heures de fonctionnement. Si une valeur ne respecte pas les contraintes, l’API la rejette avec une erreur HTTP 422. Si le modèle n’est pas disponible au moment de la prédiction, l’API retourne 503 Service Unavailable, avec un message explicite.

## Conséquences
Cette approche permet de repérer rapidement les données invalides et de distinguer une erreur de saisie d’une indisponibilité du service de prédiction. Elle demande de choisir des limites physiques adaptées au matériel réel et de les ajuster si les besoins changent. Il faudra aussi vérifier que le modèle est correctement chargé et tester les réponses HTTP, notamment les cas valides, les valeurs hors limites et le modèle absent.
