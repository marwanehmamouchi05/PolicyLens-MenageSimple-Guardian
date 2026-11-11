"""PolicyLens V3: deterministic, source-grounded, company-independent claim comparison."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
from typing import Any
from urllib.parse import urlparse
import json, re, hashlib
from typed import compare

HIGH_TOPICS = {'employer_role', 'free_cancellation_hours'}
NUMERIC_TOPICS = {'free_cancellation_hours', 'bedrooms', 'area_m2', 'ski_access', 'fee_percent'}
MAX_CLAIMS = 250

def validate_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(claims, list) or len(claims) > MAX_CLAIMS:
        raise ValueError('Expected an array of at most 250 claims')
    ids = set(); cleaned = []
    required = ('id','company','topic','value','scope','source_url','evidence','observed')
    for c in claims:
        if not isinstance(c, dict) or any(k not in c for k in required):
            raise ValueError('Claims must be objects with required fields')
        if not all(isinstance(c[k], str) and 0 < len(c[k]) <= 2500 for k in required):
            raise ValueError('Mandatory fields must be nonempty strings <=2500 characters')
        for opt in ('unit','value_type','product','jurisdiction','variant','measurement','language','authority','effective_from','effective_until','conditions','verification_status'):
            if opt in c and not isinstance(c[opt],str):raise ValueError(f'Invalid {opt}')
        if c['id'] in ids: raise ValueError('Duplicate claim id')
        ids.add(c['id'])
        p=urlparse(c['source_url'])
        if p.scheme != 'https' or not p.hostname or p.username or p.password:
            raise ValueError('Source URL must be a valid HTTPS URL')
        for key in ('effective_from','effective_until','observed'):
            if c.get(key):
                try: date.fromisoformat(c[key])
                except (TypeError,ValueError): raise ValueError(f'Invalid {key}: expected YYYY-MM-DD')
        if c.get('effective_from') and c.get('effective_until') and c['effective_from']>c['effective_until']:
            raise ValueError('Effective date range reversed')
        if len(c.get('conditions',''))>2500:raise ValueError('Conditions too long')
        cleaned.append(dict(c))
    return cleaned

def normalized(c):
    value = c['value'].strip()
    if c['topic'] in NUMERIC_TOPICS:
        # Accept numeric strings and simple unit-suffixed numbers, but never infer a conversion.
        v=re.fullmatch(r'([+-]?\d+(?:[.,]\d+)?)\s*(?:h|hours|heures|m²|m2|%|bedrooms?)?',value,re.I)
        if v:
            try: return ('number',Decimal(v.group(1).replace(',','.')).normalize())
            except InvalidOperation: pass
    return ('text',re.sub(r'\s+',' ',value).casefold())

def _context(a,b):
    if a.get('conditions') != b.get('conditions') and (a.get('conditions') or b.get('conditions')):return 'review','Conditions differ or are incomplete'
    if (a.get('conditions') or b.get('conditions')) and a.get('conditions')==b.get('conditions'):return 'review','Matching free-text conditions require human verification'
    if a['scope'] != b['scope'] and 'all' not in (a['scope'],b['scope']):
        if 'generic-model' in (a['scope'],b['scope']): return 'review','Different employment or service models'
        return 'skip','Different service or product scopes'
    for key in ('product','jurisdiction','variant'):
        if a.get(key) and b.get(key) and a[key]!=b[key]:
            return 'skip',f'Different {key} values'
    # Dates: only claim historical succession when both ranges are explicit and nonoverlapping.
    a0,a1=a.get('effective_from'),a.get('effective_until')
    b0,b1=b.get('effective_from'),b.get('effective_until')
    if a1 and b0 and a1 < b0 or b1 and a0 and b1 < a0:
        return 'skip','Nonoverlapping effective dates'
    if a.get('measurement') != b.get('measurement'):
        return 'review','Measurement definitions differ or are unspecified'
    if a['scope']=='generic-model' or b['scope']=='generic-model':
        return 'review','Generic guidance may describe a different legal model'
    if (a.get('effective_from') and not b.get('effective_from')) or (b.get('effective_from') and not a.get('effective_from')):
        return 'review','One effective date is unspecified'
    return 'same','Comparable scope; source interpretation still requires review'

def analyze(claims):
    claims=validate_claims(claims)
    flags=[]; skipped=0
    for i,a in enumerate(claims):
        for b in claims[i+1:]:
            if a['company']!=b['company'] or a['topic']!=b['topic']: continue
            relation,comparison_reason=compare(a,b)
            if relation=='equal':continue
            rel,reason=_context(a,b)
            if relation=='review' and rel=='same':rel,reason='review',comparison_reason
            if rel=='same' and (a.get('verification_status')=='unverified' or b.get('verification_status')=='unverified'):
                rel,reason='review','Unverified extracted claim; human validation required'
            if rel=='skip': skipped+=1; continue
            # Version the finding by both underlying evidence records. A changed claim must not inherit a previous approval.
            fingerprint=hashlib.sha256(json.dumps([{'id':c['id'],'value':c['value'],'evidence':c['evidence'],'source_url':c['source_url'],'conditions':c.get('conditions',''),'effective_from':c.get('effective_from',''),'effective_until':c.get('effective_until','')} for c in sorted((a,b),key=lambda c:c['id'])],sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16]
            kind='verified_wording_conflict' if rel=='same' else 'needs_context'
            flags.append({'id':'--'.join(sorted([a['id'],b['id']]))+'--'+fingerprint, 'company':a['company'], 'topic':a['topic'],
                          'kind':kind,'priority':'high' if a['topic'] in HIGH_TOPICS else 'medium',
                          'reason':reason,'comparison':comparison_reason,
                          'left':{k:a.get(k,'') for k in ('id','value','evidence','source_url','observed','scope','language','authority')},
                          'right':{k:b.get(k,'') for k in ('id','value','evidence','source_url','observed','scope','language','authority')},
                          'caveat':'Public wording differs; actual applicability and consequences are unverified. Human review required.'})
    return {'claim_count':len(claims),'flag_count':len(flags),'issue_count':len({(f['company'],f['topic']) for f in flags}),
            'skipped_incomparable':skipped,'flags':flags,
            'limitations':['Structured claims are curated; no autonomous web extraction or legal determinations.',
                           'No measured customer harm, revenue loss, or operational defect.',
                           'Human approval is required before any policy correction.']}

def cancellation_scenario(hours, hourly_rate, booked_hours, fee_percent='90'):
    try: notice=Decimal(str(hours)); rate=Decimal(str(hourly_rate)); duration=Decimal(str(booked_hours)); penalty=Decimal(str(fee_percent))
    except InvalidOperation: raise ValueError('Invalid numeric input')
    if not all(x.is_finite() for x in (notice,rate,duration,penalty)): raise ValueError('Non-finite input')
    if not (0<=notice<=10000 and 0<rate<=10000 and 0<duration<=1000 and 0<=penalty<=100): raise ValueError('Values outside allowed ranges')
    money=lambda v:str(v.quantize(Decimal('.01'),rounding=ROUND_HALF_UP))
    booking=rate*duration
    advertised=Decimal(0) if notice>=24 else booking*penalty/100
    terms=Decimal(0) if notice>=48 else booking*penalty/100
    return {'booking_chf':money(booking),'article_interpretation_chf':money(advertised),'contract_terms_interpretation_chf':money(terms),
            'difference_chf':money(terms-advertised),'notice_hours':str(notice),'hypothetical':True,
            'warning':'Illustrative interpretation only; no actual charge or loss established.'}

def load_sample(path):
    with open(path,encoding='utf-8') as f: return validate_claims(json.load(f)['claims'])
