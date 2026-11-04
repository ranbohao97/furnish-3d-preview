import {TIMES} from './solar.js';
export function setupViewerUI(lighting){
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
 let state={date:'2026-11-04',period:'noon',indoor:true};
 try{
  const saved=JSON.parse(localStorage.getItem('home3d.lighting.v1'));
  if(saved && /^\d{4}-\d{2}-\d{2}$/.test(saved.date) && saved.date>='2020-01-01' && saved.date<='2100-12-31' && TIMES[saved.period] && typeof saved.indoor==='boolean'){
   lighting.update(saved);state={date:saved.date,period:saved.period,indoor:saved.indoor};
  }
 }catch{}
 function apply(){
  const d=lighting.update(state),t=TIMES[state.period];
  document.querySelectorAll('[data-period]').forEach(b=>{const on=b.dataset.period===state.period;b.classList.toggle('selected',on);b.setAttribute('aria-pressed',String(on));});
  $('indoor-light').checked=state.indoor;$('indoor-state').textContent=state.indoor?'已开启':'已关闭';$('solar-date').value=state.date;
  const direction=d.azimuth<135?'东南':d.azimuth<225?'南侧':'西南';
  $('sun-summary').textContent=d.altitude>0?`${direction}日光 · 高度角 ${d.altitude.toFixed(0)}°`:'太阳已落下 · 暮色环境';
  $('sun-date-label').textContent=`${Number(state.date.slice(5,7))} 月 ${Number(state.date.slice(8))} 日 · 杭州`;
  $('lighting-caption').textContent=`${state.date} · ${t.label} ${t.time} · 室内灯${state.indoor?'开启':'关闭'}`;
  try{localStorage.setItem('home3d.lighting.v1',JSON.stringify(state));}catch{}
 }
 document.querySelectorAll('[data-period]').forEach(b=>b.addEventListener('click',()=>{state.period=b.dataset.period;apply();}));
 $('indoor-light').addEventListener('change',e=>{state.indoor=e.target.checked;apply();});
 $('solar-date').addEventListener('change',e=>{
  const value=e.target.value;
  try{if(!value||!e.target.validity.valid)throw new Error('Date');lighting.update({...state,date:value});state.date=value;$('solar-feedback').hidden=true;apply();}
  catch{e.target.value=state.date;$('solar-feedback').textContent='请选择 2020—2100 年的有效日期，已保留原日照。';$('solar-feedback').hidden=false;}
 });
 apply();
}
