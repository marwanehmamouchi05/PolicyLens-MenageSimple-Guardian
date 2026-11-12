"""PolicyLens Impact Graph — dependency-free, bounded, evidence-first graph engine.

Operates only on supplied structured, source-attributed claims.  It DOES NOT crawl or
understand arbitrary new webpages.  All returned findings are candidates for human review.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from urllib.parse import urlparse
from collections import defaultdict
import re

MAX_CLAIMS = 300
MAX_PAGES = 100
MAX_EVIDENCE = 1200
PRIORITY = {'employer_role': 'high', 'cancellation_hours': 'high', 'contract_reference': 'high', 'equipment_vacuum': 'medium', 'cleaning_products': 'medium', 'payment_arrangement': 'medium'}
ALLOWED_TOPICS = {'employer_role', 'cancellation_hours', 'equipment_vacuum', 'cleaning_products', 'payment_arrangement'}
VERIFICATION_STATES = {'fresh_index', 'older_index', 'user_supplied', 'not_verified', 'historical'}


def _check_str(value, field, max_chars=300):
    if not isinstance(value, str) or not value.strip() or len(value) > max_chars:
        raise ValueError(f'Champ obligatoire : texte non vide de {max_chars} caractères au maximum.')
    return value.strip()


def validate_claim(c):
    if not isinstance(c, dict):
        raise ValueError('L’information doit être un objet JSON.')
    c = dict(c)
    for key in ('id', 'topic', 'value', 'scope', 'source_url', 'evidence', 'observed'):
        c[key] = _check_str(c.get(key), key, MAX_EVIDENCE if key == 'evidence' else 300)
    if c['topic'] not in ALLOWED_TOPICS:
        raise ValueError('Choisissez une politique prise en charge ou demandez une vérification humaine.')
    p = urlparse(c['source_url'])
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.hostname not in ('menagesimple.com','www.menagesimple.com'):
        raise ValueError('Utilisez une adresse HTTPS publique de menagesimple.com, sans identifiants.')
    try: date.fromisoformat(c['observed'])
    except ValueError: raise ValueError('La date d’observation doit être au format AAAA-MM-JJ.') from None
    if c.get('status','current') not in ('current','historical'):
        raise ValueError('Le statut de la source est invalide.')
    if c['topic'] == 'cancellation_hours':
        try: v = int(c['value'])
        except ValueError: raise ValueError('Le préavis doit être un nombre entier d’heures.') from None
        if not 1 <= v <= 720: raise ValueError('Le préavis doit être compris entre 1 et 720 heures.')
        c['value'] = str(v)
    for key in ('region', 'service_model', 'language', 'authority', 'status', 'verification'):
        if key in c and (not isinstance(c[key],str) or len(c[key]) > 100):
            raise ValueError('Champ facultatif invalide : '+key)
    c.setdefault('status','current')
    c.setdefault('verification', 'historical' if c['status']=='historical' else 'not_verified')
    if c['verification'] not in VERIFICATION_STATES:
        raise ValueError('L’état de vérification est invalide.')
    c.setdefault('region','')
    c.setdefault('service_model','menagesimple')
    return c


def validate_dataset(data):
    if not isinstance(data, dict): raise ValueError('Le registre doit être un objet JSON.')
    claims = data.get('claims',[])
    if not isinstance(claims, list) or len(claims) > MAX_CLAIMS:
        raise ValueError('Le registre contient trop d’informations.')
    clean = [validate_claim(c) for c in claims]
    ids = [c['id'] for c in clean]
    if len(ids) != len(set(ids)): raise ValueError('Un identifiant d’information est déjà utilisé.')
    pages = {c['source_url'] for c in clean}
    if len(pages) > MAX_PAGES: raise ValueError('Le registre contient trop de pages.')
    policies = data.get('policies', {})
    if not isinstance(policies,dict) or any(k not in ALLOWED_TOPICS for k in policies):
        raise ValueError('Le registre des politiques est invalide.')
    for k, p in policies.items():
        if not isinstance(p,dict) or not isinstance(p.get('label'),str) or not p.get('reference_value'):
            raise ValueError('Les informations de politique sont invalides : '+k)
    clauses = data.get('clauses',{})
    if not isinstance(clauses,dict):raise ValueError('Le registre des clauses est invalide.')
    refs = data.get('references',[])
    if not isinstance(refs,list) or len(refs)>100:raise ValueError('Les renvois contractuels sont invalides.')
    for r in refs:
        if not isinstance(r,dict) or not all(isinstance(r.get(k),str) for k in ('source_clause','target_clause','expected_topic')):
            raise ValueError('Un renvoi contractuel est incomplet.')
    return {**deepcopy(data), 'claims':clean}


def _context(a,b):
    # Distinct service variants/model and regional assertions cannot be silently equated.
    if 'generic' in (a.get('service_model'),b.get('service_model')):
        return 'needs_context', 'Un guide générique peut décrire un modèle juridique différent.'
    if a.get('service_model') != b.get('service_model'):
        return 'needs_context', 'Modèles de service différents ou non précisés.'
    if a['scope']!=b['scope'] and 'all' not in (a['scope'],b['scope']):
        return 'needs_context', 'Périmètres de prestations différents.'
    if a.get('region')!=b.get('region') and (a.get('region') or b.get('region')):
        return 'needs_context', 'Une page locale peut décrire une offre spécifique.'
    if a['topic'] == 'payment_arrangement':
        return 'needs_context','Une carte obligatoire à la réservation et un paiement en espèces peuvent coexister.'
    if a['topic'] == 'employer_role':
        return 'needs_context','La responsabilité juridique doit être examinée avec le mandat applicable.'
    return 'wording_difference','Les déclarations de même périmètre diffèrent; leur portée doit être vérifiée.'


def _value(x):
    return re.sub(r'\s+', ' ', x.strip().casefold())


def findings(data):
    """Candidate differences + validated wrong-clause references (never legal conclusions)."""
    d = validate_dataset(data)
    indexed = defaultdict(list)
    for c in d['claims']:
        if c['status'] == 'current': indexed[c['topic']].append(c)
    out = []
    for topic, cs in indexed.items():
        for i, a in enumerate(cs):
            for b in cs[i+1:]:
                if a['source_url'] == b['source_url'] or _value(a['value']) == _value(b['value']):
                    continue
                classification, reason = _context(a,b)
                source_recheck = any(c['verification'] != 'fresh_index' for c in (a,b))
                if source_recheck:
                    classification = 'needs_context'
                    reason = 'Au moins une source est ancienne, fournie manuellement ou non vérifiée; contrôler la page actuelle. ' + reason
                out.append({'id':f"difference::{a['id']}::{b['id']}", 'topic':topic,
                            'kind':classification, 'severity':PRIORITY.get(topic,'medium'),
                            'reason':reason, 'claim_ids':[a['id'],b['id']],
                            'page_urls':[a['source_url'],b['source_url']],
                            'human_review_required':True,'source_recheck_required':source_recheck})
    for r in d['references']:
        target = d['clauses'].get(r['target_clause'])
        expected = [k for k,v in d['clauses'].items() if v.get('topic') == r['expected_topic']]
        if not target or target.get('topic')!=r['expected_topic']:
            out.append({'id':'reference::'+r['source_clause']+'::'+r['target_clause'],
                        'topic':'contract_reference','kind':'reference_mismatch','severity':'high',
                        'reason':'La référence vise une section sans lien avec le sujet annoncé.',
                        'source_clause':r['source_clause'],'target_clause':r['target_clause'],
                        'expected_target_candidates':expected,'page_urls':[r['source_url']],
                        'human_review_required':True, 'source_recheck_required':False})
    return out


def impact(data, topic, proposed_value=None):
    """Return affected page checklist based on indexed claims only.

    Proposed value updates the canonical rule IN SIMULATION; it does not edit sources.
    """
    d=validate_dataset(data)
    if topic not in d['policies']: raise ValueError('Politique inconnue.')
    target = str(proposed_value if proposed_value is not None else d['policies'][topic]['reference_value'])
    if topic == 'cancellation_hours':
        target = validate_claim({'id':'temp','topic':topic,'value':target,'scope':'all','source_url':'https://menagesimple.com/','evidence':'simulation','observed':'2026-11-11'})['value']
    rows=[]
    for c in d['claims']:
        if c['topic']!=topic:continue
        if c['status']=='historical':
            st='historique'
        elif c['verification'] != 'fresh_index':
            st='a_verifier'
        elif topic in ('employer_role','payment_arrangement') or c.get('service_model')=='generic' or c.get('region') or c['scope'] not in ('regular','all'):
            st='a_verifier'
        elif _value(c['value'])==_value(target):
            st='conforme'
        elif c.get('service_model')=='generic' or c.get('region') or (c['scope'] not in ('regular','all')) or topic in ('employer_role','payment_arrangement'):
            st='a_verifier'
        else:
            st='ecart_potentiel'
        rows.append({'claim_id':c['id'],'page_url':c['source_url'],'value':c['value'],
                     'status':st,'scope':c['scope'],'region':c.get('region',''), 'evidence':c['evidence'],
                     'observed':c['observed'],'source_status':c['status'],
                     'verification':c['verification'],'simulation':c.get('simulation',False),
                     'recorded_value':c.get('recorded_value',c['value']),
                     'verification_note':c.get('verification_note',''),
                     'review_action':'Confirmer le contexte et la source avant publication.' if st=='a_verifier' else 'Vérifier et harmoniser cette référence si la nouvelle règle est confirmée.' if st=='ecart_potentiel' else 'Conserver la preuve historique.' if st=='historique' else 'Vérifier les exceptions avant de conclure.'})
    clause_refs=[]
    for ref in d['references']:
        if ref['expected_topic'] != topic: continue
        actual=d['clauses'].get(ref['target_clause'], {})
        valid=actual.get('topic')==ref['expected_topic']
        clause_refs.append({'source_clause':ref['source_clause'], 'target_clause':ref['target_clause'],
                            'expected_targets':[k for k,v in d['clauses'].items() if v.get('topic')==topic],
                            'status':'conforme' if valid else 'reference_incorrecte',
                            'page_url':ref['source_url'], 'evidence':ref.get('evidence','')})
    return {'topic':topic,'label':d['policies'][topic]['label'], 'reference_value':d['policies'][topic]['reference_value'],
            'proposed_value':target,'rows':rows,'contract_references':clause_refs,'indexed_count':len(rows),
            'coverage':'Seules les pages enregistrées sont comparées. Le site réel reste inchangé.'}


def simulate_claim_correction(data, claim_id, new_value):
    """Pure simulation: changes one saved claim; recomputes differences, no external writes."""
    d=validate_dataset(data)
    old = findings(d)
    found=False
    for c in d['claims']:
        if c['id']==claim_id:
            c.setdefault('recorded_value',c['value'])
            c['value']=_check_str(new_value,'nouvelle valeur')
            c['simulation']=True
            c['verification']='user_supplied'
            c.update(validate_claim(c))
            found=True
            break
    if not found: raise ValueError('Information introuvable.')
    new=findings(d)
    return {'old_count':len(old),'new_count':len(new),'old_findings':old,'new_findings':new,
            'resolved_ids':sorted({x['id'] for x in old}-{x['id'] for x in new}),
            'created_ids':sorted({x['id'] for x in new}-{x['id'] for x in old}),
            'simulation_only':True, 'data':d}


def add_claim(data, claim):
    d=validate_dataset(data)
    new=validate_claim(claim)
    if new['id'] in {x['id'] for x in d['claims']}: raise ValueError('Cet identifiant est déjà utilisé.')
    d['claims'].append(new)
    return validate_dataset(d)


def build_graph(data):
    d=validate_dataset(data)
    issues=findings(d)
    nodes=[]; edges=[]; pages={}
    for topic,p in d['policies'].items():
        nodes.append({'id':'policy:'+topic,'type':'policy','label':p['label'],'topic':topic})
    for c in d['claims']:
        page_id='page:'+c['source_url']
        if page_id not in pages:
            pages[page_id]={'id':page_id,'type':'page','label':urlparse(c['source_url']).path or '/',
                            'url':c['source_url']}
        nodes.append({'id':'claim:'+c['id'],'type':'claim','label':c['value'], 'topic':c['topic'],'claim_id':c['id'],'simulation':c.get('simulation',False),
                      'historical':c['status']=='historical'})
        edges.append({'source':page_id,'target':'claim:'+c['id'],'type':'contient'})
        edges.append({'source':'claim:'+c['id'],'target':'policy:'+c['topic'],'type':'concerne'})
    nodes+=list(pages.values())
    for clause, info in d.get('clauses',{}).items():
        nodes.append({'id':'clause:'+clause,'type':'clause','label':'CGV §'+clause,'topic':info.get('topic')})
    for ref in d.get('references',[]):
        edges.append({'source':'clause:'+ref['source_clause'],'target':'clause:'+ref['target_clause'],
                      'type':'renvoi_contractuel'})
        edges.append({'source':'policy:'+ref['expected_topic'],'target':'clause:'+ref['source_clause'],
                      'type':'reference_a_verifier'})
    policy_page_count={topic:len({c['source_url'] for c in d['claims'] if c['topic']==topic and c['status']=='current'})
                       for topic in d['policies']}
    return {'nodes':nodes,'edges':edges,'findings':issues, 'impact_summary':policy_page_count,
            'summary':{'indexed_pages':len(pages),'claims':len(d['claims']),
                       'policies':len(d['policies']),'review_items':len(issues)},
            'disclaimer':'Graph generated from attributed structured claims, not a complete live scan of the website.'}
