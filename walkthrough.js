import {moveOnGrid,movementVector} from './navigation.js';
export function createWalkthrough({camera,canvas,nav,host,onEnter,onExit}){
 const $=id=>document.getElementById(id),keys=new Set();
 let active=false,paused=false,yaw=0,pitch=0,drag=null,saved=null,lastHud=0;
 const startButton=$('walk-start'),bar=$('walk-bar'),pausePanel=$('walk-pause');
 $('walk-lock').hidden=typeof canvas.requestPointerLock!=='function';
 canvas.tabIndex=0;canvas.setAttribute('aria-label','三维画面；漫游中使用 WASD 行走，方向键转头');
 function orient(){camera.rotation.set(pitch,yaw,0,'YXZ');}
 function clear(){keys.clear();drag=null;}
 function hud(){
  $('walk-position').textContent=`视高 1.60 m · 位置 ${camera.position.x.toFixed(2)}, ${(-camera.position.z).toFixed(2)} m`;
  $('walk-input').textContent=document.pointerLockElement===canvas?'WASD 行走 · 鼠标转头 · Esc 暂停':'WASD 行走 · 拖动画面转头 · ← → 转向 · Esc 暂停';
  pausePanel.hidden=!active||!paused;
 }
 function unlock(){if(document.pointerLockElement===canvas)document.exitPointerLock();}
 function pause(){if(!active)return;paused=true;clear();unlock();hud();}
 function relocate(key){
  $('walk-room').value=key;const s=nav.starts[key]||nav.starts.entry;camera.position.set(s.x,nav.eyeHeight,-s.y);
  yaw=({kitchen:Math.PI,guest:Math.PI,bath:Math.PI,basin:2.2,laundry:-Math.PI/2})[key]||0;pitch=0;orient();clear();hud();
 }
 function enter(){
  if(active)return;
  saved=onEnter();active=true;paused=false;host.classList.add('walking');document.body.classList.add('walk-mode');
  startButton.hidden=true;bar.hidden=false;$('selection').hidden=true;relocate('entry');canvas.focus();
 }
 function exit(){
  if(!active)return;active=false;paused=false;clear();unlock();host.classList.remove('walking');document.body.classList.remove('walk-mode');
  startButton.hidden=false;bar.hidden=true;pausePanel.hidden=true;onExit(saved);startButton.focus();
 }
 function resume(){paused=false;clear();canvas.focus();hud();}
 async function lockMouse(){
  if(!active)return;resume();
  try{await canvas.requestPointerLock();}catch{hud();$('walk-input').textContent='当前浏览器未启用鼠标锁定，可拖动画面转头，WASD 行走。';}
 }
 function advance(forward,right,dt){
  const delta=movementVector(yaw,forward,right,1.15*dt);
  const next=moveOnGrid(nav,{x:camera.position.x,y:-camera.position.z},delta.x,delta.y);
  camera.position.set(next.x,nav.eyeHeight,-next.y);
 }
 const moveKeys=new Set(['KeyW','KeyA','KeyS','KeyD','ArrowLeft','ArrowRight','ArrowUp','ArrowDown']);
 window.addEventListener('keydown',e=>{
  if(!active)return;
  if(e.code==='Escape'){e.preventDefault();pause();return;}
  if(paused||e.ctrlKey||e.metaKey||e.altKey||e.target.closest('button,input,select,textarea,dialog'))return;
  if(moveKeys.has(e.code)){e.preventDefault();keys.add(e.code);}
 });
 window.addEventListener('keyup',e=>keys.delete(e.code));
 window.addEventListener('blur',pause);
 document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});
 document.addEventListener('pointerlockchange',()=>{if(active&&document.pointerLockElement!==canvas)pause();hud();});
 document.addEventListener('pointerlockerror',()=>{if(active){resume();$('walk-input').textContent='请拖动画面转头；WASD 行走仍可使用。';}});
 document.addEventListener('mousemove',e=>{
  if(active&&!paused&&document.pointerLockElement===canvas){yaw-=e.movementX*.0022;pitch=Math.max(-1.25,Math.min(1.25,pitch-e.movementY*.0022));orient();}
 });
 canvas.addEventListener('pointerdown',e=>{if(active&&!paused&&document.pointerLockElement!==canvas){canvas.focus();drag={id:e.pointerId,x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);}});
 canvas.addEventListener('pointermove',e=>{
  if(!active||paused||!drag||drag.id!==e.pointerId)return;
  yaw-=(e.clientX-drag.x)*.004;pitch=Math.max(-1.25,Math.min(1.25,pitch-(e.clientY-drag.y)*.004));drag.x=e.clientX;drag.y=e.clientY;orient();
 });
 for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,()=>drag=null);
 for(const b of document.querySelectorAll('[data-walk-key]')){
  b.addEventListener('pointerdown',e=>{if(!active||paused)return;e.preventDefault();canvas.focus();keys.add(b.dataset.walkKey);b.setPointerCapture(e.pointerId);});
  for(const event of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(event,()=>keys.delete(b.dataset.walkKey));
  // Keyboard activation of on-screen movement buttons gives a small, predictable step.
  b.addEventListener('click',e=>{if(e.detail===0&&active&&!paused){const k=b.dataset.walkKey;if(k==='ArrowLeft'||k==='ArrowRight'){yaw+=(k==='ArrowLeft'?1:-1)*.18;orient();}else advance(k==='KeyW'?1:k==='KeyS'?-1:0,k==='KeyD'?1:k==='KeyA'?-1:0,.18);hud();}});
 }
 startButton.addEventListener('click',enter);$('walk-exit').addEventListener('click',exit);$('walk-lock').addEventListener('click',lockMouse);
 $('walk-resume').addEventListener('click',resume);$('walk-stop').addEventListener('click',exit);$('walk-home').addEventListener('click',()=>{relocate('entry');resume();});
 $('walk-room').addEventListener('change',e=>{relocate(e.target.value);resume();});
 return {get active(){return active;},pause,exit,update(dt,now){
  if(!active||paused)return;
  dt=Math.min(dt,.05);yaw+=((keys.has('ArrowLeft')?1:0)-(keys.has('ArrowRight')?1:0))*dt*1.5;
  pitch=Math.max(-1.25,Math.min(1.25,pitch+((keys.has('ArrowUp')?1:0)-(keys.has('ArrowDown')?1:0))*dt*1.1));orient();
  advance((keys.has('KeyW')?1:0)-(keys.has('KeyS')?1:0),(keys.has('KeyD')?1:0)-(keys.has('KeyA')?1:0),dt);
  if(now-lastHud>120){hud();lastHud=now;}
 }};
}
