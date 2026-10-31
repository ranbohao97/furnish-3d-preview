import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {isWalkable,moveOnGrid,movementVector} from './navigation.js';
const nav=JSON.parse(fs.readFileSync(new URL('./navigation.json',import.meta.url)));
test('navigation belongs to this exact exported model and room starts are clear',()=>{
 assert.equal(nav.model_sha256,createHash('sha256').update(fs.readFileSync(new URL('./home-model.glb',import.meta.url))).digest('hex'));
 for(const p of Object.values(nav.starts))assert.ok(isWalkable(nav,p.x,p.y));
});
test('entry corridor permits forward walking but cabinets and island stop strafing',()=>{
 const p=nav.starts.entry;
 const forward=moveOnGrid(nav,p,0,2);assert.ok(forward.y>3.4);
 const left=moveOnGrid(nav,p,-10,0);assert.ok(left.x>=.99&&left.x<1.1);
 const right=moveOnGrid(nav,p,10,0);assert.ok(right.x<=1.59&&right.x>p.x);
 assert.ok(isWalkable(nav,left.x,left.y));assert.ok(isWalkable(nav,right.x,right.y));
});
test('large deltas cannot tunnel through obstacles; diagonal input is normalized',()=>{
 const m={step:1,width:5,height:3,rows:['..#..','..#..','..#..']};
 const p=moveOnGrid(m,{x:.5,y:1.5},10,0);assert.ok(p.x<2);
 const diagonal=movementVector(0,1,1,1);assert.ok(Math.abs(Math.hypot(diagonal.x,diagonal.y)-1)<1e-10);
 const facingLeft=movementVector(Math.PI/2,1,0,1);assert.ok(facingLeft.x<-.99);
 assert.equal(isWalkable(m,-1,1),false);
});
test('entry connects to living, bedrooms, study and balcony; kitchen shortcut is explicit',()=>{
 const seen=new Set();const x=Math.floor(nav.starts.entry.x/nav.step),y=Math.floor(nav.starts.entry.y/nav.step),q=[[x,y]];seen.add(`${x},${y}`);
 for(let i=0;i<q.length;i++){const [a,b]=q[i];for(const [dx,dy]of [[1,0],[-1,0],[0,1],[0,-1]]){const c=a+dx,d=b+dy,k=`${c},${d}`;if(!seen.has(k)&&isWalkable(nav,(c+.5)*nav.step,(d+.5)*nav.step)){seen.add(k);q.push([c,d]);}}}
 for(const key of ['living','study','master','guest','bath','basin','laundry']){const p=nav.starts[key];assert.ok(seen.has(`${Math.floor(p.x/nav.step)},${Math.floor(p.y/nav.step)}`),key);}
 assert.equal(nav.starts.kitchen.connectedToEntry,false);
});

test('floor TV stand base remains an obstacle despite its low height',()=>{
 assert.equal(isWalkable(nav,1.0,7.40),false);
});

test('pass-through mode crosses furniture but retains walls and outer boundary',async()=>{
 const {navigationMode,nearestWalkable}=await import('./navigation.js');
 const free=navigationMode(nav,true),p=nav.starts.entry;
 const left=moveOnGrid(free,p,-10,0);
 assert.ok(left.x<.8&&left.x>.5,'cross shoe cabinet, stop at wall');
 assert.equal(isWalkable(nav,left.x,left.y),false);
 const restored=nearestWalkable(nav,left);
 assert.ok(isWalkable(nav,restored.x,restored.y));
 assert.equal(isWalkable(free,.15,3),false);
 assert.equal(isWalkable(free,1.0,7.4),true,'pass low TV base');
 assert.deepEqual(nearestWalkable(nav,p),p);
 const seen=new Set(),q=[p];
 for(let i=0;i<q.length;i++){
  const v=q[i],a=Math.floor(v.x/free.step),b=Math.floor(v.y/free.step),k=`${a},${b}`;
  if(seen.has(k))continue;seen.add(k);
  for(const [dx,dy]of [[1,0],[-1,0],[0,1],[0,-1]]){const x=(a+dx+.5)*free.step,y=(b+dy+.5)*free.step;if(!seen.has(`${a+dx},${b+dy}`)&&isWalkable(free,x,y))q.push({x,y});}
 }
 const k=nav.starts.kitchen;assert.ok(seen.has(`${Math.floor(k.x/free.step)},${Math.floor(k.y/free.step)}`),'entry reaches kitchen through furniture');
});
