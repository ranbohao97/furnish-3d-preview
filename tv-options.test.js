import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {Group,Object3D} from './three.module.min.js';
import {tvSpec,applyTVSize,tvNavigation,tvGLB} from './tv-options.js';
import {isWalkable,navigationMode} from './navigation.js';
const decode=bytes=>{const length=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength).getUint32(12,true);return {data:JSON.parse(new TextDecoder().decode(bytes.subarray(20,20+length))),binary:bytes.subarray(20+length)};};
const close=(a,b)=>assert.ok(Math.abs(a-b)<.00001,`${a} != ${b}`);

test('TV dimensions use actual diagonal, fixed 10 mm borders and soundbar clearance',()=>{
 for(const inches of [65,75,85]){
  const s=tvSpec(inches);close(Math.hypot(s.width,s.height),inches*.0254);close(s.width/s.height,16/9);
  close(s.bodyWidth-s.width,.02);close(s.bodyHeight-s.height,.02);
  assert.ok(s.centerHeight-s.bodyHeight/2-(.6725+s.soundbarOffset)>=.025-1e-10);
 }
 assert.equal(tvSpec(65).soundbarOffset,0);assert.equal(tvSpec('invalid').inches,65);
});
test('repeated live TV changes do not accumulate scale or shift stand and camera anchors',()=>{
 const group=new Group(),objects={};
 for(const name of ['65英寸电视机身','65英寸电视屏幕','电视落地支架底座','回音壁','电视支架回音壁托盘','电视支架托盘撑']){
  const o=new Object3D();o.name=name;o.position.set(.6,name==='回音壁'?.64:1.12,-7.06);group.add(o);objects[name]=o;
 }
 for(const size of [85,75,65,85,65]){
  const s=applyTVSize(group,size),screen=objects['65英寸电视屏幕'];
  close(screen.scale.y,size/65);close(screen.scale.z,size/65);close(screen.scale.x,1);
  assert.deepEqual(screen.position.toArray(),[.6,1.12,-7.06]);
  assert.deepEqual(objects['电视落地支架底座'].scale.toArray(),[1,1,1]);
  close(objects['回音壁'].position.y,.64+s.soundbarOffset);
 }
});
for(const layout of ['current','inset'])for(const width of [600,700,800])test(`${layout} ${width}: all exported TV sizes preserve binary and unrelated node transforms`,()=>{
 const suffix=layout==='inset'?`-inset-${width}`:width===700?'':`-${width}`;
 const bytes=new Uint8Array(fs.readFileSync(new URL(`./home-model${suffix}.glb`,import.meta.url))),original=decode(bytes);
 for(const size of [65,75,85]){
  const result=tvGLB(bytes,size),g=decode(result);assert.deepEqual(g.binary,original.binary);
  assert.equal(new DataView(result.buffer,result.byteOffset,result.byteLength).getUint32(8,true),result.length);
  const s=tvSpec(size);let count=0;
  g.data.nodes.forEach((n,i)=>{
   const old=original.data.nodes[i];
   if(/^\d+英寸电视(机身|屏幕)$/.test(n.name)){
    count++;assert.deepEqual(n.translation,old.translation);assert.ok(!old.rotation&&!old.matrix&&!old.scale,'base axes must match live scaling');
    const a=g.data.accessors[g.data.meshes[n.mesh].primitives[0].attributes.POSITION],scale=n.scale||[1,1,1],screen=n.name.endsWith('屏幕');
    close((a.max[2]-a.min[2])*scale[2],screen?s.width:s.bodyWidth);
    close((a.max[1]-a.min[1])*scale[1],screen?s.height:s.bodyHeight);
    close(scale[0],1);
   }else if(n.name==='回音壁'||n.name?.startsWith('电视支架回音壁托盘')||n.name?.startsWith('电视支架托盘撑')){
    const a=n.translation||[0,0,0],b=old.translation||[0,0,0];close(a[1]-b[1],s.soundbarOffset);close(a[0],b[0]);close(a[2],b[2]);
   }else assert.deepEqual(n,old);
  });assert.equal(count,2);
 }
});
test('TV collision grows for large screens and resets exactly at 65 while pass-through stays structural',()=>{
 const base=JSON.parse(fs.readFileSync(new URL('./navigation.json',import.meta.url)));const before=JSON.stringify(base);
 const large=tvNavigation(base,85);assert.equal(JSON.stringify(base),before);assert.strictEqual(tvNavigation(base,65),base);
 let added=0;for(let y=0;y<base.height;y++)for(let x=0;x<base.width;x++){
  if(base.rows[y][x]==='#')assert.equal(large.rows[y][x],'#');
  else if(large.rows[y][x]==='#')added++;
 }
 assert.ok(added>0);assert.strictEqual(navigationMode(large,true).rows,base.structureRows);
 for(const p of Object.values(base.starts))assert.ok(isWalkable(large,p.x,p.y));
});
