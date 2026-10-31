import * as THREE from './three.module.min.js';
import {OrbitControls} from './OrbitControls.js';
import {GLTFLoader} from './GLTFLoader.js';
import {createWalkthrough} from './walkthrough.js';
import navigation from './navigation.json';
import {RoomEnvironment} from './RoomEnvironment.js';

const $=id=>document.getElementById(id),host=$('stage');
const scene=new THREE.Scene();scene.background=new THREE.Color('#e8e4da');
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;
renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=.98;host.prepend(renderer.domElement);
const camera=new THREE.PerspectiveCamera(43,1,.025,200);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.09;
controls.maxPolarAngle=Math.PI*.49;controls.minDistance=.3;controls.maxDistance=35;
const pmrem=new THREE.PMREMGenerator(renderer);scene.environment=pmrem.fromScene(new RoomEnvironment(),.04).texture;
scene.add(new THREE.HemisphereLight(0xfff4dc,0x787166,1.25));
const sun=new THREE.DirectionalLight(0xffecd1,2.3);sun.position.set(-3,14,-8);sun.castShadow=true;
sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-12;sun.shadow.camera.right=12;sun.shadow.camera.top=12;sun.shadow.camera.bottom=-12;sun.shadow.normalBias=.025;
scene.add(sun);sun.target.position.set(4.5,0,-5);scene.add(sun.target);
const fill=new THREE.DirectionalLight(0xc9dcff,1.1);fill.position.set(12,7,4);scene.add(fill);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.MeshStandardMaterial({color:0xe8e4da,roughness:1}));floor.rotation.x=-Math.PI/2;floor.position.y=-.205;floor.receiveShadow=true;scene.add(floor);

