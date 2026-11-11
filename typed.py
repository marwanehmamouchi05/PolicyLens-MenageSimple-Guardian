"""Conservative, company-agnostic typed quantities; never infer a currency exchange."""
import re
from decimal import Decimal, InvalidOperation

WORDS={'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18,'nineteen':19,'twenty':20,'thirty':30,'forty':40,'fifty':50,'sixty':60}
UNITS={'h':('time','hour',Decimal(60)),'hr':('time','hour',Decimal(60)),'hour':('time','hour',Decimal(60)),'hours':('time','hour',Decimal(60)),'heures':('time','hour',Decimal(60)),'minute':('time','minute',Decimal(1)),'minutes':('time','minute',Decimal(1)),'min':('time','minute',Decimal(1)),'day':('time','day',Decimal(1440)),'days':('time','day',Decimal(1440)),'jour':('time','day',Decimal(1440)),'jours':('time','day',Decimal(1440)),'month':('calendar','month',Decimal(1)),'months':('calendar','month',Decimal(1)),'kg':('mass','kg',Decimal(1000)),'g':('mass','g',Decimal(1)),'m²':('area','m2',Decimal(1)),'m2':('area','m2',Decimal(1)),'%':('percent','%',Decimal(1)),'guest':('count','guest',Decimal(1)),'guests':('count','guest',Decimal(1)),'bedroom':('count','bedroom',Decimal(1)),'bedrooms':('count','bedroom',Decimal(1)),'room':('count','room',Decimal(1)),'rooms':('count','room',Decimal(1)),'bag':('count','bag',Decimal(1)),'bags':('count','bag',Decimal(1)),'chf':('money','CHF',Decimal(1)),'eur':('money','EUR',Decimal(1)),'usd':('money','USD',Decimal(1))}
# Explicit topic names carry semantic units when the value has no suffix.
def inferred(topic):
    t=topic.lower()
    if t.endswith('_days'):return 'days'
    if t.endswith('_hours'):return 'hours'
    if t.endswith('_percent'):return '%'
    if t.endswith('_m2'):return 'm2'
    if 'bedroom' in t:return 'bedroom'
    if 'guest' in t:return 'guest'
    if 'bag' in t:return 'bag'
    return None

def parse(value,topic='',unit=None,value_type=None):
    if not isinstance(value,str):return ('unsupported',str(value))
    s=' '.join(value.strip().casefold().split())
    if s in WORDS:s=str(WORDS[s])
    if s in ('true','yes','oui'):return ('bool',True)
    if s in ('false','no','non'):return ('bool',False)
    m=re.fullmatch(r'([+-]?(?:\d+(?:[.,]\d+)?|(?:'+ '|'.join(WORDS)+r')))(?:\s*([%\w²]+))?',s)
    if m:
        raw=m.group(1); rawnum=WORDS.get(raw)
        try:n=Decimal(raw.replace(',','.')) if rawnum is None else Decimal(rawnum)
        except InvalidOperation:return ('unsupported',s)
        if not n.is_finite():return ('unsupported',s)
        suffix=m.group(2)
        explicit=(unit or '').casefold() or None
        assumed=inferred(topic)
        u=(suffix or explicit or assumed or '').casefold()
        if suffix and explicit and suffix != explicit:
            # Only allow compatible units with an explicit conversion.
            if suffix not in UNITS or explicit not in UNITS or UNITS[suffix][0]!=UNITS[explicit][0]:return ('ambiguous',s)
        if u and u not in UNITS:return ('unsupported',s)
        if u:
            dimension,semantic,factor=UNITS[u]
            if dimension=='count' and assumed and assumed in UNITS and UNITS[assumed][1]!=semantic:return ('ambiguous',s)
            if dimension=='calendar':return ('calendar',n,semantic)
            return ('quantity',dimension,semantic if dimension in ('count','money') else '',n*factor)
        return ('quantity','scalar','',n)
    return ('text',s)

def compare(a,b):
    x=parse(a['value'],a.get('topic',''),a.get('unit'),a.get('value_type'))
    y=parse(b['value'],b.get('topic',''),b.get('unit'),b.get('value_type'))
    if x[0] in ('unsupported','ambiguous') or y[0] in ('unsupported','ambiguous'):
        return ('review','Unrecognized or ambiguous quantity; human verification required')
    if x==y:return ('equal','Equivalent normalized values')
    if x[0]=='quantity' and y[0]=='quantity':
        if x[1:3]!=y[1:3]:return ('review','Units, currencies, or measurement categories differ')
        return ('different','Comparable quantities differ')
    if x[0]=='calendar' or y[0]=='calendar':return ('review','Calendar months cannot be equated to fixed day counts')
    if x[0]!=y[0]:return ('review','Incompatible value types')
    if x[0]=='text':return ('review','Different natural-language statements require contextual interpretation')
    return ('different','Comparable values differ')
