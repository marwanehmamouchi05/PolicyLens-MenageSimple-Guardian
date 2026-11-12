'use strict';
// The overview is drawn exclusively from the same evidence graph as the comparisons.
(()=>{
 const $=s=>document.querySelector(s),names={'/conditions-generales/':'Conditions générales','/questions-frequentes-menage/':'Questions fréquentes','/prix-menage-domicile-suisse/':'Article tarifaire','/menage-regulier-lausanne/':'Service à Lausanne','/femme-de-menage-fully/':'Service à Fully','/femme-de-menage-rolle/':'Service à Rolle','/en/home-cleaning-french-speaking-switzerland/':'Guide en anglais','/':'Accueil'};
 let snapshot=null,mode='focus';
 const name=url=>names[new URL(url).pathname]||new URL(url).pathname;
 function view(next){mode=next;$('#graph-network').hidden=next!=='overview';$('#graph-overview-note').hidden=next!=='overview';$('#graph-workbench .impact-two').hidden=next==='overview';$('#graph-focus').setAttribute('aria-pressed',String(next==='focus'));$('#graph-overview').setAttribute('aria-pressed',String(next==='overview'));if(next==='overview')draw();}
 function draw(){
  if(!snapshot)return;const {data,current}=snapshot,root=$('#graph-network');root.replaceChildren();
  const policies=document.createElement('div'),pages=document.createElement('div');policies.className='network-policies';pages.className='network-pages';
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.classList.add('network-lines');svg.setAttribute('aria-hidden','true');root.append(svg,policies,pages);
  const urls=[...new Set(data.claims.map(c=>c.source_url))];
  for(const [id,p] of Object.entries(data.policies)){const b=document.createElement('button');b.type='button';b.className='network-policy';b.dataset.policy=id;b.classList.toggle('network-current',id===current);const title=document.createElement('strong');title.textContent=p.label;const meta=document.createElement('small');const n=new Set(data.claims.filter(c=>c.topic===id).map(c=>c.source_url)).size;meta.textContent=n+' pages reliées';b.append(title,meta);b.addEventListener('click',()=>{window.dispatchEvent(new CustomEvent('impact:select',{detail:id}));view('focus');});b.addEventListener('mouseenter',()=>highlight(id));b.addEventListener('focus',()=>highlight(id));policies.append(b);}
  for(const url of urls){const b=document.createElement('button');b.type='button';b.className='network-page';b.dataset.url=url;const title=document.createElement('strong');title.textContent=name(url);const count=new Set(data.claims.filter(c=>c.source_url===url).map(c=>c.topic)).size;const meta=document.createElement('small');meta.textContent=count+' règle'+(count===1?'':'s')+' à examiner';b.append(title,meta);b.addEventListener('click',()=>{const c=data.claims.find(c=>c.source_url===url&&c.topic===snapshot.current)||data.claims.find(c=>c.source_url===url);window.dispatchEvent(new CustomEvent('impact:select',{detail:c.topic}));view('focus');requestAnimationFrame(()=>$('#impact-graph [data-node-id="'+CSS.escape('page:'+url)+'"]')?.click());});pages.append(b);}
  const box=root.getBoundingClientRect();svg.setAttribute('viewBox',`0 0 ${box.width} ${box.height}`);
  for(const b of policies.children){const a=b.getBoundingClientRect();for(const url of new Set(data.claims.filter(c=>c.topic===b.dataset.policy).map(c=>c.source_url))){const target=[...pages.children].find(el=>el.dataset.url===url),z=target.getBoundingClientRect();const x=a.right-box.left,y=a.top+a.height/2-box.top,x2=z.left-box.left,y2=z.top+z.height/2-box.top,m=(x+x2)/2;const path=document.createElementNS(svg.namespaceURI,'path');path.setAttribute('d',`M${x},${y} C${m},${y} ${m},${y2} ${x2},${y2}`);path.dataset.policy=b.dataset.policy;svg.append(path);}}
  root.onmouseleave=()=>highlight(current);highlight(current);
 }
 function highlight(id){document.querySelectorAll('.network-lines path').forEach(p=>p.classList.toggle('network-active',p.dataset.policy===id));document.querySelectorAll('.network-policy').forEach(p=>p.classList.toggle('network-highlight',p.dataset.policy===id));}
 window.addEventListener('impact:graph',e=>{snapshot=e.detail;if(mode==='overview')requestAnimationFrame(draw)});
 window.addEventListener('impact:result',e=>{
  const r=e.detail,box=$('#graph-actions'),unverified=r.rows.filter(x=>x.verification==='not_verified'||x.verification==='older_index'),affected=r.rows.filter(x=>x.status==='ecart_potentiel');box.replaceChildren();$('#graph-clear-proposal').hidden=!$('#impact-proposed').value.trim();
  if(!affected.length&&!unverified.length)return;
  const heading=document.createElement('h3');heading.textContent=affected.length?'Votre liste de vérification':'Ces preuves demandent une nouvelle lecture';box.append(heading);
  const grouped=new Map();for(const row of affected.length?affected:unverified){if(!grouped.has(row.page_url))grouped.set(row.page_url,row);}
  for(const [url,row] of grouped){const line=document.createElement('div');line.className='graph-action-row';const title=document.createElement('strong');title.textContent=name(url);const p=document.createElement('p');p.textContent=row.review_action;const a=document.createElement('a');a.textContent='Vérifier la source';a.href=url;a.target='_blank';a.rel='noopener noreferrer';line.append(title,p,a);box.append(line);}
  const note=document.createElement('p');note.className='hint';note.textContent='Cette liste prépare une décision humaine. Elle ne modifie aucune page.';box.append(note);
 });
 $('#graph-focus').addEventListener('click',()=>view('focus'));$('#graph-overview').addEventListener('click',()=>view('overview'));
 $('#graph-example').addEventListener('click',()=>{window.dispatchEvent(new CustomEvent('impact:select',{detail:{topic:'cancellation_hours',proposed:'72'}}));view('focus');$('#impact-summary-line').scrollIntoView({block:'start',behavior:'smooth'});});
 $('#graph-clear-proposal').addEventListener('click',()=>{$('#impact-proposed').value='';$('#impact-update').click()});
 $('#graph-expand').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('#graph-workbench').requestFullscreen();}catch{$('#impact-message').textContent='Le plein écran est indisponible. La carte reste utilisable dans cette page.';}});
 document.addEventListener('fullscreenchange',()=>{$('#graph-expand').textContent=document.fullscreenElement?'Revenir à la page':'Agrandir la carte';if(mode==='overview')requestAnimationFrame(draw)});
 new ResizeObserver(()=>{if(mode==='overview')requestAnimationFrame(draw)}).observe($('#graph-workbench'));
})();