let walk=null;
let model=null,move=null,current='overview';let meshCount=0;
const V=(x,y,z)=>new THREE.Vector3(x,z,-y);
const views={
 overview:{p:[-5.8,-8.0,12.3],t:[4.7,5.2,.4],fov:43,title:'全屋轴测',note:'剖切墙体，查看客餐厨、双人工位与卧室之间的关系。',cut:true},
 plan:{p:[4.9,5.1,18.7],t:[4.9,5.1,0],fov:36,title:'俯视布局',note:'上方为南向窗面。可打开 CAD 线稿，核对家具与墙体平面。',cut:true},
 living:{p:[1.12,4.55,1.55],t:[3.2,8.15,1.15],fov:76,title:'客厅 · 双人工位',note:'炭黑皮沙发、木质长桌、管状金属与少量砖红点缀。南侧保留低梁。'},
 kitchen:{p:[3.05,5.20,1.60],t:[2.20,1.55,1.08],fov:73,title:'餐厅 · 厨房',note:'无吊柜；水槽柜朝工作通道开启。900 mm 餐桌向东调整，西侧留入户通路。'},
 study:{p:[5.10,5.11,1.55],t:[3.8,7.7,1.1],fov:75,title:'双人工位',note:'长桌同时容纳两套电脑及缝纫设备，半高隔板与客厅保持联系。'},
 master:{p:[7.55,6.16,1.60],t:[8.65,8.30,1.10],fov:79,title:'主卧',note:'床尾浅柜采用正向抽拉挂衣；另一组保留长衣区。修正柜前误加墙及床头、梳妆台交叠。'},
 guest:{p:[5.58,3.61,1.55],t:[6.92,2.48,.72],fov:79,title:'弹性次卧',note:'2.0 × 0.9 米日床沿窗墙摆放，释放柜前空间；边几可移动。'},
 bath:{p:[8.68,5.56,1.58],t:[9.00,4.0,1.0],fov:85,title:'主卫',note:'依当前平面保留淋浴与帘隔。旧需求中的浴缸尚未落实到这版图纸。'},
 entry:{p:[3.10,2.78,1.64],t:[.52,2.80,1.37],fov:65,title:'玄关 · 高柜与吊顶',note:'柜高 2400 mm，上方局部吊顶 320 mm。整排 3230 mm：鞋履、归家随手位、长靴雨伞、通勤备品；餐桌端留 760 mm 餐边区。勾选柜内分区查看。'},
 basin:{p:[4.96,4.91,1.62],t:[3.92,4.16,.89],fov:62,title:'客卫 · 三角洗手台',note:'按 CAD 三角轮廓重建台面与柜体，圆盆嵌入台面；斜面开门避开卫生间入口。'},
 laundry:{p:[3.9,9.3,1.55],t:[5.85,9.3,1.2],fov:70,title:'阳台 · 洗烘',note:'洗烘正面可操作；家政柜按机器归位、长柄工具和日用品分区。'}
};
function viewFov(v){if(current==='entry' && host.clientWidth/host.clientHeight<.8)return 100;return v.cut && host.clientWidth/host.clientHeight<.8 ? 68 : v.fov;}
function setView(key,instant=false){
 if(walk?.active)walk.exit();
 const v=views[key];current=key;document.querySelectorAll('[data-view]').forEach(b=>{b.classList.toggle('selected',b.dataset.view===key);b.setAttribute('aria-pressed',b.dataset.view===key)});
 $('view-title').textContent=v.title;$('view-note').textContent=v.note;
 $('cut').checked=!!v.cut;$('roof').checked=!v.cut;$('cad').checked=false;
 controls.minDistance=v.cut?5:.25;controls.maxDistance=v.cut?35:9;
 controls.maxPolarAngle=v.cut?Math.PI*.49:Math.PI*.80;
 const dest=V(...v.p),target=V(...v.t);
 if(instant||matchMedia('(prefers-reduced-motion: reduce)').matches){camera.position.copy(dest);controls.target.copy(target);camera.fov=viewFov(v);camera.updateProjectionMatrix();}
 else move={start:performance.now(),p0:camera.position.clone(),t0:controls.target.clone(),f0:camera.fov,p1:dest,t1:target,f1:viewFov(v)};
 updateLayers();
}
const upperCats=new Set(['WallsUpper','Windows','Curtains','BathroomWalls']);
const furnishing=new Set(['Furniture','Storage','Appliances','Decor','Lighting']);
function category(o){let n=o;while(n){if(n.userData?.category)return n.userData.category;n=n.parent;}return '';}
function updateLayers(){
 if(!model)return;
 model.traverse(o=>{
  const cat=o.userData?.category;if(!cat)return;
  let visible=true;
  if(upperCats.has(cat)&&$('cut').checked)visible=false;
  if(cat==='Ceiling')visible=$('roof').checked;
  if(furnishing.has(cat)&&!$('furniture').checked)visible=false;
  if((o.userData.front_panel || /柜门拉手|抽屉拉手|家政柜门把手|三角盆柜斜面拉手/.test(o.name)) && $('internals').checked)visible=false;
  o.visible=visible;
 });
 cadLines.visible=$('cad').checked;
 usageOverlay.visible=$('usage').checked;
}
const coords=[];for(const l of window.CAD_LINES){for(const p of l){coords.push(p[0]/1000,.038,-p[1]/1000)}}
const cadGeo=new THREE.BufferGeometry();cadGeo.setAttribute('position',new THREE.Float32BufferAttribute(coords,3));
const cadLines=new THREE.LineSegments(cadGeo,new THREE.LineBasicMaterial({color:0x1b5278,transparent:true,opacity:.85,depthTest:false}));cadLines.visible=false;cadLines.renderOrder=99;scene.add(cadLines);
// Measured concept clearances and one unobstructed daily route, metres.
const usageOverlay=new THREE.Group();scene.add(usageOverlay);usageOverlay.visible=false;
function noteSprite(text,pos){const c=document.createElement('canvas');c.width=640;c.height=100;const ctx=c.getContext('2d');ctx.fillStyle='#f8f5edee';ctx.fillRect(0,0,640,100);ctx.fillStyle='#244739';ctx.font='500 48px sans-serif';ctx.textAlign='center';ctx.fillText(text,320,62);const m=new THREE.SpriteMaterial({map:Object.assign(new THREE.CanvasTexture(c),{colorSpace:THREE.SRGBColorSpace}),depthTest:false,toneMapped:false});const o=new THREE.Sprite(m);o.scale.set(2.2,.344,1);o.position.copy(V(...pos));o.renderOrder=110;usageOverlay.add(o);}
function dimension(a,b,text){const ps=[V(...a),V(...b)];const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(ps),new THREE.LineBasicMaterial({color:0x486f54,depthTest:false}));line.renderOrder=108;usageOverlay.add(line);noteSprite(text,[(a[0]+b[0])/2,(a[1]+b[1])/2,.32]);}
dimension([.786,1.8,.06],[1.79,1.8,.06],'玄关净距约 1000 mm');
dimension([.786,3.7,.06],[1.557,3.7,.06],'入户通路约 770 mm');
dimension([4.862,7.85,.06],[5.612,7.85,.06],'工位后约 750 mm');
dimension([6.88,7.2,.06],[7.515,7.2,.06],'床尾最窄约 635 mm');
dimension([6.9,2.90,.06],[6.9,3.747,.06],'次卧柜前约 850 mm');
const route=[[1.18,1.25,.05],[1.18,3.1,.05],[1.18,4.65,.05],[2.5,5.05,.05],[4.95,5.3,.05],[5.22,6.2,.05],[5.22,8.85,.05]].map(p=>V(...p));
const pathLine=new THREE.Line(new THREE.BufferGeometry().setFromPoints(route),new THREE.LineDashedMaterial({color:0x557650,dashSize:.12,gapSize:.07,depthTest:false}));pathLine.computeLineDistances();pathLine.renderOrder=107;usageOverlay.add(pathLine);
const raycaster=new THREE.Raycaster();const pointer=new THREE.Vector2();let down=null;
renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);
renderer.domElement.addEventListener('pointerup',e=>{
 if(walk?.active||!model||!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>4)return;
 const r=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);raycaster.setFromCamera(pointer,camera);
 const hit=raycaster.intersectObject(model,true).find(h=>{let p=h.object;while(p){if(!p.visible)return false;p=p.parent;}return true});
 if(hit){let n=hit.object;while(n.parent&&!n.userData.category)n=n.parent;
 $('selection').textContent=n.name.replace(/_\d+$/,'');$('selection').hidden=false;}
});
function error(message){$('loading').classList.add('failed');$('loading-text').textContent=message;}
let modelBytes;
$('download').disabled=true;
async function loadModel(){
 try {
  const response=await fetch(window.MODEL_URL);
  if(!response.ok)throw new Error(`HTTP ${response.status}`);
  const buffer=await response.arrayBuffer();
  const g=await new GLTFLoader().parseAsync(buffer,'');
  modelBytes=new Uint8Array(buffer);model=g.scene;scene.add(model);
  model.traverse(o=>{if(o.isMesh){meshCount++;o.castShadow=true;o.receiveShadow=true;
   const ms=Array.isArray(o.material)?o.material:[o.material];ms.forEach(m=>{if(m.name==='透明玻璃'){m.transparent=true;m.opacity=.18;m.depthWrite=false;}m.envMapIntensity=.8;});
  }});
  setView('overview',true);$('loading').hidden=true;$('download').disabled=false;$('walk-start').disabled=false;
  $('status').textContent='模型已就绪 · v4';window.MODEL_READY=true;window.MODEL_MESHES=meshCount;
 }catch(e){error('模型加载失败，请检查网络后刷新：'+e.message)}
}
loadModel();
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
for(const id of ['cut','roof','furniture','cad','internals','usage'])$(id).addEventListener('change',updateLayers);
$('reset').addEventListener('click',()=>setView(current));
$('capture').addEventListener('click',()=>{renderer.render(scene,camera);const a=document.createElement('a');a.download='全屋_'+(walk?.active?'第一人称漫游':views[current].title)+'.png';a.href=renderer.domElement.toDataURL('image/png');a.click()});
$('download').addEventListener('click',()=>{if(!modelBytes)return;const bytes=modelBytes;const url=URL.createObjectURL(new Blob([bytes],{type:'model/gltf-binary'}));const a=document.createElement('a');a.href=url;a.download='全屋_全屋模型.glb';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
$('info').addEventListener('click',()=>{walk?.pause();$('details').showModal()});$('close-info').addEventListener('click',()=>$('details').close());
walk=createWalkthrough({camera,canvas:renderer.domElement,nav:navigation,host,
 onEnter(){
  const saved={position:camera.position.clone(),target:controls.target.clone(),fov:camera.fov,layers:{}};
  move=null;controls.enabled=false;
  for(const id of ['cut','roof','furniture','cad','internals','usage']){saved.layers[id]=$(id).checked;$(id).disabled=true;}
  $('cut').checked=false;$('roof').checked=true;$('furniture').checked=true;$('cad').checked=false;$('internals').checked=false;$('usage').checked=false;updateLayers();
  $('view-title').textContent='第一人称漫游';$('view-note').textContent='从入户出发，用 WASD 行走。拖动画面转头，或启用鼠标自由转头。';
  camera.fov=72;camera.updateProjectionMatrix();return saved;
 },
 onExit(saved){
  controls.enabled=true;camera.position.copy(saved.position);controls.target.copy(saved.target);camera.fov=saved.fov;camera.updateProjectionMatrix();
  for(const [id,value]of Object.entries(saved.layers)){$(id).checked=value;$(id).disabled=false;}updateLayers();
  $('view-title').textContent=views[current].title;$('view-note').textContent=views[current].note;
 }
});
function resize(){const r=host.getBoundingClientRect();renderer.setSize(r.width,r.height);camera.aspect=r.width/r.height;camera.fov=walk?.active?72:viewFov(views[current]);if(move)move.f1=camera.fov;camera.updateProjectionMatrix()}
new ResizeObserver(resize).observe(host);resize();
let lastFrame=performance.now();
function tick(now){requestAnimationFrame(tick);const dt=Math.max(0,(now-lastFrame)/1000);lastFrame=now;
 if(move){let t=Math.min(1,(now-move.start)/750);t=t*t*(3-2*t);camera.position.lerpVectors(move.p0,move.p1,t);controls.target.lerpVectors(move.t0,move.t1,t);camera.fov=THREE.MathUtils.lerp(move.f0,move.f1,t);camera.updateProjectionMatrix();if(t>=1)move=null;}
 if(walk?.active)walk.update(dt,now);else controls.update();renderer.render(scene,camera);
}
requestAnimationFrame(tick);
window.HOME3D={setView,scene,camera,renderer,controls,getModel:()=>model};
