# Déploiement AWS effectivement réalisé — 11 novembre 2026

Application : https://policylens.54-173-165-46.sslip.io/

## Installation

EC2 existant, région us-east-1, avec HTTPS Caddy et adresse publique déjà utilisés par Nodum. Aucune nouvelle instance, adresse IP, base de données, connexion App Runner ou fonction Lambda créée. Le site Nodum reste accessible ; sa configuration initiale a été sauvegardée avant ajout d’un second hôte virtuel. Aucun accès à sa base de données ou à ses secrets.

App Runner n’a pas été utilisé : le service n’accepte plus de nouveaux clients depuis le 30 avril 2026. Voir la [documentation officielle](https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html). La configuration App Runner conservée dans le dépôt est historique et n’est pas le déploiement réel.

Version installée : e67d425ed60b51402a1bc539d3d33f6c966fcdb3. Archive GitHub vérifiée avec SHA-256 : 01a6dee89adf154de83539e9f7cb83ffe4d6fae2941f23decfb4333e0adb0f3e. Les commits documentaires suivants ne sont pas déployés automatiquement.

Service systemd policylens-guardian.service ; Python 3.9.25 sans dépendance ajoutée. Répertoire /opt/policylens-guardian, versions sous releases, lien current. BIND_HOST=127.0.0.1, PORT=8889, PUBLIC_HOST=policylens.54-173-165-46.sslip.io. LOCAL_PUBLIC_TEST absent. Caddy assure TLS valide et redirection HTTP vers HTTPS. Port applicatif accessible seulement sur loopback.

Exécution comme nobody, système de fichiers protégé, /opt/nodum inaccessible, aucun privilège additionnel, réseau sortant bloqué sauf loopback, mémoire maximale 160 Mio, CPU limité à 25 % d’un cœur, 40 tâches. Environ 12 Mio mesurés au contrôle final ; ce n’est pas un test de charge. Sessions en mémoire avec cookies HTTPS et réinitialisation individuelle.

## Durée et coûts

Autorisation : 25 USD bruts au maximum, jusqu’au 12 décembre 2026. L’hôte existant continue d’être facturé pour Nodum ; aucune deuxième capacité fixe n’a été provisionnée. Un trafic sortant peut entraîner un coût variable. Les crédits et alertes du compte ont été contrôlés dans la console propriétaire ; leurs détails restent dans le rapport privé de livraison. Un budget est une alerte, pas un plafond dur.

Le minuteur policylens-expire.timer arrête uniquement Guardian le 12 décembre à 23:00 UTC, soit le 13 décembre à 00:00 au Maroc. Il ne supprime pas les fichiers, ne modifie pas Nodum et n’arrête pas le serveur partagé. Après échéance l’adresse Guardian n’est plus une démonstration disponible. Toute prolongation exige une nouvelle décision sur durée et coût.

## Validation distante

58 tests Python réussis sur l’hôte, 66 assertions de navigateur sur le véritable domaine HTTPS. Rapport français HTML/JSON réellement téléchargé, décisions après rechargement, simulation 48 → 72 → 48 et seconde session vierge vérifiés. La démonstration distante ne dépend pas de l’ordinateur local. Voir validation-browser-aws.json.

## Retour arrière ciblé (administrateur du serveur)

Ne jamais arrêter l’instance partagée ou les conteneurs Nodum.

1. `sudo systemctl disable --now policylens-expire.timer policylens-guardian.service`
2. Restaurer le contenu de /opt/nodum/Caddyfile.before-policylens-20261111 dans /opt/nodum/Caddyfile, en préservant le fichier monté : `sudo sh -c 'cat /opt/nodum/Caddyfile.before-policylens-20261111 > /opt/nodum/Caddyfile'`.
3. `sudo docker exec nodum-tls caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile`
4. `sudo docker exec nodum-tls caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile`
5. Vérifier le site Nodum. Conserver les versions et sauvegardes pour audit ; aucune suppression n’est nécessaire.

Le checkpoint métier original 13631a791204ccd39951e52dac7c067fb6cd470b reste intact dans la copie de travail antérieure. Le nouveau dépôt public possède son propre historique propre.

## Correction de date confirmée

Le 11 novembre, l’utilisateur a précisé le 12 décembre 2026, et non le 12 novembre. Le minuteur effectif a été modifié puis relu dans AWS Systems Manager : prochain déclenchement samedi 12 décembre 2026 à 23:00 UTC, soit dimanche 13 décembre à 00:00 au Maroc. La commande a terminé avec succès (code 0). Guardian actif et Nodum accessible après modification. Le droit IAM temporaire reste retiré ; cette correction a utilisé la console propriétaire, sans nouvel accès IAM.
