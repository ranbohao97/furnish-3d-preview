"""Union coincident CAD wall solids into a clean, watertight shell per Z band."""
import json,sys
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient
src,dst=sys.argv[1:3]
data=json.load(open(src));levels=sorted(set(round(z,6)for w in data for z in (w['z1'],w['z2'])))
out=[]
for lo,hi in zip(levels,levels[1:]):
    if hi-lo<.00001:continue
    active=[Polygon(w['p']).buffer(0)for w in data if w['z1']<=(lo+hi)/2<=w['z2']]
    if not active:continue
    geom=unary_union(active)
    for p in ([geom]if geom.geom_type=='Polygon'else geom.geoms):
        p=orient(p,sign=1)
        tris=constrained_delaunay_triangles(p)
        out.append({'z1':lo,'z2':hi,'rings':[[list(v)for v in list(r.coords)[:-1]]for r in [p.exterior,*p.interiors]],'triangles':[[list(v)for v in list(t.exterior.coords)[:-1]]for t in tris.geoms]})
json.dump(out,open(dst,'w'))
print('wall slabs',len(out))
