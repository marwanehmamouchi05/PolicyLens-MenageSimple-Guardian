# Validation reproductible

Depuis la racine :

```sh
python -m unittest discover -v
node --check app.js
node --check navigation.js
node --check impact.js
node --check graph-explorer.js
```

106 tests Python réussis le 12 novembre 2026 : docs/audit/tests-payment.txt. Le compte inclut les 20 tests du module de graphe et les régressions du moteur existant.

Pour les contrôles navigateur, installer Playwright dans un environnement de test séparé (aucune dépendance nécessaire au serveur), puis lancer le serveur public en mode HTTP local :

```sh
LOCAL_PUBLIC_TEST=1 BIND_HOST=127.0.0.1 PORT=8893 python public_server.py
node browser_release.cjs
node browser_graph_explorer.cjs
```

Sous PowerShell, affecter chaque variable avec `$env:NOM='valeur'` avant le lancement. Les scripts utilisent Chrome installé. PLAYWRIGHT_MODULE permet de fournir le chemin d’une installation Playwright existante. TARGET_URL et PROOF_DIR permettent de cibler un autre service et de conserver des preuves séparées (premier script).

Résultats locaux effectivement exécutés : 116 contrôles généraux (results.json), puis 24 contrôles ciblés (graph-explorer-results.json), 0 erreur JavaScript. Les téléchargements ont été ouverts et vérifiés : rapports français, décisions, preuves et historiques réels. Les erreurs, états vides, chargement, réseau indisponible, mobile, clavier, plein écran, deux visiteurs et protections de saisie ont été exercés.

Les scripts respectent la limite publique de 120 demandes/minute ; le parcours général attend 59 secondes entre deux phases. Un échec réseau ponctuel d’un premier essai a été corrigé par une exécution complète réussie, sans suppression de la protection. Les preuves anciennes ne doivent pas être confondues avec une nouvelle exécution.

Les contrôles AWS et l’extraction propre sont enregistrés dans des fichiers distincts après réalisation. Pas de test de charge, d’audit externe de sécurité ou de mesure d’impact commercial.
