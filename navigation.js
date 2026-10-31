// Plan coordinates are metres: (x, y) maps to Three.js (x, -z).
export function isWalkable(nav,x,y){
 const col=Math.floor(x/nav.step),row=Math.floor(y/nav.step);
 return row>=0&&row<nav.height&&col>=0&&col<nav.width&&nav.rows[row][col]==='.';
}
export function moveOnGrid(nav,position,dx,dy){
 const steps=Math.max(1,Math.ceil(Math.hypot(dx,dy)/(nav.step*.45)));
 let {x,y}=position;dx/=steps;dy/=steps;
 for(let i=0;i<steps;i++){
  if(isWalkable(nav,x+dx,y))x+=dx;
  if(isWalkable(nav,x,y+dy))y+=dy;
 }
 return {x,y};
}
export function movementVector(yaw,forward,right,distance){
 const norm=Math.hypot(forward,right)||1;
 return {x:(-Math.sin(yaw)*forward+Math.cos(yaw)*right)*distance/norm,y:(Math.cos(yaw)*forward+Math.sin(yaw)*right)*distance/norm};
}

// Switching collision on while inside furniture must not trap the visitor.
export function nearestWalkable(nav,position){
 if(isWalkable(nav,position.x,position.y))return position;
 let nearest=null,best=Infinity;
 for(let y=0;y<nav.height;y++)for(let x=0;x<nav.width;x++)if(nav.rows[y][x]==='.'){
  const p={x:(x+.5)*nav.step,y:(y+.5)*nav.step},d=(p.x-position.x)**2+(p.y-position.y)**2;
  if(d<best){nearest=p;best=d;}
 }
 return nearest||position;
}
export function navigationMode(nav,passObjects){return passObjects?{...nav,rows:nav.structureRows}:nav;}
