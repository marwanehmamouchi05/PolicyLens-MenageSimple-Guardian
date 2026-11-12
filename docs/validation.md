# Validation reproductible

Depuis la racine :

```sh
python -m unittest discover -v
node --check app.js
node --check navigation.js
node --check impact.js
node --check graph-explorer.js
```

106 tests Python réussis le 12 novembre 2026 : docs/audit/tests-final-local.txt. Le compte inclut les 20 tests du module de graphe et les régressions du moteur existant.

Pour les contrôles navigateur, installer Playwright dans un environnement de test séparé (aucune dépendance nécessaire au serveur), puis lancer le serveur public en mode HTTP local :

```sh
LOCAL_PUBLIC_TEST=1 BIND_HOST=127.0.0.1 PORT=8893 python public_server.py
node browser_release.cjs
node browser_graph_explorer.cjs
```

Sous PowerShell, affecter chaque variable avec `$env:NOM='valeur'` avant le lancement. Les scripts utilisent Chrome installé. PLAYWRIGHT_MODULE permet de fournir le chemin d’une installation Playwright existante. TARGET_URL et PROOF_DIR permettent de cibler un autre service et de conserver des preuves séparées (premier script).

Résultats locaux effectivement exécutés : 116 contrôles généraux (results.json), puis 24 contrôles ciblés (graph-explorer-results.json), 0 erreur JavaScript. Les téléchargements ont été ouverts et vérifiés : rapports français, décisions, preuves et historiques réels. Les erreurs, états vides, chargement, réseau indisponible, mobile, clavier, plein écran, deux visiteurs et protections de saisie ont été exercés.

Les scripts respectent la limite publique de 120 demandes/minute ; le parcours général attend 59 secondes entre deux phases. Un échec réseau ponctuel d’un premier essai a été corrigé par une exécution complète réussie, sans suppression de la protection. Les preuves anciennes ne doivent pas être confondues avec une nouvelle exécution.

Les contrôles AWS sont enregistrés dans docs/validation/aws ; l’extraction propre est documentée dans docs/audit/clean-extraction-tests.txt. Pas de test de charge, d’audit externe de sécurité ou de mesure d’impact commercial.

## Résultats distants exécutés

Le 12 novembre, sur `https://policylens.54-173-165-46.sslip.io` : 116 contrôles généraux et 24 ciblés, zéro erreur JavaScript non traitée. Voir `docs/validation/aws/results.json`, `graph-explorer-results.json` et `release-content-verification.json`. Les contrôles font correspondre la réponse d’impact à la valeur de la requête pour ne pas confondre une actualisation en arrière-plan avec le calcul demandé. Le navigateur revient au premier visiteur après l’ouverture d’un second contexte.

Des essais intermédiaires du script de navigateur ont exposé des attentes trop courtes et une réponse d’actualisation capturée à la place de la réponse demandée. Les contrôles finaux complets ont été réexécutés avec les attentes et le rapprochement de requête corrects. Le défaut de redémarrage HTTP détecté pendant la publication a été reproduit sur Linux, corrigé et testé ; son retour arrière n’est pas masqué.

La vidéo finale dure 176 secondes. Le MP4 a été décodé intégralement sans erreur ; 13 images représentatives ont été extraites et examinées. Les sous-titres français sont intégrés à l’image et également fournis en SRT. Lecture YouTube contrôlée, visibilité non répertoriée et contrôles YouTube sans problème signalé.
