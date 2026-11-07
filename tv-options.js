export const TV_SIZES=[65,75,85];
export function tvSpec(value){
 const inches=TV_SIZES.includes(Number(value))?Number(value):65;
 const width=inches*.0254*16/Math.hypot(16,9),height=width*9/16;
 const bodyWidth=width+.020,bodyHeight=height+.020;
 return {inches,width,height,bodyWidth,bodyHeight,centerHeight:1.12,
  soundbarOffset:Math.min(0,1.12-bodyHeight/2-.025-.6725)};
}
function tvPart(name){return /^\d+英寸电视(机身|屏幕)$/.exec(name)?.[1];}
function isSoundbar(name){return name==='回音壁'||name.startsWith('电视支架回音壁托盘')||name.startsWith('电视支架托盘撑');}
function scaleFor(part,spec){const base=tvSpec(65);return part==='屏幕'?[1,spec.height/base.height,spec.width/base.width]:[1,spec.bodyHeight/base.bodyHeight,spec.bodyWidth/base.bodyWidth];}
const supportHeights=new WeakMap();
export function applyTVSize(model,value){
 const spec=tvSpec(value);
 model.traverse(o=>{
  const part=tvPart(o.name);
  if(part){o.scale.set(...scaleFor(part,spec));o.name=`${spec.inches}英寸电视${part}`;o.userData.tv_inches=spec.inches;}
  if(isSoundbar(o.name)){
   if(!supportHeights.has(o))supportHeights.set(o,o.position.y);
   o.position.y=supportHeights.get(o)+spec.soundbarOffset;
  }
 });
 return spec;
}
// Start from the unmodified 65-inch map each time; only furniture collisions grow.
export function tvNavigation(base,value){
 const spec=tvSpec(value);if(spec.inches===65)return base;
 const margin=base.radius+base.step*Math.SQRT2/2;
 const xmin=.5675-margin,xmax=.618+margin;
 const ymin=7.06-spec.bodyWidth/2-margin,ymax=7.06+spec.bodyWidth/2+margin;
 const rows=base.rows.map((row,y)=>{
  const py=(y+.5)*base.step;if(py<ymin||py>ymax)return row;
  return [...row].map((c,x)=>{const px=(x+.5)*base.step;return px>=xmin&&px<=xmax?'#':c;}).join('');
 });
 return {...base,rows};
}
// Patch only node transforms in the original GLB, preserving all binary geometry,
// materials and hidden layers. Export therefore matches the selected screen size.
export function tvGLB(bytes,value){
 const spec=tvSpec(value);if(spec.inches===65)return bytes;
 const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 if(view.getUint32(0,true)!==0x46546c67||view.getUint32(4,true)!==2||view.getUint32(16,true)!==0x4e4f534a)throw new Error('Invalid GLB');
 const oldLength=view.getUint32(12,true),data=JSON.parse(new TextDecoder().decode(bytes.subarray(20,20+oldLength)));
 for(const n of data.nodes){
  const part=tvPart(n.name||'');
  if(part){n.scale=scaleFor(part,spec);n.name=`${spec.inches}英寸电视${part}`;n.extras={...n.extras,tv_inches:spec.inches};}
  if(isSoundbar(n.name||'')){n.translation=[...(n.translation||[0,0,0])];n.translation[1]+=spec.soundbarOffset;}
 }
 const json=new TextEncoder().encode(JSON.stringify(data)),length=Math.ceil(json.length/4)*4,tail=bytes.subarray(20+oldLength);
 const result=new Uint8Array(20+length+tail.length),out=new DataView(result.buffer);
 result.set(bytes.subarray(0,12));out.setUint32(8,result.length,true);out.setUint32(12,length,true);out.setUint32(16,0x4e4f534a,true);
 result.fill(32,20,20+length);result.set(json,20);result.set(tail,20+length);return result;
}
