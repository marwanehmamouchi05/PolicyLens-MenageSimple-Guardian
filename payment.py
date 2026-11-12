"""Payment review from the same qualified evidence used by the impact graph."""
from copy import deepcopy

def finding(data,fingerprint):
    proofs=deepcopy([c for c in data['claims'] if c['topic']=='payment_arrangement'])
    uncertain=any(c['verification']!='fresh_index' for c in proofs)
    return dict(id='payment',name='Carte, virement ou espèces ?',policy='Moyens de paiement',severity='Review',
      status='Insufficient evidence' if uncertain else 'Clarity concern',evidence=[],proofs=proofs,
      explanation='Les conditions demandent une carte valide à la réservation. Des extraits antérieurement indexés annoncent aussi le virement ou les espèces, mais ils n’ont pas été retrouvés dans la lecture directe du 12 novembre. Leur origine reste à authentifier : aucun écart actuel n’est confirmé.',
      impact='Un client peut préparer un moyen de paiement qui n’est pas accepté pour sa réservation. Aucun refus de paiement réel n’a été constaté.',
      alternatives='Une carte de garantie et un autre mode de règlement peuvent coexister. Des modalités particulières peuvent aussi dépendre du service ou du lieu. L’absence actuelle des anciens extraits ne prouve pas quand ni pourquoi un texte aurait changé.',
      action='Vérifier les pages et le parcours de réservation, puis confirmer les moyens acceptés, la garantie demandée et les éventuelles exceptions.',
      suggestion='À faire confirmer : quels moyens de paiement sont acceptés pour chaque prestation ? La carte sert-elle de garantie, de moyen de règlement, ou des deux ? Préciser les exceptions avant de modifier les textes.',
      fingerprint=fingerprint(['payment',proofs]))
