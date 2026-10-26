# ADR 000 : Chargement du modèle de prédiction au démarrage de l’API

Date : 26/10/2026 · Auteurs : Wiam Souili

## Contexte

L’API MaintAI doit utiliser un modèle de Machine Learning sauvegardé dans `models/model.joblib` afin de prédire le risque de panne à partir des données des capteurs.

Comme l’API peut recevoir plusieurs requêtes de prédiction, il faut décider si le modèle doit être chargé depuis le disque à chaque requête ou une seule fois au démarrage de l’application.

## Options étudiées

1. Charger le modèle à chaque requête** : cette solution est simple à comprendre et permet de relire le modèle à chaque prédiction. En revanche, elle augmente le temps de réponse et effectue inutilement plusieurs chargements du même modèle depuis le disque.

2. Charger le modèle une seule fois au démarrage de l’API** : cette solution permet de conserver le modèle en mémoire et de le réutiliser pour toutes les requêtes. Elle améliore les performances et évite les chargements répétitifs. En revanche, si le fichier du modèle est modifié pendant que l’API fonctionne, il faut redémarrer ou recharger l’application pour prendre en compte la nouvelle version.

## Décision

Nous avons choisi de **charger le modèle une seule fois au démarrage de l’API**, à l’aide du mécanisme `lifespan` de FastAPI.

Le modèle est chargé avec :

```python id="0ypp9u"
state["predictor"] = Predictor.load(get_settings())
```

puis il est conservé dans `state` afin d’être réutilisé par l’endpoint `/v1/predict`.

Cette solution a été retenue principalement pour éviter de charger le modèle depuis le disque à chaque requête et ainsi réduire le temps nécessaire pour effectuer une prédiction.

Si le modèle n’est pas disponible au démarrage, l’API peut tout de même démarrer et conserve :

```python id="qk77c4"
state["predictor"] = None
```

Dans ce cas, une demande de prédiction retourne un code HTTP `503 Service Unavailable`.

## Conséquences

Cette décision facilite les prédictions successives, car le modèle est déjà chargé en mémoire lorsque l’API reçoit une requête. Elle permet également de limiter les accès au disque et d’améliorer le temps de réponse de l’API.

En revanche, une nouvelle version du modèle enregistrée sur le disque ne sera pas automatiquement utilisée par l’API déjà en cours d’exécution. Il faudra prévoir un redémarrage ou un mécanisme de rechargement si le modèle doit être mis à jour.

Il faudra également surveiller le chargement du modèle au démarrage. Si celui-ci est absent ou impossible à charger, l’endpoint de prédiction doit rester indisponible et retourner le code HTTP `503`.
