"""Reviewer-supplied structured inputs compared by the unchanged engine."""
from datetime import date
from decimal import Decimal, InvalidOperation
from engine import analyze, validate_claims
from guardian import EXCERPTS, fingerprint

CATEGORIES={
 'cancellation':dict(topic='free_cancellation_hours',name='Délai d’annulation',unit='heures',evidence=['terms-notice','faq-notice'],maximum=168),
 'late_fee':dict(topic='fee_percent',name='Frais d’annulation tardive',unit='%',evidence=['terms-fee'],maximum=100)
}
def evaluate(data):
    category=data.get('category')
    if category not in CATEGORIES:raise ValueError('Choisissez une catégorie prise en charge.')
    cfg=CATEGORIES[category]
    try:value=Decimal(str(data.get('value','')))
    except InvalidOperation:raise ValueError('Saisissez une valeur numérique.')
    if not value.is_finite() or not 0<=value<=cfg['maximum'] or category=='cancellation' and value==0:raise ValueError('Valeur hors limites pour cette catégorie.')
    for key,maximum in (('title',120),('excerpt',2500),('source_url',2000)):
        if not isinstance(data.get(key),str) or not 1<=len(data[key].strip())<=maximum:raise ValueError('Renseignez le titre, l’extrait et une URL HTTPS.')
    if data.get('scope') not in ('regular','other') or type(data.get('confirmed')) is not bool or type(data.get('simulated')) is not bool:raise ValueError('Précisez le service, les conditions et le caractère fictif.')
    entered=dict(id='entered',company='MénageSimple',topic=cfg['topic'],value=str(value),scope=data['scope'],source_url=data['source_url'].strip(),evidence=data['excerpt'].strip(),observed=date.today().isoformat(),verification_status='unverified')
    saved=[]
    for eid in cfg['evidence']:
        e=EXCERPTS[eid]
        # Quantities are read from the saved verified excerpts, not from a demo value.
        import re
        number=re.search(r'\d+',e['quote'])[0]
        saved.append(dict(id=eid,company='MénageSimple',topic=cfg['topic'],value=number,scope='regular',source_url=e['url'],evidence=e['quote'],observed=e['observed']))
    try:validate_claims([entered]+saved)
    except ValueError:raise ValueError('Vérifiez les champs de la règle et renseignez une URL HTTPS valide, sans identifiant ni mot de passe.')
    result=analyze([entered]+saved)
    if data['scope']!='regular' or not data['confirmed']:status='Insufficient evidence'
    elif result['flag_count']:status='Potential mismatch'
    else:status='Compatible input'
    return dict(id=data['id'],name=data['title'].strip(),policy=cfg['name'],severity='High' if category=='cancellation' else 'Medium',status=status,
      evidence=cfg['evidence'],submitted={k:data[k] for k in ('category','value','title','excerpt','source_url','scope','confirmed','simulated')},
      explanation=f'Valeur saisie : {value} {cfg["unit"]}. Référence enregistrée : {saved[0]["value"]} {cfg["unit"]}. La comparaison utilise la valeur structurée ; l’extrait libre n’est pas interprété automatiquement.',
      impact='Des informations différentes peuvent créer des attentes différentes chez les clients. La portée réelle doit être confirmée avant toute action.',
      alternatives='Le texte saisi peut concerner une exception, une date ou un service différent. Son URL est non vérifiée et ne valide pas le contenu saisi.',
      action='Vérifier la source et l’applicabilité. Si le même service est concerné, harmoniser le texte avec la règle confirmée puis relancer la comparaison.',
      suggestion=f'Après confirmation du responsable, communiquer une valeur de {saved[0]["value"]} {cfg["unit"]} pour ce service et expliciter les exceptions.',
      check=result,fingerprint=fingerprint(data))
