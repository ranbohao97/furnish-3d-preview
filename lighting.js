import * as THREE from './three.module.min.js';
import {daylight,SITE} from './solar.js';
// Positions match build_model.py fixtures, in plan X/Y and height above finished floor.
export const FIXTURES=[
 {p:[2.45,3.70,1.74],power:23,reach:4.2,angle:1.35},
 {p:[8.40,8.10,2.10],power:28,reach:4.5,angle:1.4},
 {p:[6.48,2.88,2.13],power:23,reach:4,angle:1.4},
 ...[[2,6.2],[4.7,7],[2.8,4.9],[5.8,4.5],[3,1.3]].map(([x,y])=>({p:[x,y,2.56],power:25,reach:4,angle:.95})),
 {p:[1.37,8.40,1.44],power:6,reach:1.6,angle:1.15},
 {p:[3.98,6.67,1.16],power:2.5,reach:.85,angle:1.1},
 {p:[3.98,8.17,1.16],power:2.5,reach:.85,angle:1.1}
];
export function createLighting(scene,renderer){
 const sky=new THREE.HemisphereLight(0xdcecff,0x968271,.7);scene.add(sky);
 const sun=new THREE.DirectionalLight(0xfff1dd,3);sun.castShadow=true;
 sun.shadow.mapSize.set(4096,4096);Object.assign(sun.shadow.camera,{left:-8,right:8,top:8,bottom:-8,near:.5,far:65});sun.shadow.normalBias=.012;sun.shadow.bias=-.00006;
 sun.target.position.set(4.7,1,-5.1);scene.add(sun,sun.target);
 const fixtures=FIXTURES.map(f=>{
  const l=new THREE.SpotLight(0xffdfb4,f.power,f.reach,f.angle,.6,2);l.position.set(f.p[0],f.p[2],-f.p[1]);l.target.position.copy(l.position).add(new THREE.Vector3(0,-1,0));
  l.castShadow=true;const resolution=f.reach>2?1024:512;l.shadow.mapSize.set(resolution,resolution);l.shadow.normalBias=.025;l.shadow.bias=-.0002;l.shadow.camera.near=.05;
  scene.add(l,l.target);return l;
 });
 const ground=new THREE.Mesh(new THREE.PlaneGeometry(1600,1600),new THREE.MeshStandardMaterial({color:0xb5b9ad,roughness:1}));ground.rotation.x=-Math.PI/2;ground.position.y=-(SITE.floor-1)*SITE.floorHeight-.2;ground.receiveShadow=true;scene.add(ground);
 const shell=new THREE.Group();scene.add(shell);
 const shadowOnly=new THREE.MeshBasicMaterial({colorWrite:false,depthWrite:false,side:THREE.DoubleSide});
 const emissives=new Map();let state={date:'2026-11-04',period:'noon',indoor:true};
 renderer.shadowMap.autoUpdate=false;
 function invalidate(){renderer.shadowMap.needsUpdate=true;}
 function syncModel(model){
  shell.clear();emissives.clear();model.updateMatrixWorld(true);
  model.traverse(o=>{
   if(!o.isMesh)return;
   const materials=Array.isArray(o.material)?o.material:[o.material],glass=materials.some(m=>m.name==='透明玻璃');
   // Clear glazing transmits sunlight; frames/mullions remain shadow casters.
   o.castShadow=!glass && o.userData.category!=='Lighting';
   for(const m of materials){if(m.name==='乳白发光灯罩')emissives.set(m,.7);}
   // Preserve the actual envelope's shade even while its visible walls/roof are cut away.
   if(!glass && ['WallsUpper','WallsLower','Windows','Ceiling','BathroomWalls','Curtains'].includes(o.userData.category)){
    const proxy=new THREE.Mesh(o.geometry,shadowOnly);proxy.matrixAutoUpdate=false;proxy.matrix.copy(o.matrixWorld);proxy.castShadow=true;proxy.frustumCulled=false;shell.add(proxy);o.castShadow=false;
   }
  });
  update(state);
 }
 function update(next){
  state={...state,...next};const d=daylight(state.date,state.period);
  sun.position.copy(sun.target.position).addScaledVector(new THREE.Vector3(...d.direction),30);sun.intensity=d.direct;
  sun.color.set('#fff3df').lerp(new THREE.Color('#ffb773'),d.warmth);sky.intensity=d.sky;
  scene.background=new THREE.Color('#dce6e8').lerp(new THREE.Color('#928d9f'),d.warmth*.7);
  if(d.altitude<0)scene.background.set('#343e58');
  // A modest IBL approximation for diffuse bounce, never the old always-on studio fill.
  scene.environmentIntensity=.10+d.sky*.40+(state.indoor?.08:0);
  fixtures.forEach((l,i)=>l.intensity=state.indoor?FIXTURES[i].power:0);
  emissives.forEach((intensity,m)=>m.emissiveIntensity=state.indoor?intensity:0);
  ground.position.y=d.groundY;invalidate();return d;
 }
 return {update,syncModel,invalidate,get state(){return {...state}},sun,fixtures,shell};
}
