'use strict';
// A small view controller: the same application and state, one task on screen.
(()=>{
 const $=s=>document.querySelector(s);
 const targets={top:'home',findings:'findings',impact:'impact','impact-list':'impact',try:'try',simulation:'try','new-analysis':'try',calculator:'try',reports:'reports'};
 const toolFor={simulation:'correction','new-analysis':'information',calculator:'calculator'};
 function tool(name){
  document.querySelectorAll('[data-tool-panel]').forEach(p=>p.hidden=p.dataset.toolPanel!==name);
  document.querySelectorAll('[data-tool]').forEach(b=>{const active=b.dataset.tool===name;b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1;});
 }
 function route(hash,update=true){
  const id=(hash||'#top').replace('#',''),name=targets[id]||'home';
  document.querySelectorAll('[data-view]').forEach(s=>s.hidden=s.dataset.view!==name);
  if(name==='try')tool(toolFor[id]||'correction');
  document.querySelectorAll('#main-nav a').forEach(a=>{const active=targets[a.hash.slice(1)]===name;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  $('#main-nav').classList.remove('is-open');$('#menu-toggle').setAttribute('aria-expanded','false');
  if(update&&location.hash!=='#'+id)history.pushState(null,'','#'+id);
  window.scrollTo({top:0,behavior:'instant'});
  if(id==='impact-list')$('#impact-table-details').open=true;
 }
 document.addEventListener('click',e=>{
  const a=e.target.closest('a[href^="#"]');if(!a)return;
  if(targets[a.hash.slice(1)]){e.preventDefault();route(a.hash);}
 });
 window.addEventListener('hashchange',()=>route(location.hash,false));
 window.addEventListener('popstate',()=>route(location.hash,false));
 $('#menu-toggle').addEventListener('click',()=>{const open=$('#main-nav').classList.toggle('is-open');$('#menu-toggle').setAttribute('aria-expanded',String(open));});
 $('#demo-reference').addEventListener('click',()=>route('#findings'));
 $('#home-reference').addEventListener('click',()=>{$('#demo-reference').click();});
 document.querySelectorAll('[data-tool]').forEach((b,i,all)=>{
  b.addEventListener('click',()=>tool(b.dataset.tool));
  b.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const n=e.key==='Home'?0:e.key==='End'?all.length-1:(i+(e.key==='ArrowRight'?1:-1)+all.length)%all.length;tool(all[n].dataset.tool);all[n].focus();});
 });
 window.addEventListener('guardian:state',()=>{
  const a=$('#metric-open').textContent,b=$('#metric-clarify').textContent;
  $('#home-state').textContent=a+' point'+(a==='1'?'':'s')+' à examiner · '+b+' point'+(b==='1'?'':'s')+' à clarifier';
 });
 const names={'/conditions-generales/':'Conditions générales','/questions-frequentes-menage/':'Questions fréquentes','/prix-menage-domicile-suisse/':'Article tarifaire','/menage-regulier-lausanne/':'Service à Lausanne','/femme-de-menage-fully/':'Service à Fully','/femme-de-menage-rolle/':'Service à Rolle','/en/home-cleaning-french-speaking-switzerland/':'Guide en anglais','/':'Accueil'};
 window.addEventListener('impact:result',e=>{
  const r=e.detail,rows=r.rows.filter(x=>x.source_status!=='historical'),pages=[...new Set(rows.map(x=>x.page_url))],affected=rows.filter(x=>x.status==='ecart_potentiel'),line=$('#impact-summary-line');
  const n=affected.length?new Set(affected.map(x=>x.page_url)).size:pages.length;line.textContent=affected.length?n+' page'+(n===1?'':'s')+' à réexaminer si cette règle est confirmée.':n+' page'+(n===1?' reliée':'s reliées')+' à cette règle. Cliquez pour lire ce qu’elles indiquent.';
  const list=$('#impact-page-list');list.replaceChildren();
  for(const url of pages){const rs=rows.filter(x=>x.page_url===url),row=rs[0];const b=document.createElement('button');b.type='button';b.className='linked-page-row';const n=document.createElement('span');n.textContent=names[new URL(url).pathname]||new URL(url).pathname;const st=document.createElement('span');st.className='page-status';st.textContent=rs.some(x=>x.status==='ecart_potentiel')?'À réexaminer':rs.every(x=>x.status==='conforme')?'Valeur alignée':'Contexte à vérifier';b.append(n,st);b.addEventListener('click',()=>{const node=[...document.querySelectorAll('#impact-graph [data-node-id]')].find(x=>x.dataset.nodeId==='page:'+url);if(node)node.click();});list.append(b);}
 });
 route(location.hash||'#top',false);
})();
