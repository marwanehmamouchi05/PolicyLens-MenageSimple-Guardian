# Validation de publication

La suite Python de cette copie a été exécutée : 58 cas réussis. Le journal validation-python.txt en donne le détail. Le contrôle de cookie a ensuite été répété après adoption du préfixe __Host- pour HTTPS et a réussi. La syntaxe JavaScript a été vérifiée.

La version métier précédente avait passé 64 assertions de navigateur. Ces résultats historiques ne seront pas confondus avec les contrôles de la copie publique ni avec une acceptation du véritable domaine AWS.

Les captures de assets/screenshots représentent l’application réelle vérifiée localement, pas un déploiement AWS. La livraison doit remplacer ou compléter ces captures par des preuves distantes après publication effective du service.

Contrôles ajoutés pour Internet : sessions séparées, réinitialisation privée, cookie HttpOnly / SameSite / Secure, refus d’origine externe et de fichiers internes, limite de requêtes. Le code ne consulte pas d’URL saisie, n’appelle pas de modèle et ne conserve pas d’état sur disque en mode public.

Aucune mesure nouvelle de précision Qwen ni comparaison de performance n’a été exécutée ici. Aucun crédit, coût nul ou résultat de déploiement n’est déduit d’un simple build local.
