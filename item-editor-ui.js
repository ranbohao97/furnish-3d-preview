import * as THREE from './three.module.min.js';
import {createItemEdits,EDIT_STORAGE_KEY,itemId,isVisible,effectiveDeleted} from './item-edit.js';
export function createItemEditor({scene,camera,canvas,catalog,getModel,getWalk,isBusy,onChange}){
 const $=id=>document.getElementById(id);let stored='';try{stored=localStorage.getItem(EDIT_STORAGE_KEY)||'';}catch{}
 const edits=createItemEdits(catalog,stored),panel=$('item-editor');let selected=null,editing=false,down=null,dragged=false,pointerId=null;const pointers=new Set();
 const ray=new THREE.Raycaster(),pointer=new THREE.Vector2(),overlay=new THREE.Group();scene.add(overlay);
 const tint=new THREE.MeshBasicMaterial({color:0xd18c30,transparent:true,opacity:.22,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-1});
 const outline=new THREE.Box3Helper(new THREE.Box3(),0xd18c30);outline.material.depthTest=false;outline.renderOrder=130;scene.add(outline);outline.visible=false;
 function highlight(){
  overlay.clear();outline.visible=false;if(!selected)return;
  const ids=effectiveDeleted(catalog,[selected]),box=new THREE.Box3();getModel()?.updateMatrixWorld(true);
  getModel()?.traverse(o=>{if(!o.isMesh||!ids.has(itemId(o))||!isVisible(o))return;
   const mesh=new THREE.Mesh(o.geometry,tint);mesh.matrixAutoUpdate=false;mesh.matrix.copy(o.matrixWorld);mesh.renderOrder=125;overlay.add(mesh);
   if(!o.geometry.boundingBox)o.geometry.computeBoundingBox();box.union(o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld));
  });
  if(!box.isEmpty()){outline.box.copy(box);outline.visible=true;}
 }
 function renderList(){
  const list=$('deleted-items');list.replaceChildren();const ids=[...edits.deleted];
  $('deleted-count').textContent=ids.length?`已删除 ${ids.length} 件 · 仅保存在此浏览器`:'尚未删除物品';
  for(const id of ids){const li=document.createElement('li'),name=document.createElement('span'),button=document.createElement('button');name.textContent=catalog.items[id].label;button.textContent='恢复';button.className='plain';button.setAttribute('aria-label','恢复'+catalog.items[id].label);button.addEventListener('click',()=>change(()=>edits.restore(id),'已恢复'+catalog.items[id].label));li.append(name,button);list.append(li);}
  $('item-undo').disabled=!edits.canUndo;$('item-restore-all').disabled=!ids.length;
  $('deleted-open').textContent=ids.length?`已删除 ${ids.length}`:'已删除物品';
 }
 function sync(){
  $('item-selected').textContent=selected?catalog.items[selected].label:'点选一件家具或物品';
  $('item-context').textContent=selected?`${catalog.items[selected].room} · 高亮部分将一起移除`:(getWalk()?.active?'轻点选择物品；完成编辑后继续走动和转头。':'拖动调整视角，轻点选中；墙体、门窗和管道保留。');
  $('item-delete').disabled=!selected||isBusy();renderList();highlight();
 }
 function clear(){selected=null;highlight();if(editing)sync();}
 function change(action,message){
  if(isBusy()||!action())return;selected=null;
  let saved=true;try{localStorage.setItem(EDIT_STORAGE_KEY,edits.serialize());}catch{saved=false;}
  onChange();sync();$('item-feedback').textContent=message+(saved?'':'；浏览器存储不可用，仅本次有效。');
 }
 function setEditing(value){
  if(isBusy())return;editing=!!value;panel.hidden=!editing;document.body.classList.toggle('item-editing',editing);
  document.querySelectorAll('[data-item-edit]').forEach(b=>b.setAttribute('aria-pressed',String(editing)));
  if(editing){$('deleted-panel').hidden=true;getWalk()?.setEditing(true);$('item-feedback').textContent=getWalk()?.active?'已暂停行走。轻点选择物品，完成后返回漫游。':'轻点选择整件物品，Delete 删除，⌘ / Ctrl + Z 撤销。';sync();}
  else{clear();getWalk()?.setEditing(false);}
 }
 function pick(e){
  if(!editing||isBusy()||!getModel()||e.button!==0||dragged)return;
  const r=canvas.getBoundingClientRect();pointer.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(pointer,camera);
  // The first visible surface occludes objects behind it, even when protected.
  const hit=ray.intersectObject(getModel(),true).find(h=>isVisible(h.object));selected=hit?itemId(hit.object):null;
  if(selected&&edits.effective.has(selected))selected=null;sync();
  $('item-feedback').textContent=selected?'已选中。删除可随时撤销。':hit?'这是固定结构，不能作为物品删除。':'未选中物品。';
 }
 canvas.addEventListener('pointerdown',e=>{pointers.add(e.pointerId);if(pointers.size>1){dragged=true;return;}if(e.button!==0)return;pointerId=e.pointerId;down=[e.clientX,e.clientY];dragged=false;});
 canvas.addEventListener('pointermove',e=>{if(down&&e.pointerId===pointerId&&Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)dragged=true;});
 canvas.addEventListener('pointerup',e=>{if(down&&e.pointerId===pointerId&&pointers.size===1)pick(e);pointers.delete(e.pointerId);down=null;pointerId=null;});
 canvas.addEventListener('pointercancel',e=>{pointers.delete(e.pointerId);down=null;pointerId=null;});
 document.querySelectorAll('[data-item-edit]').forEach(b=>b.addEventListener('click',()=>setEditing(!editing)));
 $('item-done').addEventListener('click',()=>setEditing(false));
 $('item-delete').addEventListener('click',()=>{if(selected){const id=selected;change(()=>edits.remove(id),'已删除'+catalog.items[id].label+'，可撤销。');}});
 $('item-undo').addEventListener('click',()=>change(()=>edits.undo(),'已撤销上一步操作。'));
 $('item-restore-all').addEventListener('click',()=>change(()=>edits.restoreAll(),'已恢复全部物品，可撤销本次恢复。'));
 $('deleted-open').addEventListener('click',()=>{$('deleted-panel').hidden=!$('deleted-panel').hidden;});
 window.addEventListener('keydown',e=>{
  if(!editing||isBusy()||document.querySelector('dialog[open]')||e.target.closest('input,select,textarea,[contenteditable="true"]'))return;
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'){e.preventDefault();change(()=>edits.undo(),'已撤销上一步操作。');}
  else if(['Delete','Backspace'].includes(e.key)&&selected){e.preventDefault();$('item-delete').click();}
  else if(e.key==='Escape'){e.preventDefault();setEditing(false);}
 });
 window.addEventListener('storage',e=>{if(e.key===EDIT_STORAGE_KEY)$('item-feedback').textContent='其他页面修改了物品；刷新后载入最新记录。';});
 sync();return {get active(){return editing;},get deleted(){return edits.effective;},clear,refresh:sync,close:()=>setEditing(false),setBusy(value){panel.inert=value;document.querySelectorAll('[data-item-edit]').forEach(b=>b.disabled=value);}};
}
