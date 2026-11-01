import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {isWalkable,navigationMode} from './navigation.js';
const read=f=>fs.readFileSync(new URL(f,import.meta.url));
const options=JSON.parse(read('./kitchen-options.json'));
function model(file){const b=read(file);return {b,g:JSON.parse(b.subarray(20,20+b.readUInt32LE(12)).toString())};}
function bounds(g,n){
 const out=[];const [x,y,z,w]=n.rotation||[0,0,0,1],sc=n.scale||[1,1,1],t=n.translation||[0,0,0];
 const r=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]];
 for(const p of g.meshes[n.mesh].primitives){const a=g.accessors[p.attributes.POSITION];for(let i=0;i<8;i++){
  const v=[0,1,2].map(j=>((i>>j)&1?a.max[j]:a.min[j])*sc[j]);const q=r.map((row,j)=>row.reduce((sum,c,k)=>sum+c*v[k],0)+t[j]);out.push([q[0],-q[2],q[1]]);
 }}return {min:[0,1,2].map(i=>Math.min(...out.map(v=>v[i]))),max:[0,1,2].map(i=>Math.max(...out.map(v=>v[i])))};
}
function merged(g,prefix){const rows=g.nodes.filter(n=>n.mesh!==undefined&&n.name.startsWith(prefix)).map(n=>bounds(g,n));assert.ok(rows.length,prefix);return {min:[0,1,2].map(i=>Math.min(...rows.map(v=>v.min[i]))),max:[0,1,2].map(i=>Math.max(...rows.map(v=>v.max[i])))};}
const close=(a,b)=>assert.ok(Math.abs(a-b)<.0001,`${a} != ${b}`);
let referenceShafts,referencePantry;
for(const width of [600,700,800])test(`${width} mm: French doors, coordinated cabinets, robot opening, fixed shafts and matching navigation`,()=>{
 const k=options[width],{b,g}=model(k.model),nav=JSON.parse(read(k.navigation));
 assert.equal(nav.model_sha256,createHash('sha256').update(b).digest('hex'));
 const fridge=merged(g,'法式冰箱箱体'),pantry=merged(g,'冰箱旁窄高柜'),counter=merged(g,'窗侧钢台面');
 close(fridge.max[1]-fridge.min[1],width/1000);close(fridge.min[1]-counter.max[1],.01);close(pantry.min[1]-fridge.max[1],.02);close(pantry.max[1],2.46);
 close(counter.min[1],.86);close(counter.max[1]-counter.min[1],k.robot_width_mm/1000);close(pantry.max[1]-pantry.min[1],k.pantry_width_mm/1000);close(pantry.max[2],2.4);
 close(pantry.min[1],2.23);close(pantry.max[1]-pantry.min[1],.23);close(counter.max[1]-counter.min[1],(1340-width)/1000);
 const fixedPantry=g.nodes.filter(n=>n.mesh!==undefined&&n.name.startsWith('冰箱旁窄高柜')).map(n=>[n.name,bounds(g,n)]).sort((a,b)=>a[0].localeCompare(b[0]));
 if(referencePantry)assert.deepEqual(fixedPantry,referencePantry);else referencePantry=fixedPantry;
 const doors=g.nodes.filter(n=>n.name?.startsWith('法式冰箱冷藏门')&&!n.name.includes('把手')),drawers=g.nodes.filter(n=>n.name?.startsWith('法式冰箱冷冻抽屉'));
 assert.equal(doors.length,width===600?1:2);assert.equal(drawers.length,2);
 if(width===600)close(bounds(g,doors[0]).max[1]-bounds(g,doors[0]).min[1],.59);
 assert.equal(g.nodes.filter(n=>n.name?.startsWith('法式冰箱冷藏门把手')).length,width===600?1:2);
 for(const n of doors)assert.ok(bounds(g,n).min[2]>.80);
 for(const n of drawers)close(bounds(g,n).max[1]-bounds(g,n).min[1],width/1000-.01);
 assert.ok(!g.nodes.some(n=>n.name?.startsWith('冰箱对开门')));
 const panels=g.nodes.filter(n=>n.name?.startsWith('扫地机洞口侧封板')).map(n=>bounds(g,n)).sort((a,b)=>a.min[1]-b.min[1]);
 close(panels[1].min[1]-panels[0].max[1],.430);
 const dock=merged(g,'扫地机自动上下水基站');assert.ok(dock.min[1]>panels[0].max[1]&&dock.max[1]<panels[1].min[1]);close(dock.max[1]-dock.min[1],.381);
 const shafts=g.nodes.filter(n=>n.extras?.category==='ServiceEnclosures').map(n=>[n.name,bounds(g,n)]).sort((a,b)=>a[0].localeCompare(b[0]));
 if(referenceShafts)assert.deepEqual(shafts,referenceShafts);else referenceShafts=shafts;
 for(const p of Object.values(nav.starts))assert.ok(isWalkable(nav,p.x,p.y));
 const center={x:3.6,y:(fridge.min[1]+fridge.max[1])/2};assert.equal(isWalkable(nav,center.x,center.y),false);assert.equal(isWalkable(navigationMode(nav,true),center.x,center.y),true);
});

for(const width of [600,700,800])test(`${width} mm: balcony four-column glazing and both casements open outdoors`,()=>{
 const {g}=model(options[width].model);
 assert.ok(!g.nodes.some(n=>n.name?.startsWith('南向封窗')));
 const outer=merged(g,'阳台四列外框');close(outer.max[0]-outer.min[0],4.56);close(outer.max[2]-outer.min[2],2.30);
 const fixed=g.nodes.filter(n=>n.extras?.window_type==='fixed');assert.equal(fixed.length,4);
 for(const n of fixed){const b=bounds(g,n);close((b.min[1]+b.max[1])/2,10.11);
  if(n.name.startsWith('阳台F1')||n.name.startsWith('阳台F2')){close(b.min[2],.08);close(b.max[2],2.28);assert.equal(n.extras.nominal_column_mm,1600);}
  else {close(b.max[2],1.005);assert.equal(n.extras.nominal_column_mm,700);}
 }
 const mullions=g.nodes.filter(n=>n.name?.startsWith('阳台四列竖梃')).map(n=>bounds(g,n)).sort((a,b)=>a.min[0]-b.min[0]);assert.equal(mullions.length,3);
 const cuts=[1,...mullions.map(b=>(b.min[0]+b.max[0])/2),5.56];
 for(let i=0;i<4;i++)close(cuts[i+1]-cuts[i],[700,1600,1600,700][i]/4600*4.56);
 const sashes=g.nodes.filter(n=>n.name?.includes('外开扇玻璃'));assert.equal(sashes.length,2);
 for(const n of sashes){const b=bounds(g,n);assert.equal(n.extras.opening_degrees,35);assert.ok(b.min[1]>10.11&&b.max[1]>10.40,`${n.name} must open to outdoor +Y`);assert.ok(b.min[2]>1.03);}
 assert.equal(g.nodes.filter(n=>n.name?.startsWith('阳台边列上下分格横梃')).length,2);
});
