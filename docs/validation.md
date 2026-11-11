# Validation exécutée le 11 novembre 2026

- Copie de publication : 58 tests Python réussis, journal validation-python.txt ; contrôle cookie __Host- répété avec succès.
- Adaptateur public local : 66 assertions réussies, validation-browser-public-local.json.
- Serveur AWS Python 3.9.25 : 58 tests réussis avant démarrage.
- Véritable application AWS HTTPS : 66 assertions réussies, zéro échec et zéro erreur JavaScript non traitée ; validation-browser-aws.json. Capture public-aws-verified.png.

Le premier essai distant a exposé une attente manquante dans le test : le tableau s’affichait avant la réponse initiale du calculateur. Le test attend désormais la valeur calculée ; aucune modification du calculateur n’a été nécessaire. Le parcours distant complet a ensuite réussi.

Parcours : quatre constats, français hors citations, états vides, erreurs de validation, erreur réseau provoquée, chargement, liens, nouvelle saisie 12 → 48, revue humaine conservée au rechargement, ambiguïté employeur maintenue, simulation 48 → 72 → 48, recalcul, rapport HTML/JSON, affichage bureau/mobile, réinitialisation et second contexte vierge. Les erreurs HTTP 400 et réseau provoquées sont des contrôles attendus.

Le service est déployé sur AWS et a répondu depuis un navigateur distinct. Nodum répond toujours en HTTPS. Les captures vidéo et les exports joints proviennent du véritable service distant. Les anciennes captures locales sont conservées et identifiées comme telles par leur nom.

Pas de test de charge, de certification de sécurité ni de nouvelle mesure de précision Qwen. Le minuteur d’expiration a été vérifié comme actif et programmé, sans attendre son déclenchement réel.
