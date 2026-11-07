// Whole-item edits are a local view preference, independent of model variants.
export const EDIT_STORAGE_KEY='home3d.deleted-items.v1';
export function effectiveDeleted(catalog,ids){
 const deleted=new Set([...ids].filter(id=>Object.hasOwn(catalog.items,id)));
 let changed=true;while(changed){changed=false;for(const [id,item]of Object.entries(catalog.items))if(item.parent&&deleted.has(item.parent)&&!deleted.has(id)){deleted.add(id);changed=true;}}
 return deleted;
}
export function createItemEdits(catalog,saved=''){
 let deleted=new Set(),history=[];
 try{const data=JSON.parse(saved);if(data.version===1&&Array.isArray(data.deleted))deleted=new Set(data.deleted.filter(id=>typeof id==='string'&&Object.hasOwn(catalog.items,id)));}catch{}
 function change(next){if([...next].join('\0')===[...deleted].join('\0'))return false;history.push([...deleted]);if(history.length>100)history.shift();deleted=next;return true;}
 return {get deleted(){return new Set(deleted);},get effective(){return effectiveDeleted(catalog,deleted);},get canUndo(){return history.length>0;},
  remove(id){return Object.hasOwn(catalog.items,id)&&!effectiveDeleted(catalog,deleted).has(id)&&change(new Set([...deleted,id]));},
  restore(id){const next=new Set(deleted);next.delete(id);return change(next);},
  restoreAll(){return change(new Set());},undo(){if(!history.length)return false;deleted=new Set(history.pop());return true;},
  serialize(){return JSON.stringify({version:1,deleted:[...deleted]});}
 };
}
export function originalItemName(name){return name.replace(/^\d+英寸电视/,'65英寸电视');}
export function bindItems(model,members){
 model.traverse(o=>{const name=originalItemName(o.userData.name||o.name);o.userData.editItem=members[name]||null;});
}
export function itemId(object){for(let o=object;o;o=o.parent)if(o.userData?.editItem)return o.userData.editItem;return null;}
export function isVisible(object){for(let o=object;o;o=o.parent)if(!o.visible)return false;return true;}
export function editedNavigation(base,deleted){
 if(!Object.keys(base.itemObstacles||{}).some(id=>deleted.has(id)))return base;
 const rows=base.editFixedRows.map(row=>[...row]);
 for(const [id,spans]of Object.entries(base.itemObstacles))if(!deleted.has(id))for(const [y,a,b]of spans)for(let x=a;x<b;x++)rows[y][x]='#';
 return {...base,rows:rows.map(row=>row.join(''))};
}
export function editedGLB(bytes,members,deleted){
 if(!deleted.size)return bytes;
 const dv=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),oldLength=dv.getUint32(12,true);
 const data=JSON.parse(new TextDecoder().decode(bytes.subarray(20,20+oldLength)));
 for(const n of data.nodes)if(deleted.has(members[originalItemName(n.name||'')]))delete n.mesh;
 data.extras={...data.extras,removed_items:[...deleted]};
 const json=new TextEncoder().encode(JSON.stringify(data)),length=Math.ceil(json.length/4)*4,tail=bytes.subarray(20+oldLength);
 const out=new Uint8Array(20+length+tail.length);out.set(bytes.subarray(0,12));const view=new DataView(out.buffer);
 view.setUint32(8,out.length,true);view.setUint32(12,length,true);view.setUint32(16,0x4e4f534a,true);
 out.fill(32,20,20+length);out.set(json,20);out.set(tail,20+length);return out;
}
