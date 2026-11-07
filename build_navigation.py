"""Derive a conservative 2D standing-person navigation map from the exported GLB.
No CAD walls or furniture are approximated by one global bounding box.
"""
from pathlib import Path
import json, struct, hashlib, argparse
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import contains_xy
from collections import deque
R=Path(__file__).resolve().parent
args=argparse.ArgumentParser();args.add_argument('--model',default='home-model.glb');args.add_argument('--output',default='navigation.json');args=args.parse_args()
blob=(R/args.model).read_bytes();size=struct.unpack_from('<I',blob,12)[0]
g=json.loads(blob[20:20+size]);binary=blob[28+size:]
def accessor(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
 dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
 n={'SCALAR':1,'VEC3':3}[a['type']];dt=np.dtype(dtype);offset=v.get('byteOffset',0)+a.get('byteOffset',0)
 return np.ndarray((a['count'],n),dtype=dt,buffer=binary,offset=offset,strides=(v.get('byteStride',dt.itemsize*n),dt.itemsize)).copy()
def matrix(n):
 if 'matrix'in n:return np.array(n['matrix']).reshape(4,4).T
 x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4)
 m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0]);return m
parents={c:i for i,n in enumerate(g['nodes'])for c in n.get('children',[])}
def world(i):return (world(parents[i])if i in parents else np.eye(4))@matrix(g['nodes'][i])
catalog=json.loads((R/'edit-catalog.json').read_text())
model_hash=hashlib.sha256(blob).hexdigest()
entry=next((e for e in catalog['models'].values()if e['model_sha256']==model_hash),None)
if entry is None:raise ValueError('Rebuild edit-catalog.json for this model first')
members=entry['members'];item_shapes={};fixed_shapes=[]
obstacles=[];structure=[];included=0
for i,n in enumerate(g['nodes']):
 if 'mesh'not in n or n.get('extras',{}).get('category')not in {'WallsLow','WallsUpper','BathroomWalls','Windows','Doors','Storage','Furniture','Appliances','Exterior','ServiceEnclosures'}:continue
 transform=world(i);polys=[]
 for p in g['meshes'][n['mesh']]['primitives']:
  v=accessor(p['attributes']['POSITION']);v=v@transform[:3,:3].T+transform[:3,3]
  if (v[:,1].max()<.12 and n['name']!='电视落地支架底座') or v[:,1].min()>1.85:continue
  indices=accessor(p['indices']).ravel() if 'indices'in p else np.arange(len(v))
  # Full projection of each overlapping mesh preserves concave wall outlines.
  tri=v[indices.reshape(-1,3)][:,:,[0,2]];tri[:,:,1]*=-1
  u=tri[:,1]-tri[:,0];w=tri[:,2]-tri[:,0];area=np.abs(u[:,0]*w[:,1]-u[:,1]*w[:,0])
  polys.extend(Polygon(t)for t in tri[area>1e-9])
 if polys:
  shape=unary_union(polys);obstacles.append(shape);included+=1
  ident=members.get(n['name'])
  if ident:item_shapes.setdefault(ident,[]).append(shape)
  else:fixed_shapes.append(shape)
  if n.get('extras',{}).get('category') in {'WallsLow','WallsUpper','BathroomWalls','Windows','Exterior','ServiceEnclosures'}:structure.append(shape)
step=.04;radius=.20
footprint=Polygon(json.loads((R/'model-data.json').read_text())['footprint'])
# Half-cell diagonal margin makes every open cell safe across its whole area.
margin=radius+step*2**.5/2
safe=footprint.buffer(-margin).difference(unary_union(obstacles).buffer(margin))
nx=250;ny=260;xx,yy=np.meshgrid((np.arange(nx)+.5)*step,(np.arange(ny)+.5)*step)
free=contains_xy(safe,xx,yy)
structure_free=contains_xy(footprint.buffer(-margin).difference(unary_union(structure).buffer(margin)),xx,yy)
# Mark components for safe room starts and connectivity regression checks.
labels=np.full((ny,nx),-1,dtype=int);components=[]
for y,x in zip(*np.where(free)):
 if labels[y,x]>=0:continue
 idx=len(components);q=deque([(x,y)]);labels[y,x]=idx;cells=[]
 while q:
  a,b=q.popleft();cells.append((a,b))
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
   c,d=a+dx,b+dy
   if 0<=c<nx and 0<=d<ny and free[d,c]and labels[d,c]<0:labels[d,c]=idx;q.append((c,d))
 components.append(cells)
main=max(range(len(components)),key=lambda i:len(components[i]))
# Remove tiny pockets inside objects; keep genuinely separate rooms if any.
free &= np.array([len(components[max(0,i)])>=100 if i>=0 else False for i in labels.ravel()]).reshape(labels.shape)
starts={'entry':[1.25,1.55],'living':[1.3,5.5],'kitchen':[2.85,2.9],'study':[5.12,5.3],'master':[7.2,6.4],'guest':[5.9,3.3],'bath':[8.65,5.45],'basin':[4.8,4.7],'laundry':[5.2,9.25]}
resolved={}
for name,(x,y)in starts.items():
 ys,xs=np.where(free);k=np.argmin((xx[ys,xs]-x)**2+(yy[ys,xs]-y)**2);a,b=xs[k],ys[k]
 resolved[name]={'x':round(float(xx[b,a]),3),'y':round(float(yy[b,a]),3),'component':int(labels[b,a]),'connectedToEntry':bool(labels[b,a]==main)}
data={'model_sha256':hashlib.sha256(blob).hexdigest(),'step':step,'radius':radius,'eyeHeight':1.6,'bodyTop':1.85,'width':nx,'height':ny,'rows':[''.join('.'if c else '#'for c in row)for row in free],'starts':resolved,'obstacleMeshes':included,'structureRows':[''.join('.'if c else '#'for c in row)for row in structure_free]}
# Each item retains its own buffered occupied cells: deleting one object must
# never clear cells occupied by an overlapping neighbor or by the building.
def spans(mask):
 result=[]
 for y,row in enumerate(mask):
  indices=np.flatnonzero(np.diff(np.r_[False,row,False].astype(int)))
  result.extend([int(y),int(a),int(b)]for a,b in zip(indices[::2],indices[1::2]))
 return result
fixed=footprint.buffer(-margin).difference(unary_union(fixed_shapes).buffer(margin))
data['editFixedRows']=[''.join('.'if c else '#'for c in row)for row in contains_xy(fixed,xx,yy)]
data['itemObstacles']={key:spans(contains_xy(unary_union(shapes).buffer(margin),xx,yy))for key,shapes in item_shapes.items()}
(R/args.output).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
print(json.dumps({'obstacleMeshes':included,'components':sorted([len(c)for c in components],reverse=True)[:10],'starts':resolved},ensure_ascii=False,indent=2))
