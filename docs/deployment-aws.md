# Déploiement AWS — procédure et état réel

## État au 11 novembre 2026

Le code inclut une configuration App Runner et un adaptateur public testé. Aucune ressource AWS n’est déclarée comme créée tant que la création, le déploiement et le contrôle HTTPS n’ont pas réussi.

La première vérification du compte authentifié a renvoyé SubscriptionRequiredException pour App Runner et AccessDenied pour la lecture du forfait, des crédits, des coûts et des budgets. Une connexion console du propriétaire est examinée pour lever ce blocage. Les crédits disponibles et leur éligibilité ne sont donc pas supposés vérifiés par le seul fait que des identifiants CLI existent.

L’autorisation de coût communiquée pour cette livraison est limitée à 25 USD bruts et une disponibilité jusqu’au 12 novembre 2026. Ce montant est une autorisation, pas un plafond technique garanti par AWS Budgets.

## Configuration minimale prévue

- Région candidate : Europe (Irlande), eu-west-1.
- Source : branche main du nouveau dépôt PolicyLens-MenageSimple-Guardian, via une connexion GitHub autorisée pour ce dépôt.
- Runtime : Python 3.11, fichier apprunner.yaml ; commande python3 public_server.py ; PORT=8080.
- Déploiements manuels ; aucune reconstruction automatique après chaque commit.
- 0,25 vCPU, 0,5 Go ; minimum et maximum d’instances : 1 ; concurrence cible : 8.
- Contrôle de santé HTTP /api/health ; endpoint public HTTPS fourni par AWS.
- Pas de domaine acheté, base de données, inférence, stockage durable ni accès aux réservations.
- LOCAL_PUBLIC_TEST doit être absent. Les cookies HTTPS isolent les sessions ; une mise à jour du service réinitialise les démonstrations en mémoire.

La version locale continue de fonctionner avec python server.py --ephemeral.

## Estimation brute avant crédits

Tarification publique consultée le 11 novembre : en Irlande, mémoire 0,007 USD / Go-heure et CPU actif 0,064 USD / vCPU-heure.

Pour une seule instance 0,25 vCPU / 0,5 Go pendant 48 heures :

- Mémoire provisionnée : 0,5 × 0,007 × 48 = 0,168 USD.
- CPU continuellement actif, hypothèse conservatrice : 0,25 × 0,064 × 48 = 0,768 USD.
- Total de calcul indicatif : 0,936 USD, avant construction, journaux, transferts, taxes et effets transitoires de déploiement. Ce n’est ni une facture ni un plafond garanti.

Un budget d’alerte à 5 / 10 / 20 USD peut signaler une dérive, avec destinataire choisi dans le compte. Une alerte n’arrête pas automatiquement le service. Vérifier l’éligibilité des crédits et leur expiration dans Billing avant de créer la ressource ; ne pas supposer que tout est gratuit.

## Validation nécessaire après création

Ouvrir le vrai domaine awsapprunner.com depuis deux sessions indépendantes, sans authentification. Vérifier les quatre constats, sources, calculateur, correction 48 → 72 → 48, décisions, rapport et isolation des sessions. Fermer l’application locale pour confirmer que le domaine public ne dépend pas de l’ordinateur. Consigner URL, ARN, région, commit et résultats dans un document de livraison séparé ; ne pas publier de secrets.

## Gestion et arrêt après examen

Dans App Runner, sélectionner le service créé, puis le mettre en pause une fois la période d’examen terminée. Vérifier les ressources encore facturables, notamment les journaux et toute ressource créée pour ce service. Reprendre le service si un recruteur a besoin d’un délai supplémentaire, après accord sur le coût. Ne pas supprimer ou mettre en pause un service encore nécessaire à l’examen. Aucun arrêt automatique n’a été programmé.

## Sources officielles

- https://docs.aws.amazon.com/apprunner/latest/dg/service-source-code-python.html
- https://docs.aws.amazon.com/apprunner/latest/dg/manage-autoscaling.html
- https://aws.amazon.com/apprunner/pricing/
