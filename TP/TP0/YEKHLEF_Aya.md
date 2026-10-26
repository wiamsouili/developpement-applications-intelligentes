# TP0 : MaintAI

**Nom :** YEKHLEF Aya · **Groupe :** G3

## Le problème
Dans un contexte industriel de maintenance prédictive, l'objectif est d'anticiper les défaillances mécaniques critiques à partir des relevés télémétriques de 4 capteurs : la température (	emperature_c), la vitesse de vibration (ibration_mm_s), le taux de charge (load_pct) et les heures de fonctionnement cumulées (
untime_hours). 
Sur une chaîne de fabrication, une panne non détectée (faux négatif) provoque l'arrêt immédiat et imprévu de toute la ligne de production, générant des coûts financiers massifs et des risques de casse matérielle, tandis qu'une fausse alerte (faux positif) n'entraîne qu'une vérification préventive par un technicien. Le rappel (*recall*) constitue donc la métrique prioritaire.

## Résultats sur le jeu de test

| Modèle | Accuracy | Rappel | Précision |
|---|---|---|---|
| baseline | 0.824 | 0.000 | 0.000 |
| régression logistique | 0.889 | 0.574 | 0.737 |

## Mon choix, et pourquoi
J'ai retenu la **régression logistique précédée d'une standardisation (StandardScaler)**.
- **Inutilité absolue de la baseline :** Bien qu'elle affiche une accuracy apparemment élevée de 82,4 % (liée au déséquilibre naturel des classes où 82,4 % des machines sont saines), son rappel est de **0,000**. Elle ne détecte strictement aucune défaillance, ce qui la rend totalement inopérante.
- **Régression logistique :** Elle surpasse la baseline sur l'ensemble des indicateurs (accuracy de 88,9 %, rappel de 57,4 %, précision de 73,7 %). Elle offre un excellent compromis entre performance, robustesse numérique et temps d'exécution quasi-instantané. De plus, ses coefficients linéaires sont directement interprétables par les équipes de maintenance, permettant de quantifier l'impact exact de chaque capteur dans l'élévation du risque.

## Le critère (rappel >= 0,75) est-il atteint ?
**Non, le critère initial de rappel >= 0,75 n'est pas atteint avec le seuil standard de 0,5.** 
Avec le seuil de décision par défaut (0,5), la régression logistique n'atteint qu'un rappel de **0,574**, ce qui signifie que 42,6 % des pannes réelles ne sont pas anticipées. 

*Cependant, ce résultat reste tout à fait valable et explicable :*
Le modèle probabiliste calcule une estimation continue du risque. Pour atteindre et dépasser le seuil d'exigence métier de 0,75 en rappel, la solution consiste à **abaisser le seuil de classification opérationnel à 0,3** (comme démontré dans la suite du TP). Cette décision permet de capturer 75 % des pannes réelles au prix d'une légère baisse de précision, arbitrage parfaitement conforme aux contraintes économiques de l'atelier.

## Ce qui reste flou
- **La granularité temporelle :** Le fichier de données ne disposant pas d'horodatage fin, il reste à définir précisément l'horizon temporel réel couvert par une prédiction positive (la panne est-elle imminente dans l'heure ou dans les prochaines 24 heures ?).
- **La robustesse aux dérives (data drift) :** Comment le modèle se comportera-t-il lorsque les machines vieilliront et que la distribution conjointe charge/température évoluera en exploitation réelle ?
