# Redémarrage HTTP — régression détectée pendant la publication

Le correctif d’affichage des essais a passé les 105 tests sur l’hôte, mais n’a pas répondu aux cinq premières sondes après redémarrage. La procédure a restauré la version précédente. Le service restauré est ensuite redevenu sain ; Nodum est resté accessible.

Le candidat démarrait comme nobody sur un port isolé. La classe HTTP désactivait SO_REUSEADDR, ce qui peut empêcher un redémarrage Linux immédiat après des connexions HTTP. La correction rétablit allow_reuse_address=True ; un test effectue une vraie requête, ferme le serveur et réutilise immédiatement le même port. Le délai de contrôle du script de publication est porté à 90 secondes pour la transition depuis l’ancien serveur et conserve le retour arrière automatique.

La correction a été vérifiée sur Linux : le redémarrage immédiat échoue sans réutilisation d’adresse et réussit avec elle. Les 106 tests locaux et les 106 tests sur l’hôte passent ; les 140 contrôles HTTPS de la livraison finale ont également réussi. Voir docs/validation/aws/deployment.json. Aucune configuration de Nodum ou règle réseau n’est modifiée.
