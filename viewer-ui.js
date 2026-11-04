export function setupViewerUI(){
 const $=id=>document.getElementById(id);
 const panelOpen=open=>{document.body.classList.toggle('panel-open',open);$('panel-toggle').setAttribute('aria-expanded',String(open));$('panel-backdrop').hidden=!open;};
 $('panel-toggle').addEventListener('click',()=>panelOpen(!document.body.classList.contains('panel-open')));
 $('panel-backdrop').addEventListener('click',()=>panelOpen(false));
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.body.classList.contains('panel-open')){panelOpen(false);$('panel-toggle').focus();}});
 document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>panelOpen(false)));
 $('walk-start').addEventListener('click',()=>panelOpen(false));
 $('info-settings').addEventListener('click',()=>$('info').click());
 const tabs=['spaces','settings'];
 function activate(key,focus=false){
  for(const tab of tabs){const selected=tab===key;$(`tab-${tab}`).setAttribute('aria-selected',String(selected));$(`tab-${tab}`).tabIndex=selected?0:-1;$(`panel-${tab}`).hidden=!selected;}
  if(focus)$(`tab-${key}`).focus();
 }
 for(const tab of tabs){
  $(`tab-${tab}`).addEventListener('click',()=>activate(tab));
  $(`tab-${tab}`).addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();activate(e.key==='Home'?'spaces':e.key==='End'?'settings':tabs[1-tabs.indexOf(tab)],true);}});
 }
 // Discard the retired lighting preference; geometry preferences are independent.
 try{localStorage.removeItem('home3d.lighting.v1');}catch{}
}
