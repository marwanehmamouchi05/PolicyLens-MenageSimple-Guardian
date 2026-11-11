# Synthèse d’ingénierie

Guardian réutilise un moteur déterministe existant, sans changer ses règles pour embellir les résultats. La version métier vérifiée est conservée séparément au checkpoint 13631a7. Ce dépôt neuf ne contient pas l’historique expérimental V9/V10, les modèles, données d’entraînement ni environnements privés.

La copie de publication ajoute seulement public_server.py : frontières HTTP, isolation et expiration des sessions, réinitialisation du seul navigateur courant, limites d’entrées / actions / connexions et cookies réservés à HTTPS. Le serveur local d’origine reste disponible. Les résultats Python incluent des tests qui démontrent qu’un navigateur ne voit pas les modifications d’un autre.

## Recherche séparée : mesure et choix de portée

Les comptes rendus archivés du 8 novembre pour Qwen3 8B indiquent :

| Expérience historique | Décisions exactes | Contrôles positifs connus |
|---|---:|---:|
| retained-v1 | 19/24 | 5/5 |
| coherent | 19/24 | 5/5 |

Le second candidat réduisait certains faux conflits, sans améliorer ce total de décisions exactes ; des faux positifs subsistaient. Les mesures sont des résultats de développement archivés, pas une précision indépendante de Guardian. Certains cas négatifs étaient revus par un agent ; ils ne doivent pas être décrits comme une annotation humaine indépendante authentifiée. Aucune nouvelle exécution ou formation de Qwen n’a eu lieu pour cette livraison. Aucun comparatif apparié n’a établi une supériorité de Guardian.

L’intérêt pour la candidature est le jugement : privilégier une application complète, inspectable et reproductible, dont les incertitudes sont explicites. L’IA a assisté l’implémentation et les matériaux de présentation ; les règles, preuves datées et décisions de revue restent visibles. Les décisions fictives de démonstration ne constituent pas une validation par MénageSimple.

## Répartition du code

- engine.py / typed.py : validation et comparaison conservatrices, quantités et calcul décimal.
- guardian.py : état, workflow et historique local.
- employer.py : distinction de rôles, comparaison de modèles génériques et spécifiques.
- new_information.py : deux types de saisies structurées, sans extraction de texte libre.
- report_fr.py / business_fr.py : rapports, libellés et qualifications françaises.
- server.py : usage local ; public_server.py : adaptateur de démonstration publique isolée.
- index.html / app.js / style.css : interface légère sans framework ni service tiers à l’exécution.

Les points restant à confirmer sont métier : modèle réservé, contrats, dates d’effet, assurances et exceptions. Le prototype n’est ni un système juridique, ni un moniteur général du site, ni un registre d’audit inviolable.
