"""Contextual employer review using the existing conservative comparison engine."""
from engine import analyze
def finding(excerpts,fingerprint):
    def c(cid,topic,value,scope,eid):
        e=excerpts[eid]
        return dict(id=cid,company='MénageSimple',topic=topic,value=value,scope=scope,source_url=e['url'],evidence=e['quote'],observed=e['observed'])
    claims=[c('guide-role','employer_role','not_specified_in_generic_guide','generic-model','english-model'),
            c('terms-role','employer_role','customer_is_legal_employer','regular','terms-employer'),
            c('faq-role','employer_role','customer_is_legal_employer','regular','faq-employer'),
            c('admin','administrative_manager','delegated_payment_administration','regular','terms-administration')]
    result=analyze(claims)
    # An unknown generic model can require context, never establish a legal contradiction.
    contextual=any(f['kind']=='needs_context' for f in result['flags'])
    return dict(id='employer',name="Qui est réellement l’employeur ?",policy='Responsabilités de l’employeur',severity='High',
      status='Clarity concern' if contextual else 'Insufficient evidence',evidence=['english-model','english-assurance','faq-employer','terms-employer','terms-administration'],
      explanation='Ambiguïté sur les responsabilités de l’employeur — clarification nécessaire. Le guide évoque une délégation complète à une agence ou entreprise. Les conditions et la FAQ attribuent le rôle d’employeur au client dans le modèle documenté de MénageSimple.',
      impact='Le client doit comprendre qui est l’employeur de l’aide ménagère, quelles démarches sont déléguées et quelles responsabilités lui restent attachées. Aucun manquement ni dommage réel n’est établi.',
      alternatives='Les deux textes peuvent décrire des modèles différents. Le guide actuel ne dit pas explicitement que l’entreprise est l’employeur légal. Confier la gestion administrative, les cotisations ou l’assurance ne transfère pas nécessairement ce rôle.',
      action='Demander au responsable : quel modèle s’applique précisément au service réservé par le client ? Préciser séparément l’employeur, le mandat administratif, les assurances et les responsabilités restantes.',
      suggestion='Clarification à obtenir, sans modification automatique du contrat : identifier l’employeur pour chaque service, les tâches confiées à MénageSimple, les assurances et cotisations gérées, et les obligations qui restent au client. Expliquer à quel modèle se rapporte le guide.',
      context=[dict(theme='Identité de l’employeur',article='Non précisée pour le modèle d’agence ; aucune désignation actuelle de l’entreprise comme employeur légal.',terms='Le client est employeur selon la FAQ et le modèle contractuel documenté.'),
               dict(theme='Gestion administrative',article='Le guide décrit une délégation complète.',terms='MénageSimple intervient sous mandat, notamment pour la gestion du paiement des salaires.'),
               dict(theme='Assurances et cotisations',article='La gestion de ces démarches est présentée comme prise en charge.',terms='Le mandat décrit des services administratifs ; leur gestion ne suffit pas à identifier l’employeur.'),
               dict(theme='Responsabilités contractuelles',article='Présentation générale ; portée à vérifier.',terms='Des responsabilités restent liées au cocontractant employeur et au contrat signé.')],
      check=result,claims=claims,fingerprint=fingerprint(claims))
