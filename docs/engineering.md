# Ingénierie et portée

Une application Python standard et une interface HTML/CSS/JavaScript sans dépendances applicatives. Les règles sont déterministes et inspectables ; aucun modèle, entraînement, API payante ou robot de collecte ne tourne à l’exécution.

Le moteur conserve les seuils numériques et le calcul Decimal. Le module d’impact ajoute un registre de valeurs, des liens calculés et un adaptateur explicite à l’état Guardian : les copies historiques et les nouvelles saisies prises en charge sont reflétées dans le graphe. Les citations originales sont préservées pendant les simulations ; la valeur de travail reste distincte de la valeur initiale.

Les cas métier de départ sont rédigés et sélectionnés manuellement. Le recalcul concerne les champs structurés reconnus, les relations et les états de simulation. L’outil ne déduit pas une nouvelle règle d’un texte libre. Les observations sans capture vérifiée restent qualifiées, y compris dans les exports.

## Frontières de la démonstration publique

Cookies HttpOnly, Secure et SameSite=Strict derrière HTTPS ; état privé par navigateur, expiration après 30 minutes d’inactivité. Limites de sessions, demandes, connexions, tailles et actions. Origine et hôte contrôlés. Citations non fiables échappées ou rendues comme texte. Réinitialisation limitée au visiteur courant. L’état public reste en mémoire et disparaît au redémarrage ; les décisions ne sont pas un journal permanent certifié.

## Fichiers principaux

- engine.py / typed.py : validation, comparaison et calculs.
- guardian.py / new_information.py : scénarios, saisies et décisions.
- employer.py / payment.py : qualifications métier et preuves contextualisées.
- impact_graph.py / impact_integration.py : registre, liens, impact, adaptateur et historique de session.
- business_fr.py / report_fr.py / impact_report_fr.py : présentation et exports français.
- server.py / public_server.py : mode local et démonstration publique isolée.
- app.js / navigation.js / impact.js / graph-explorer.js : interface et carte, une seule application.

## Usage de l’IA

L’IA a assisté la programmation, les vérifications et la préparation de présentation. Les tests et captures constituent les preuves vérifiables. Les décisions de démonstration ne sont pas des validations authentifiées par MénageSimple. La recherche locale Qwen est séparée et mise en pause ; elle n’est pas une fonction de Guardian et aucune précision générale issue de cette recherche n’est revendiquée.

Le prototype n’est ni un avis juridique, ni une surveillance exhaustive, ni un système connecté aux données clients. Les contrats, prestations et exceptions doivent être vérifiés par un responsable.
