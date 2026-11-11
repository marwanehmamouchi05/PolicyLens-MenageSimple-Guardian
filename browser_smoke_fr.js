// Call with a Playwright page opened in a fresh ephemeral session.
async (page) => {
 const checks=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
 const check=(ok,name)=>{if(!ok)throw Error(name);checks.push(name);};
 await page.waitForSelector('[data-issue="cancellation"]');
 await page.waitForFunction(()=>document.querySelector('#scenario-result').textContent.includes('79.02'));
 const postClickError=async(selector,path)=>{const response=page.waitForResponse(r=>r.url().endsWith(path)&&r.request().method()==='POST');await page.locator(selector).click();check((await response).status()===400,'Erreur prévue : '+path);await page.waitForFunction(()=>!document.querySelector('#rescan').disabled);};
 const postClick=async(selector,path)=>{const response=page.waitForResponse(r=>r.url().endsWith(path)&&r.request().method()==='POST');await page.locator(selector).click();const r=await response;check(r.status()===200,'Réponse valide : '+path);await page.waitForFunction(()=>!document.querySelector('#rescan').disabled);};
 check(await page.locator('html').getAttribute('lang')==='fr','Tableau de bord en français');
 check(await page.locator('[data-issue]').count()===4,'Quatre catégories intégrées');
 check(await page.locator('#metric-open').innerText()==='1'&&await page.locator('#metric-clarify').innerText()==='2','Synthèse initiale calculée');
 check((await page.locator('#detail').innerText()).includes('24h')&&(await page.locator('#detail').innerText()).includes('48 heures'),'Preuves d’annulation visibles');
 check(await page.locator('#source-register a').count()===5,'Cinq liens de sources réelles');
 check((await page.locator('#scenario-result').innerText()).includes('79.02'),'Calcul exact du scénario');
 await page.locator('[data-issue="reference"]').click();check((await page.locator('#detail').innerText()).includes('10d. Photographies'),'Renvoi contractuel conservé');
 await page.locator('[data-issue="equipment"]').click();check((await page.locator('#detail').innerText()).includes('À clarifier'),'Produits : qualification prudente');

 const frenchAudit=async()=>await page.evaluate(()=>{const copy=document.body.cloneNode(true);copy.querySelectorAll('script,style,blockquote').forEach(n=>n.remove());return !/One booking|Cancellation policy|Clarity concern|After owner confirmation|Pending review|Local wording|Request clarification|Failed to fetch|Not found/.test(copy.textContent);});
 check(await frenchAudit(),'Libellés de l’écran principal en français hors citations');
 await page.locator('[data-issue="employer"]').click();
 check((await page.locator('#detail').innerText()).includes('clarification nécessaire'),'Ambiguïté employeur visible');
 check(await page.locator('.role-comparison tbody tr').count()===4,'Employeur, administration, assurances et responsabilités distingués');
 check((await page.locator('#detail').innerText()).includes('non explicitée')||(await page.locator('#detail').innerText()).includes('Non précisée'),'Absence de désignation explicite dans le guide signalée');
 check((await page.locator('#detail').innerText()).includes('2026-11-10')&&(await page.locator('#detail').innerText()).includes('Anglais'),'Langue, date et périmètre des preuves');
 check(await frenchAudit(),'Explications employeur en français, citations anglaises conservées');
 await page.locator('#review-wording').fill('');await postClickError('[data-review="Accept"]','/api/review');
 check((await page.locator('#message').innerText()).includes('Renseignez une proposition'),'Erreur de décision vide en français');
 await page.locator('#review-wording').fill('Quel modèle s’applique au service réservé ?');await postClick('[data-review="Request clarification"]','/api/review');
 await page.reload();await page.waitForSelector('[data-issue="employer"]');await page.locator('[data-issue="employer"]').click();
 check((await page.locator('.review-state').innerText()).includes('Demander une précision'),'Décision employeur conservée après rechargement');
 check((await page.locator('.detail-top').innerText()).includes('À clarifier'),'La revue ne résout pas le modèle employeur');
 await page.locator('#information-clear').click();check((await page.locator('#information-result').innerText()).includes('Aucune information analysée'),'État vide en français');
 await postClickError('#information-submit','/api/information');check((await page.locator('#message').innerText()).includes('Saisissez une valeur numérique'),'Erreur de nouvelle saisie vide en français');
 await page.locator('#rate').fill('');await postClickError('#scenario button','/api/scenario');check((await page.locator('#message').innerText()).includes('Saisissez un préavis'),'Erreur du calculateur en français');await page.locator('#rate').fill('43.90');
 await page.locator('#information-title').fill('Article fictif de démonstration');await page.locator('#information-value').fill('12');await page.locator('#information-url').fill('https://example.org/article-fictif');await page.locator('#information-excerpt').fill('Annulation gratuite jusqu’à 12 heures avant le ménage.');await page.locator('#information-confirmed').check();
 await postClick('#information-submit','/api/information');
 check((await page.locator('#information-result').innerText()).includes('Écart potentiel'),'Nouvel écart de 12 heures détecté');
 check(await page.locator('#metric-open').innerText()==='2','Synthèse actualisée après nouvelle analyse');
 check((await page.locator('#detail').innerText()).includes('URL déclarée, non vérifiée'),'Origine de saisie qualifiée');
 await page.locator('#information-value').fill('48');await page.locator('#information-excerpt').fill('Annulation gratuite jusqu’à 48 heures avant le ménage.');await postClick('#information-submit','/api/information');
 check((await page.locator('#information-result').innerText()).includes('Aucun écart'),'Modification de la même saisie à 48 heures compatible');
 check(await page.locator('[data-issue]').count()===5&&await page.locator('#metric-open').innerText()==='1','Pas de doublon ni de faux conflit');
 await page.locator('[data-issue="cancellation"]').click();
 for(const decision of ['Accept','Edit','Reject','Request clarification']){
  await page.locator('#review-wording').fill('Proposition examinée pour la démonstration uniquement.');await page.locator('#review-note').fill('Validation du responsable à obtenir.');await postClick(`[data-review="${decision}"]`,'/api/review');
  check((await page.locator('.review-state').innerText()).includes('Décision enregistrée'),'Décision humaine : '+decision);
 }
 await page.locator('#use-suggestion').click();await page.locator('#confirmed').check();await postClick('#apply','/api/snapshot');
 check((await page.locator('#check-status').innerText()).includes('Résolu dans la simulation'),'Correction locale à 48 heures recalculée');
 check(await page.locator('#metric-resolved').innerText()==='1','Résumé des résolutions dynamique');
 check((await page.locator('.review-state').innerText()).includes('En attente'),'Décision précédente non reprise après changement');
 await page.locator('#snapshot-text').fill((await page.locator('#snapshot-text').inputValue()).replace('48','72'));await postClick('#apply','/api/snapshot');
 check((await page.locator('#check-status').innerText()).includes('Écart historique à simuler'),'Nouvel écart à 72 heures réapparu');
 await page.locator('#snapshot-text').fill((await page.locator('#snapshot-text').inputValue()).replace('72','48'));await postClick('#apply','/api/snapshot');
 await postClick('[data-review="Accept"]','/api/review');
 check((await page.locator('[data-issue="employer"]').innerText()).includes('À clarifier'),'La correction d’annulation ne résout pas l’employeur');
 const report=await page.evaluate(async()=>await(await fetch('/report')).text());
 check(report.includes('lang="fr"')&&report.includes('Synthèse pour le responsable')&&report.includes('Résolu dans la simulation'),'Rapport de direction en français');
 check(report.includes('Article fictif de démonstration')&&report.includes('URL non vérifiée')&&report.includes('Valeur précédente : 12'),'Rapport : nouvelle saisie et son historique');
 check(report.includes('Qui est réellement l’employeur ?')&&report.includes('Une gestion déléguée'),'Employeur intégré au rapport français');
 check(report.includes('Accepter')&&report.includes('Historique des corrections simulées'),'Rapport : décisions et avant/après');
 const exported=await page.evaluate(async()=>{const r=await fetch('/api/export');return {header:r.headers.get('content-disposition'),data:await r.json()};});
 check(exported.data.problemes.some(p=>p.titre.includes('employeur'))&&!JSON.stringify(exported.data).includes('Clarity concern'),'Rapport JSON en français avec employeur');
 check(exported.header.includes('attachment')&&exported.data.historique_informations.length===2,'Export JSON complet');
 await page.locator('#threshold').selectOption('24');await postClick('#scenario button','/api/scenario');
 check((await page.locator('#scenario-result').innerText()).includes('Règle sélectionnée (24 h) : CHF 0.00'),'Calculateur : règle sélectionnée conservée');
 await postClick('#rescan','/api/recheck');check((await page.locator('#check-status').innerText()).includes('Résolu'),'Revérification locale conservée');
 await page.setViewportSize({width:1440,height:1100});check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Bureau sans débordement');
 await page.setViewportSize({width:390,height:844});check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile sans débordement');

 let release;const hold=new Promise(resolve=>release=resolve);await page.route('**/api/recheck',async route=>{await hold;await route.continue();});
 const loadingResponse=page.waitForResponse(r=>r.url().endsWith('/api/recheck'));await page.locator('#rescan').click();check(await page.locator('#loading').isVisible(),'Chargement affiché en français');release();await loadingResponse;await page.waitForFunction(()=>document.querySelector('#loading').hidden);await page.unroute('**/api/recheck');
 await page.route('**/api/recheck',route=>route.abort());await page.locator('#rescan').click();await page.waitForFunction(()=>document.querySelector('#message').textContent.includes('Impossible de joindre'));check((await page.locator('#message').innerText()).includes('application locale'),'Erreur réseau en français');await page.unroute('**/api/recheck');
 check(await frenchAudit(),'Parcours final sans libellé anglais hors preuve');
 check(errors.length===0,'Aucune erreur JavaScript');
 await page.setViewportSize({width:1440,height:1100});await page.evaluate(()=>window.scrollTo(0,0));
 return {passed:checks.length,failed:0,checks,errors};
}
