import test from 'node:test';
import assert from 'node:assert/strict';
import {solarPosition,daylight,SITE} from './solar.js';
import {createLighting} from './lighting.js';
import * as THREE from './three.module.min.js';

test('Hangzhou winter/summer noon elevations reflect seasonal geometry',()=>{
 const winter=solarPosition('2026-12-21',12),summer=solarPosition('2026-06-21',12);
 assert.ok(Math.abs(winter.altitude-36.3)<1);assert.ok(Math.abs(summer.altitude-83.2)<1);
 assert.ok(Math.abs(winter.azimuth-180)<4);assert.ok(Math.abs(summer.azimuth-180)<6);
});
test('morning east / afternoon west, correct south-facing Three coordinate mapping',()=>{
 const morning=solarPosition('2026-11-04',8),noon=solarPosition('2026-11-04',12),evening=solarPosition('2026-11-04',17);
 assert.ok(morning.direction[0]>0);assert.ok(evening.direction[0]<0);assert.ok(noon.direction[2]<0);
 for(const s of [morning,noon,evening])assert.ok(Math.abs(Math.hypot(...s.direction)-1)<1e-10);
});
test('sixth floor changes terrain elevation, never solar intensity',()=>{
 const high=daylight('2026-11-04','noon'),low=daylight('2026-11-04','noon',{...SITE,floor:1});
 assert.equal(high.direct,low.direct);assert.equal(high.groundY,-15.2);assert.equal(low.groundY,-.2);
});
test('evening below horizon has no direct sunlight; date/time validation includes leap day',()=>{
 assert.equal(daylight('2026-12-21','evening').direct,0);
 assert.ok(Number.isFinite(solarPosition('2028-02-29',12).altitude));
 for(const d of ['2026-02-29','2026-13-01','bad'])assert.throws(()=>solarPosition(d,12),RangeError);
 assert.throws(()=>solarPosition('2026-11-04',24),RangeError);assert.throws(()=>daylight('2026-11-04','night'),RangeError);
});
test('clear glazing transmits sunlight, hidden envelope retains shade, switch controls emitters and light sources',()=>{
 const scene=new THREE.Scene(),renderer={shadowMap:{}},rig=createLighting(scene,renderer),model=new THREE.Group();
 const wall=new THREE.Mesh(new THREE.BoxGeometry(1,2,.2),new THREE.MeshStandardMaterial());wall.userData.category='WallsUpper';wall.position.set(3,1,-4);model.add(wall);
 const glass=new THREE.Mesh(new THREE.BoxGeometry(1,1,.01),new THREE.MeshStandardMaterial({name:'透明玻璃'}));glass.userData.category='Windows';model.add(glass);
 const shade=new THREE.Mesh(new THREE.SphereGeometry(.1),new THREE.MeshStandardMaterial({name:'乳白发光灯罩',emissive:0xffcc88,emissiveIntensity:.7}));shade.userData.category='Lighting';model.add(shade);
 scene.add(model);rig.syncModel(model);wall.visible=false;
 assert.equal(rig.shell.children.length,1);assert.equal(rig.shell.children[0].castShadow,true);assert.equal(rig.shell.children[0].material.colorWrite,false);assert.equal(rig.shell.children[0].matrix.elements[12],3);assert.equal(glass.castShadow,false);
 rig.update({indoor:false});assert.ok(rig.fixtures.every(l=>l.intensity===0));assert.equal(shade.material.emissiveIntensity,0);
 rig.update({indoor:true});assert.ok(rig.fixtures.every(l=>l.intensity>0));assert.equal(shade.material.emissiveIntensity,.7);
 rig.syncModel(model);assert.equal(rig.shell.children.length,1);
});
