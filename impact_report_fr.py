"""French presentation adapter; comparison and graph objects remain language-neutral."""
import html
from impact_graph import impact

STATUSES={'conforme':'Valeur alignée','historique':'Source historique','a_verifier':'À vérifier','ecart_potentiel':'Écart potentiel','reference_incorrecte':'Renvoi incorrect'}
VERIFY={'fresh_index':'Citation retrouvée dans la capture datée','older_index':'Index antérieur à revérifier','not_verified':'Extrait non retrouvé dans la dernière capture','historical':'Preuve historique','user_supplied':'Information fournie par le réviseur, non vérifiée'}
VALUES={'client_employeur':'Client employeur','gestion_administrative_deleguee':'Gestion administrative déléguée','entreprise_employeur':'Entreprise employeur : interprétation à confirmer','aucune_responsabilite_employeur_client':'Absence de responsabilité employeur annoncée','client_fournit_aspirateur':'Aspirateur fourni par le client','prestataire_entierement_equipe':'Prestataire annoncé équipé','produits_inclus':'Produits inclus','client_fournit_produits':'Produits fournis par le client','carte_requise_reservation':'Carte requise à la réservation','carte_virement_especes':'Carte, virement ou espèces annoncés'}
SCOPES={'regular':'Ménage régulier','all':'Toutes prestations : portée à confirmer','other':'Service non déterminé','generic-model':'Modèle générique'}
def value(v):return VALUES.get(str(v),str(v))

def export(state):
    data=state.get('data',{})
    if not data:return {}
    proposals=state.get('proposals',{})
    policies=[]
    for topic,p in data['policies'].items():
        result=impact(data,topic,proposals.get(topic))
        rows=[]
        for r in result['rows']:
            rows.append(dict(identifiant=r['claim_id'],url_source=r['page_url'],valeur_de_travail=value(r['value']),valeur_initialement_indexee=value(r['recorded_value']),citation_originale=r['evidence'],date_observation=r['observed'],service=SCOPES.get(r['scope'],r['scope']),region=r['region'],statut=STATUSES[r['status']],verification=VERIFY[r['verification']],precision_sur_la_preuve=r['verification_note'],modification_simulee=r['simulation'],action_recommandee=r['review_action']))
        policies.append(dict(politique=p['label'],reference_indexee=value(result['reference_value']),hypothese_simulee=value(result['proposed_value']) if topic in proposals else None,references_indexees=rows,renvois_contractuels=[dict(clause_source=r['source_clause'],clause_visee=r['target_clause'],candidats_attendus=r['expected_targets'],statut=STATUSES[r['status']],url_source=r['page_url'],citation=r['evidence']) for r in result['contract_references']]))
    return dict(portee=data['metadata']['coverage'],politiques=policies,historique=[dict(date=h['time'],action='Ajout fourni par le réviseur' if h['action']=='add' else 'Correction simulée',identifiant=h['claim_id'],avant=value(h['before']) if h['before'] is not None else None,apres=value(h['after']),comparaisons_resolues=h.get('resolved_ids',[]),comparaisons_creees=h.get('created_ids',[])) for h in state.get('history',[])],limite='Analyse des seules références indexées. Une valeur alignée ou une simulation ne vérifie pas une page en ligne et ne confirme pas la règle d’une réservation réelle.')

def render(state):
    report=export(state)
    if not report:return ''
    e=lambda x:html.escape(str(x),quote=True)
    blocks=['<section><h2>Graphe des politiques et analyse d’impact</h2><p>'+e(report['portee'])+'</p>']
    for p in report['politiques']:
        blocks.append('<h3>'+e(p['politique'])+'</h3><p>Référence indexée : '+e(p['reference_indexee'])+('. Hypothèse simulée : '+e(p['hypothese_simulee']) if p['hypothese_simulee'] is not None else '')+'.</p>')
        for r in p['references_indexees']:
            blocks.append('<div class="quote"><b>'+e(r['statut'])+(' · Valeur simulée' if r['modification_simulee'] else '')+'</b><p>Valeur de travail : '+e(r['valeur_de_travail'])+' ; valeur initiale : '+e(r['valeur_initialement_indexee'])+'.</p><blockquote>'+e(r['citation_originale'])+'</blockquote><a href="'+e(r['url_source'])+'">'+e(r['url_source'])+'</a><small>Observation : '+e(r['date_observation'])+' · '+e(r['service'])+' · '+e(r['verification'])+'</small><p>'+e(r['precision_sur_la_preuve'])+'</p><p>Action : '+e(r['action_recommandee'])+'</p></div>')
        for r in p['renvois_contractuels']:
            blocks.append('<p><b>'+e(r['statut'])+'</b> : §'+e(r['clause_source'])+' → §'+e(r['clause_visee'])+'. Référence attendue à confirmer : '+e(', '.join(r['candidats_attendus']))+'.</p>')
    blocks.append('<h3>Historique des corrections du graphe</h3>')
    for h in report['historique']:
        blocks.append('<p>'+e(h['date'])+' · '+e(h['action'])+' · '+e(h['identifiant'])+' : '+e(h['avant'])+' → '+e(h['apres'])+'.</p>')
    if not report['historique']:blocks.append('<p>Aucune modification du graphe dans cette session.</p>')
    blocks.append('<p>'+e(report['limite'])+'</p></section>')
    return ''.join(blocks)
