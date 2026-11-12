# Publication sur le service AWS existant

Adresse : https://policylens.54-173-165-46.sslip.io/

Le service Guardian utilise l’hôte EC2 existant, Caddy pour HTTPS et Python standard. Aucun nouveau serveur, base, service payant ni route Nodum n’est nécessaire. Ne pas modifier la configuration de Nodum, arrêter ses conteneurs ou redémarrer l’hôte partagé.

## Procédure de mise à jour

`ops/release.sh COMMIT_SHA ARCHIVE_SHA256`, exécuté par l’administrateur sur l’hôte existant via AWS Systems Manager, vérifie l’archive GitHub du commit exact, extrait dans une nouvelle version, lance tous les tests Python, préserve l’ancienne cible et remplace atomiquement le lien current. Il redémarre uniquement `policylens-guardian.service`. Une erreur de santé déclenche le retour à l’ancienne version.

Ne pas utiliser cette procédure pour une première installation. Les chemins sont /opt/policylens-guardian/releases et /opt/policylens-guardian/current. Le service écoute sur 127.0.0.1:8889 et conserve PUBLIC_HOST ; LOCAL_PUBLIC_TEST reste absent.

## Retour arrière applicatif

Avant publication, cible effective vérifiée le 12 novembre : `/opt/policylens-guardian/releases/e67d425ed60b51402a1bc539d3d33f6c966fcdb3`. Le dépôt distant précédent est `02d01073622204b710fafc819f68d1c7707ed2af`, préservé dans l’historique et un tag de rollback.

Pour restaurer cette cible, créer un nouveau lien temporaire vers ce répertoire, le déplacer atomiquement sur current puis redémarrer uniquement Guardian. Ne pas modifier Caddy ou le minuteur d’expiration ; ne pas arrêter Nodum. Le script conserve aussi la cible effective dans rollback-COMMIT.txt.

## Isolement et disponibilité

Exécution comme nobody, fichiers protégés, répertoire Nodum inaccessible au service, réseau sortant bloqué sauf loopback, 160 Mio de mémoire maximum, 25 % d’un cœur et 40 tâches. Cookies HTTPS et sessions temporaires propres à chaque navigateur. Aucun accès aux réservations ou données clients.

Le contrôle préalable du 12 novembre a retrouvé Guardian actif, Nodum sain et Nodum HTTPS 200. Commande SSM : 659d2090-723b-4c17-a6a1-70d7cd245f01, succès. Ces éléments précèdent la nouvelle publication ; ses résultats sont enregistrés séparément.

L’expiration demeure le **12 décembre 2026 à 23:00 UTC**, soit le **13 décembre à 00:00 au Maroc**, fin de journée autorisée du 12 décembre. Seul Guardian s’arrête. L’autorisation de coût reste au maximum 25 USD bruts ; aucun nouveau poste fixe n’est provisionné et le budget AWS ne constitue pas un plafond dur. Les détails de facturation restent privés.
