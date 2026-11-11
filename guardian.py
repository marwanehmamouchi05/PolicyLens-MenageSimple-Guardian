"""Small, deterministic submission workflow. No network or model calls."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from copy import deepcopy
import hashlib, html, json, re
from engine import analyze, cancellation_scenario

ROOT=Path(__file__).resolve().parent
SOURCES=json.loads((ROOT/'sources.json').read_text(encoding='utf-8'))
EXCERPTS={e['id']:dict(e,source=s['id'],url=s['url']) for s in SOURCES['sources'] for e in s['excerpts']}
ORIGINAL=EXCERPTS['pricing-notice']['quote']
SUGGESTION='Annulation sans frais jusqu’à 48 heures avant le ménage standard. Passé ce délai, le service est facturé à 90 %.'
from business_fr import LIMITS as LIMITATIONS
def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16]
def deadline(text):
    if text==ORIGINAL:return 24
    m=re.fullmatch(r'Annulation sans frais jusqu’à (\d{1,3}) heures avant le ménage standard\. Passé ce délai, le service est facturé à 90 %\.',text)
    return int(m[1]) if m and 0<int(m[1])<=168 else None
def claim(cid,value,source,scope):
    e=EXCERPTS[source]
    return dict(id=cid,company='MénageSimple',topic='free_cancellation_hours',value=str(value),scope=scope,
      source_url=e['url'],evidence=e['quote'],observed=e['observed'])

def findings(snapshot):
    hours=deadline(snapshot['text'])
    terms=int(re.search(r'\d+',EXCERPTS['terms-notice']['quote'])[0])
    faq=int(re.search(r'\d+',EXCERPTS['faq-notice']['quote'])[0])
    claims=[claim('article',hours,'pricing-notice',snapshot['scope']),claim('terms',terms,'terms-notice','all'),claim('faq',faq,'faq-notice','regular')]
    claims[0]['evidence']=snapshot['text']
    result=analyze(claims) if hours is not None else None
    aligned=snapshot['scope']=='regular' and snapshot['confirmed']
    if hours is None or snapshot['scope']!='regular':status='Insufficient evidence'
    elif result['flag_count']:status='Wording inconsistency'
    elif aligned:status='Resolved in simulation'
    else:status='Insufficient evidence'
    target=re.search(r'point (\d+[a-z])',EXCERPTS['terms-reference']['quote'])[1]
    cancellation_section=re.match(r'(\d+[a-z])',EXCERPTS['terms-cancellation']['quote'])[1]
    wrong_reference=target!=cancellation_section
    base=[dict(id='cancellation',name='One booking. Two cancellation deadlines.',policy='Cancellation policy',severity='High',
      status=status,evidence=['pricing-notice','terms-notice','terms-fee','faq-notice'],
      explanation=f'The selected pricing excerpt gives 24 hours; the terms and FAQ give {terms} hours. Current local snapshot: '+(f'{hours} hours.' if hours is not None else 'wording cannot be safely parsed.'),
      impact='Customers cancelling between 24 and 48 hours could expect different fees if these statements apply to the same booking. The illustrative 36-hour scenario gives a CHF 79.02 expectation gap.',
      alternatives='The pricing article may be outdated or refer to an exception or a different service. The terms reserve signed contracts. Effective dates and actual billing remain unconfirmed.',
      action='Ask the business owner to confirm the applicable deadline, fee, scope and exceptions; then align pricing, terms and FAQ.',
      suggestion=SUGGESTION,
      check=dict(article_hours=hours,terms_hours=terms,faq_hours=faq,scope=snapshot['scope'],conditions_assumed_aligned=snapshot['confirmed'],comparison=result)),
    dict(id='reference',name='Cancellation points to photography.',policy='Terms §7 → §10',severity='Medium',
      status='Wording inconsistency' if wrong_reference else 'Resolved in simulation',evidence=['terms-reference','terms-cancellation','terms-photo'],
      explanation=f'Section 7 refers cancellation fees to {target}. Cancellation appears under {cancellation_section}; 10d is the photography heading. The reference is compared with the curated section headings.',
      impact='A customer or support colleague following the reference reaches an unrelated policy section.',
      alternatives='The full section 7 context concerns cancellations after payment problems. Confirm whether this context needs a separate fee provision and check the intended version.',
      action='Confirm the intended clause and correct the section reference in the same published version.',
      suggestion='Sous réserve de confirmation de la clause applicable, remplacer le renvoi « 10d » par « 10c » dans la section 7.'),
    dict(id='equipment',name='Who brings the cleaning products?',policy='Standard cleaning / equipment',severity='Review',status='Clarity concern',
      evidence=['home-equipment','english-products','faq-products'],
      explanation='The French homepage and FAQ include products; the English guide asks customers to provide basic products. The homepage now explicitly asks standard-cleaning customers to supply a vacuum and mop.',
      impact='Customers reading different languages may prepare different supplies before the visit. No disrupted service has been established.',
      alternatives='Products and equipment are distinct. End-of-tenancy cleaning includes equipment according to the FAQ; optional equipment and customer preferences can explain some differences.',
      action='Confirm the service and optional extras, then align the English guide with the service-specific French explanation.',
      suggestion='After owner confirmation: Cleaning products are included. For standard cleaning, please provide a vacuum cleaner and mop; check equipment options when booking. End-of-tenancy cleaning includes products and equipment. Confirm any exceptions for your booking.')]
    for f in base:
        f['fingerprint']=fingerprint([f['id'],f['status'],snapshot if f['id']=='cancellation' else [EXCERPTS[e] for e in f['evidence']]])
    base[0]['historical']=True
    base[0]['evidence'].insert(1,'pricing-current')
    from employer import finding
    base.append(finding(EXCERPTS,fingerprint))
    for f in base:
        f['fingerprint']=fingerprint([f['id'],f['status'],[EXCERPTS[q] for q in f['evidence']],snapshot if f['id']=='cancellation' else f.get('claims',[])])
    return base

class Guardian:
    def __init__(self,path=None):
        self.path=Path(path) if path else None
        if self.path and self.path.exists():self.state=json.loads(self.path.read_text(encoding='utf-8'))
        else:self.state=dict(snapshot=dict(text=ORIGINAL,scope='regular',confirmed=False),history=[],reviews=[],revision=0)
        self.state.setdefault('information',[])
        self.state.setdefault('information_history',[])
    def save(self):
        if self.path:
            tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(self.state,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(self.path)
    def view(self):
        state=deepcopy(self.state);state.update(findings=findings(state['snapshot']),sources=SOURCES,limitations=LIMITATIONS,suggestion=SUGGESTION)
        from new_information import evaluate
        from business_fr import describe
        state['findings'].extend(evaluate(d) for d in state['information'])
        for f in state['findings']:
            f['review']=next((r for r in reversed(state['reviews']) if r['fingerprint']==f['fingerprint']),None)
            f['display']=describe(f)
        return state
    def information(self,data):
        from new_information import evaluate
        from uuid import uuid4
        data=deepcopy(data)
        current=next((d for d in self.state['information'] if d['id']==data.get('id')),None)
        if data.get('id') and not current:raise ValueError('Information introuvable.')
        if not current and len(self.state['information'])>=30:raise ValueError('Cette démonstration est limitée à 30 informations.')
        data['id']=current['id'] if current else 'info-'+uuid4().hex[:10]
        data={k:data[k] for k in ('id','category','value','title','excerpt','source_url','scope','confirmed','simulated') if k in data}
        if not isinstance(data.get('value'),(str,int,float)) or isinstance(data.get('value'),bool):raise ValueError('Valeur numérique attendue.')
        data['value']=str(data['value'])
        result=evaluate(data)
        self.state['information_history'].append(dict(time=now(),id=data['id'],before=deepcopy(current),after=deepcopy(data),status=result['status']))
        if current:self.state['information'][self.state['information'].index(current)]=data
        else:self.state['information'].append(data)
        self.save();return self.view()
    def change(self,data):
        text=data.get('text');scope=data.get('scope');confirmed=data.get('confirmed')
        if not isinstance(text,str) or not 1<=len(text)<=2000:raise ValueError('Le texte local doit contenir entre 1 et 2 000 caractères.')
        if scope not in ('regular','other') or type(confirmed) is not bool:raise ValueError('Précisez le service et la confirmation des conditions.')
        before=deepcopy(self.state['snapshot']);after=dict(text=text,scope=scope,confirmed=confirmed)
        old=findings(before)[0]['status'];new=findings(after)[0]['status']
        self.state['revision']+=1;self.state['snapshot']=after
        self.state['history'].append(dict(time=now(),revision=self.state['revision'],before=before,after=after,before_status=old,after_status=new))
        self.save();return self.view()
    def review(self,data):
        f=next((f for f in self.view()['findings'] if f['id']==data.get('id')),None)
        if not f or data.get('fingerprint')!=f['fingerprint']:raise ValueError('Le constat a changé. Actualisez-le avant de prendre une décision.')
        if data.get('decision') not in ('Accept','Edit','Reject','Request clarification'):raise ValueError('Choisissez une décision de revue.')
        wording=data.get('wording','');note=data.get('note','')
        if not isinstance(wording,str) or not 1<=len(wording)<=3000 or not isinstance(note,str) or len(note)>2000:raise ValueError('Renseignez une proposition de 1 à 3 000 caractères et une note de 2 000 caractères au maximum.')
        r=dict(time=now(),id=f['id'],fingerprint=f['fingerprint'],decision=data['decision'],wording=wording,note=note)
        self.state['reviews'].append(r);self.save();return self.view()

def scenario(data):
    # Preserve the original Decimal-based calculator; add a selectable threshold.
    try:base=cancellation_scenario(data['notice'],data['rate'],data['duration'])
    except ValueError:raise ValueError('Saisissez un préavis, un prix et une durée valides, dans les limites du formulaire.')
    try:threshold=Decimal(str(data['threshold']))
    except InvalidOperation:raise ValueError('Le délai d’annulation doit être un nombre valide.')
    if not threshold.is_finite() or not 0<threshold<=168:raise ValueError('Le délai doit être supérieur à zéro et ne pas dépasser 168 heures.')
    fee=Decimal(str(data['rate']))*Decimal(str(data['duration']))*Decimal('.9') if Decimal(str(data['notice']))<threshold else Decimal(0)
    base['selected_rule_chf']=str(fee.quantize(Decimal('.01'),rounding=ROUND_HALF_UP));base['threshold_hours']=str(threshold)
    base['assumption']='La comparaison suppose les mêmes frais tardifs de 90 % pour les deux délais. Les frais de l’article et les exceptions d’une réservation ne sont pas vérifiés.'
    return base

def report(state):
    from report_fr import render
    return render(state)
