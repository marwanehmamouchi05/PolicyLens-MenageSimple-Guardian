"""French presentation only. Detection statuses remain stable in the core API."""
STATUS={'Wording inconsistency':'Écart de formulation','Clarity concern':'À clarifier','Insufficient evidence':'Informations insuffisantes','Resolved in simulation':'Résolu dans la simulation','Potential mismatch':'Écart potentiel','Compatible input':'Aucun écart sur ce contrôle'}
DECISIONS={'Accept':'Accepter','Edit':'Modifier','Reject':'Rejeter','Request clarification':'Demander une précision'}
SEVERITY={'High':'Élevée','Medium':'Modérée','Review':'À examiner'}
SOURCE_TITLES={'pricing':'Article tarifaire','terms':'Conditions générales','faq':'Questions fréquentes','home':'Accueil','english':'Guide en anglais'}
LIMITS=[
 'Extraits publics sélectionnés, revérifiés le 10 novembre 2026. Le cas d’annulation à 24 heures est historique, observé le 9 novembre ; la lecture directe du 10 novembre donne 48 heures. Le bouton de revérification ne consulte pas le site.',
 'Les conditions affichent le 15 juillet 2026. Les dates d’effet des articles, contrats signés, exceptions et facturations réelles restent à confirmer.',
 'Les nouvelles informations sont saisies par un réviseur. Leur URL est une référence déclarée, pas une preuve de leur présence sur la page.',
 'Les simulations et décisions restent locales. Aucune publication, surveillance autonome, perte mesurée ou infraction juridique n’est établie.'
]
COPY={
 'cancellation':dict(name='Annulation : 24 ou 48 heures ?',policy='Délai d’annulation',
 explanation='Cas historique : l’extrait du 9 novembre indiquait 24 heures, contre 48 heures dans les conditions et la FAQ. La lecture directe du 10 novembre donne désormais 48 heures. La simulation conserve l’ancien écart pour montrer le contrôle avant / après ; elle ne décrit pas un écart actuel confirmé.',
 impact='Un client qui annule entre 24 et 48 heures avant le ménage peut s’attendre à une gratuité alors qu’un autre texte prévoit des frais. À 36 heures, l’exemple de deux heures à CHF 43.90 illustre un écart de CHF 79.02.',
 alternatives='L’article peut concerner une ancienne règle, une exception ou un autre service. Les contrats signés prévalent selon les conditions générales. Leur application à une réservation réelle reste à confirmer.',
 action='Faire confirmer le délai, les frais et les exceptions par le responsable, puis harmoniser l’article, les conditions et la FAQ.'),
 'reference':dict(name='Un renvoi vers la mauvaise clause',policy='Conditions : section 7 → section 10',
 explanation='La section 7 renvoie les frais d’annulation au point 10d, consacré aux photographies. La clause d’annulation se trouve au point 10c.',
 impact='Le client ou le support qui suit ce renvoi arrive sur une règle sans rapport avec les frais recherchés.',
 alternatives='La section 7 traite notamment des annulations liées au paiement. Vérifier si ce contexte justifie une clause distincte et quelle version doit s’appliquer.',
 action='Confirmer la clause visée puis remplacer le renvoi 10d par 10c si cette référence est bien celle attendue.'),
 'equipment':dict(name='Qui fournit les produits de nettoyage ?',policy='Produits et matériel selon le service',
 explanation='L’accueil et la FAQ en français incluent les produits. Le guide anglais demande au client de fournir les produits de base. L’accueil précise désormais que le client prévoit son aspirateur et son balai-serpillière pour un ménage standard.',
 impact='Selon la langue consultée, le client peut préparer des fournitures différentes avant la visite. Aucun incident réel n’a été constaté dans cet audit.',
 alternatives='Les produits ne sont pas le matériel. Le matériel du nettoyage de fin de bail et certaines options peuvent être inclus : cela peut expliquer une partie des différences.',
 action='Confirmer les fournitures par type de service, puis mettre le guide anglais en cohérence avec les informations françaises.',
 suggestion='Après confirmation : les produits de nettoyage sont inclus. Pour un ménage standard, prévoyez votre aspirateur et votre balai-serpillière ; vérifiez les options de matériel à la réservation. Pour une fin de bail, les produits et le matériel sont inclus. Préciser les exceptions éventuelles.')
}
def describe(f):
    d={k:f[k] for k in ('name','policy','explanation','impact','alternatives','action','suggestion')}
    d.update(COPY.get(f['id'],{}));d['status']=STATUS[f['status']];d['severity']=SEVERITY.get(f['severity'],f['severity'])
    if f.get('historical') and f['status']=='Wording inconsistency':d['status']='Écart historique à simuler'
    return d
