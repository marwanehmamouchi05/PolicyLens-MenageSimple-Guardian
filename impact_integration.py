"""Guardian's evidence-scoped, session-local policy impact extension."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json
import re
from impact_graph import validate_dataset,build_graph,findings,impact,add_claim,simulate_claim_correction

ROOT=Path(__file__).resolve().parent
BASE=validate_dataset(json.loads((ROOT/'impact_evidence.json').read_text(encoding='utf-8')))

# The Guardian source register is authoritative for currently indexed quotations.
# The graph's historical and manually entered observations remain explicitly qualified.
def initial_data():
    from guardian import EXCERPTS
    data=deepcopy(BASE)
    for c in data['claims']:
        matches=[e for e in EXCERPTS.values() if e['url']==c['source_url'] and e['quote'].strip()==c['evidence'].strip()]
        if matches:
            e=matches[0]
            c['observed']=e['observed']
            c['status']='historical' if e.get('historical') else c.get('status','current')
            c['verification']='historical' if e.get('historical') else ('older_index' if not e.get('verified_in_current_capture',False) else 'fresh_index')
        elif c['verification']=='fresh_index' and not c.get('capture_sha256'):
            # Graph-only text has not been reconciled with Guardian's source register.
            c['verification']='older_index'
    data['metadata']['coverage']='Échantillon d’affirmations indexées : les observations sans concordance exacte dans le registre Guardian sont à revérifier.'
    return validate_dataset(data)

def get_data(app):
    if not hasattr(app,'impact_data') or app.impact_data is None:
        app.impact_data=initial_data()
    # Explicit adapters keep Guardian's local copies visible in the same session graph.
    data=app.impact_data
    from guardian import deadline, ORIGINAL
    snapshot=app.state['snapshot']
    historical=next(c for c in data['claims'] if c['id']=='CAN-PRIX-HIST')
    if snapshot['text']!=ORIGINAL:
        value=deadline(snapshot['text'])
        if value is not None:
            historical.update(value=str(value),simulation=True,recorded_value='24')
    else:
        historical.update(value='24',simulation=False)
    for info in app.state.get('information',[]):
        if info.get('category')!='cancellation':continue
        # The original entry point permits arbitrary declared URLs. Keep those findings
        # there; only supported MénageSimple references enter this bounded graph.
        from urllib.parse import urlsplit
        u=urlsplit(info['source_url'])
        if u.scheme!='https' or u.hostname not in ('menagesimple.com','www.menagesimple.com'):continue
        cid='guardian-'+info['id']
        item=dict(id=cid,topic='cancellation_hours',value=info['value'],scope=info['scope'],source_url=info['source_url'],evidence=info['excerpt'],observed=datetime.now(timezone.utc).date().isoformat(),verification='user_supplied',status='current',service_model='menagesimple',origin='guardian')
        try:validate_dataset({**data,'claims':[item]})
        except ValueError:continue
        existing=next((c for c in data['claims'] if c['id']==cid),None)
        if existing:existing.update(item)
        elif len(data['claims'])<77:data['claims'].append(item)
    return data

def state(app):
    d=get_data(app)
    proposals=getattr(app,'impact_proposals',{})
    result={'data':d,'graph':build_graph(d),'session_only':True,'proposals':deepcopy(proposals),'history':deepcopy(getattr(app,'impact_history',[]))}
    result['impacts']={topic:impact(d,topic,value) for topic,value in proposals.items()}
    return result

def reset(app):
    app.impact_data=initial_data()
    app.impact_proposals={}
    app.impact_history=[]
    return state(app)

def report(app):
    d=get_data(app);g=build_graph(d)
    return {'title':'PolicyLens Guardian — Rapport d’impact','generated_at':datetime.now(timezone.utc).isoformat(),
            'coverage':d['metadata'].get('coverage'),'summary':g['summary'],'findings':findings(d),
            'claims':d['claims'],'references':d['references'],
            'human_review':'Toute divergence demande une vérification humaine; les URL saisies ne sont pas consultées automatiquement.',
            'simulation':'Les corrections sont limitées à la session; aucune publication sur le site MénageSimple.',
            'history':deepcopy(getattr(app,'impact_history',[])),
            'proposals':deepcopy(getattr(app,'impact_proposals',{})),
            'impacts':state(app)['impacts']}

def action(app, name, body):
    if not isinstance(body,dict):raise ValueError('Les données doivent être un objet JSON.')
    if name=='reset':return reset(app)
    if name=='state':return state(app)
    d=get_data(app)
    history=getattr(app,'impact_history',[])
    if name in ('add','simulate') and len(history)>=100:raise ValueError('Limite de la session atteinte. Réinitialisez la démonstration.')
    if name=='impact':
        result=impact(d,body.get('topic'),body.get('proposed_value'))
        proposals=deepcopy(getattr(app,'impact_proposals',{}))
        if body.get('proposed_value') is None:proposals.pop(body['topic'],None)
        else:proposals[body['topic']]=result['proposed_value']
        app.impact_proposals=proposals
        return result
    if name=='add':
        c=deepcopy(body.get('claim'))
        if not isinstance(c,dict):raise ValueError('Une affirmation structurée est nécessaire.')
        # Never allow a manually entered claim to masquerade as independently verified.
        c.update(verification='user_supplied',status='current')
        if sum(x.get('verification')=='user_supplied' and x.get('origin')!='guardian' for x in d['claims'])>=30:raise ValueError('Cette démonstration est limitée à 30 informations ajoutées au graphe.')
        app.impact_data=add_claim(d,c)
        app.impact_history=history+[dict(time=datetime.now(timezone.utc).isoformat(),action='add',claim_id=c['id'],before=None,after=c['value'])]
        return state(app)
    if name=='simulate':
        original=next((c for c in d['claims'] if c['id']==body.get('claim_id')),None)
        if original and original['status']=='historical':
            raise ValueError('La preuve historique est conservée. Modifiez sa copie dans la rubrique Simulations.')
        before=original['value'] if original else None
        result=simulate_claim_correction(d,body.get('claim_id'),body.get('new_value'))
        if original and original.get('origin')=='guardian':
            info=next(i for i in app.state['information'] if 'guardian-'+i['id']==original['id'])
            app.information({**info,'value':body.get('new_value')})
        app.impact_data=result['data']
        app.impact_history=history+[dict(time=datetime.now(timezone.utc).isoformat(),action='simulate',claim_id=body.get('claim_id'),before=before,after=body.get('new_value'),resolved_ids=result['resolved_ids'],created_ids=result['created_ids'])]
        return {**result,'graph':build_graph(app.impact_data)}
    if name=='report':
        from impact_report_fr import export
        return {**report(app),'export_fr':export(state(app))}
    raise ValueError('Action inconnue.')
