import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {Group,Mesh,BoxGeometry,MeshBasicMaterial} from './three.module.min.js';
import {createItemEdits,effectiveDeleted,bindItems,itemId,isVisible,editedNavigation,editedGLB} from './item-edit.js';
import {tvGLB,tvNavigation} from './tv-options.js';
import {modelChoice} from './model-options.js';
const catalog=JSON.parse(fs.readFileSync(new URL('./edit-catalog.json',import.meta.url)));
const read=name=>fs.readFileSync(new URL('./'+name,import.meta.url));
const decode=bytes=>{const n=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength).getUint32(12,true);return {g:JSON.parse(new TextDecoder().decode(bytes.subarray(20,20+n))),tail:bytes.subarray(20+n)};};
test('delete/undo/restore use independent snapshots and survive serialized reload',()=>{
 const edit=createItemEdits(catalog);assert.equal(edit.remove('walls'),false);assert.equal(edit.remove('lounge'),true);assert.equal(edit.remove('lounge'),false);
 assert.equal(edit.remove('sofa'),true);assert.ok(edit.undo());assert.deepEqual([...edit.deleted],['lounge']);
 const restored=createItemEdits(catalog,edit.serialize());assert.deepEqual([...restored.deleted],['lounge']);assert.equal(restored.canUndo,false);
 restored.restoreAll();assert.equal(restored.deleted.size,0);restored.undo();assert.ok(restored.deleted.has('lounge'));
 restored.restore('lounge');restored.undo();assert.ok(restored.deleted.has('lounge'));
 assert.equal(createItemEdits(catalog,'corrupt').deleted.size,0);
 assert.deepEqual([...createItemEdits(catalog,JSON.stringify({version:1,deleted:['lounge','made-up',null,'lounge']})).deleted],['lounge']);
});
test('removing a desk also removes supported devices without losing independent edits',()=>{
 const edit=createItemEdits(catalog);edit.remove('laptop');edit.remove('desk-lower');edit.restore('desk-lower');assert.ok(edit.effective.has('laptop'));
 edit.restoreAll();edit.remove('desk-lower');assert.ok(edit.effective.has('laptop'));edit.restore('desk-lower');assert.equal(edit.effective.size,0);
 assert.ok(effectiveDeleted(catalog,['dining-table']).has('vase'));
});
test('live matching survives GLTF name sanitizing, nested primitives and TV resizing',()=>{
 const root=new Group(),parent=new Group(),child=new Mesh(new BoxGeometry(),new MeshBasicMaterial());parent.userData.name='65英寸电视屏幕';parent.name='85英寸电视屏幕';parent.add(child);root.add(parent);
 bindItems(root,catalog.models['current-700'].members);assert.equal(itemId(child),'tv');assert.ok(isVisible(child));parent.visible=false;assert.equal(isVisible(child),false);
});
test('catalog groups complete objects and keeps chair instances and structure separate',()=>{
 for(const model of Object.values(catalog.models)){
  assert.equal(model.members['休闲椅坐垫'],'lounge');assert.equal(model.members['休闲椅左椅脚'],'lounge');assert.equal(model.members['回音壁'],'tv');
  assert.equal(model.members['装饰隔断实墙'],undefined);assert.equal(model.members['入户门拉手'],undefined);assert.equal(model.members['储物间柜门顶封'],undefined);
  const seats=Object.entries(model.members).filter(([n])=>n.startsWith('日常餐椅座面'));assert.equal(seats.length,4);assert.equal(new Set(seats.map(([,v])=>v)).size,4);
  const office=Object.entries(model.members).filter(([n])=>n.startsWith('人体工学椅座面'));assert.equal(new Set(office.map(([,v])=>v)).size,2);
  assert.ok(Object.entries(model.members).filter(([n,id])=>n.startsWith('人体工学椅脚轮')&&id===office[0][1]).length===5);
 }
});
test('overlapping remaining obstacles stay blocked; deleted TV no longer enlarges collision',()=>{
 const base={rows:['.###.'],editFixedRows:['....#'],itemObstacles:{a:[[0,1,3]],b:[[0,2,4]]},structureRows:['....#']};
 assert.strictEqual(editedNavigation(base,new Set()),base);
 assert.deepEqual(editedNavigation(base,new Set(['a'])).rows,['..###']);assert.deepEqual(editedNavigation(base,new Set(['a','b'])).rows,['....#']);
 const nav=JSON.parse(read('navigation.json')),removed=editedNavigation(nav,new Set(['tv']));
 const grown=tvNavigation(removed,85);assert.notDeepEqual(grown.rows,removed.rows);assert.strictEqual(removed.structureRows,nav.structureRows);
});
for(const layout of ['current','inset'])for(const width of [600,700,800])test(`${layout} ${width}: edits change export and collision, retain walls and original bytes`,()=>{
 const choice=modelChoice(width,layout),members=catalog.models[choice.key].members,raw=new Uint8Array(read(choice.model)),nav=JSON.parse(read(choice.navigation));
 const deleted=effectiveDeleted(catalog,['tv','lounge','desk-lower']);
 const nextNav=editedNavigation(nav,deleted);let freed=0;
 for(let y=0;y<nav.height;y++)for(let x=0;x<nav.width;x++){
  if(nav.editFixedRows[y][x]==='#')assert.equal(nextNav.rows[y][x],'#');
  if(nav.rows[y][x]==='#'&&nextNav.rows[y][x]==='.')freed++;
 }
 assert.ok(freed>30);assert.strictEqual(nextNav.structureRows,nav.structureRows);
 for(const size of [65,75,85]){
  const sized=tvGLB(raw,size),before=decode(sized),result=editedGLB(sized,members,deleted),after=decode(result);assert.deepEqual(after.tail,before.tail);
  let removed=0;
  before.g.nodes.forEach((node,i)=>{const n=after.g.nodes[i],key=node.name?.replace(/^\d+英寸电视/,'65英寸电视');
   if(deleted.has(members[key])&&'mesh'in node){assert.equal(n.mesh,undefined);removed++;const {mesh,...rest}=node;assert.deepEqual(n,rest);}else assert.deepEqual(n,node);
  });assert.ok(removed>=30);assert.equal(new DataView(result.buffer).getUint32(8,true),result.length);
 }
 assert.strictEqual(editedGLB(raw,members,new Set()),raw);
});
