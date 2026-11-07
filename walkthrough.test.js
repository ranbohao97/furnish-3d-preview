import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createWalkthrough} from './walkthrough.js';
import {isWalkable,navigationMode} from './navigation.js';

test('live configuration keeps pose, resolves new walls and freezes input while loading',()=>{
 class Element extends EventTarget{
  hidden=false;checked=false;value='';style={setProperty(){}};classList={add(){},remove(){}};
  closest(){return null;} setAttribute(){} focus(){} querySelector(){return new Element();}
 }
 const elements=new Map();const get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
 const previous={document:globalThis.document,window:globalThis.window,ResizeObserver:globalThis.ResizeObserver};
 globalThis.document=Object.assign(new Element(),{getElementById:get,querySelectorAll:()=>[],querySelector:()=>null,body:new Element()});
 globalThis.window=new Element();globalThis.ResizeObserver=class{observe(){}};
 try{
  const nav=JSON.parse(fs.readFileSync(new URL('./navigation-inset-700.json',import.meta.url)));
  const camera={position:{x:0,y:0,z:0,set(x,y,z){Object.assign(this,{x,y,z});}},rotation:{set(...args){this.values=args;}}};
  const canvas=new Element(),host=new Element();let exited=false;
  const walk=createWalkthrough({camera,canvas,nav,host,onEnter:()=>({}),onExit:()=>{exited=true;}});
  get('walk-through').checked=true;get('walk-start').dispatchEvent(new Event('click'));
  // Turning and walking use the real controller, not a copy of its math.
  const key=(type,code)=>window.dispatchEvent(Object.assign(new Event(type),{code}));
  key('keydown','ArrowLeft');walk.update(.05,200);key('keyup','ArrowLeft');
  const heading=[...camera.rotation.values],p={...camera.position};
  walk.setBusy(true);key('keydown','KeyW');walk.resume();walk.update(.05,400);
  assert.deepEqual({...camera.position},p,'busy controller must not move');
  Object.assign(nav,JSON.parse(fs.readFileSync(new URL('./navigation-600.json',import.meta.url))));
  assert.equal(walk.revalidatePosition(),false);assert.deepEqual({...camera.position},p);
  assert.deepEqual(camera.rotation.values,heading,'configuration must not rotate the camera');
  // This former open spot becomes a wall when switching inset -> current.
  camera.position.set(5.90,nav.eyeHeight,-7.05);
  assert.equal(isWalkable(navigationMode(nav,true),5.90,7.05),false);
  assert.equal(walk.revalidatePosition(),true);
  assert.ok(isWalkable(navigationMode(nav,true),camera.position.x,-camera.position.z));
  assert.ok(Math.hypot(camera.position.x-5.90,-camera.position.z-7.05)<.6,'relocation stays nearby');
  assert.deepEqual(camera.rotation.values,heading);
  walk.setBusy(false);walk.resume();const recovered={...camera.position};walk.update(.05,600);
  assert.deepEqual({...camera.position},recovered,'held keys are cleared across configuration');
  key('keydown','KeyW');walk.update(.05,800);key('keyup','KeyW');
  assert.ok(walk.active);
  const editPose={...camera.position},editHeading=[...camera.rotation.values];
  walk.setEditing(true);assert.ok(get('walk-pause').hidden,'editing hides the pause screen');
  key('keydown','KeyW');key('keydown','ArrowLeft');walk.resume();walk.update(.05,1000);
  assert.deepEqual({...camera.position},editPose);assert.deepEqual(camera.rotation.values,editHeading);
  walk.setEditing(false);assert.ok(get('walk-pause').hidden);walk.update(.05,1100);
  assert.deepEqual({...camera.position},editPose,'editing clears held movement keys');
  walk.exit();assert.ok(exited);assert.equal(walk.active,false);
 }finally{for(const [k,v]of Object.entries(previous)){if(v===undefined)delete globalThis[k];else globalThis[k]=v;}}
});
