"""Compare actual GLB wall triangles with CAD evidence and every scheduled opening.

Run with --model <path> --output <path>; --baseline records differences without
asserting, so the report can show exactly which prior defects were corrected.
"""
from pathlib import Path
import argparse,json,struct
import numpy as np
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
from architecture import wall_records
ROOT=Path(__file__).resolve().parent


def read_meshes(path):
    raw=Path(path).read_bytes();length=struct.unpack_from('<I',raw,12)[0]
    g=json.loads(raw[20:20+length]);binary=raw[28+length:]
    def ac(i):
        a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
        dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);n={'SCALAR':1,'VEC3':3}[a['type']]
        return np.ndarray((a['count'],n),dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*n),dt.itemsize)).copy()
    parents={c:i for i,n in enumerate(g['nodes'])for c in n.get('children',[])}
    def world(i):
        n=g['nodes'][i]
        if 'matrix'in n:m=np.array(n['matrix']).reshape(4,4).T
        else:
            x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4)
            m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
        return world(parents[i])@m if i in parents else m
    result=[]
    for i,n in enumerate(g['nodes']):
        if 'mesh'not in n:continue
        cat=n.get('extras',{}).get('category')
        if cat not in ('WallsLow','WallsUpper','Doors','Windows','Furniture','Storage','ServiceEnclosures'):continue
        if cat in ('Furniture','Storage') and not n['name'].startswith(('储物间柜门顶封','储物间封闭柜门','装饰隔断实墙','过道浅柜')):continue
        mat=world(i);vertices=[];polys=[]
        for p in g['meshes'][n['mesh']]['primitives']:
            v=ac(p['attributes']['POSITION']);v=v@mat[:3,:3].T+mat[:3,3];v=v[:,[0,2,1]];v[:,1]*=-1;vertices.extend(v)
            ix=ac(p['indices']).ravel();tri=v[ix.reshape(-1,3)][:,:,:2];u=tri[:,1]-tri[:,0];w=tri[:,2]-tri[:,0]
            areas=np.abs(u[:,0]*w[:,1]-u[:,1]*w[:,0]);polys.extend(Polygon(t)for t in tri[areas>1e-10])
        v=np.array(vertices)
        result.append(dict(name=n['name'],category=cat,lo=v.min(0),hi=v.max(0),footprint=unary_union(polys)))
    return result


def check(model,master_layout='current'):
    manifest=json.loads((ROOT/'architecture.json').read_text());cad=json.loads((ROOT/'current-geometry.json').read_text());rows=read_meshes(model);records=wall_records(ROOT,master_layout)
    changed_zone=Polygon()
    if master_layout=='inset':
        moved={'主卧门上过梁','主卧门手工侧封墙','主卧入口折墙'}
        changed_zone=unary_union([Polygon(w['p'])for w in wall_records(ROOT)+records if w['name']in moved]).buffer(.002)
        for d in manifest['doors']:
            if d['id']=='master':d['b'][0]+=.67;d['b'][1]+=.67
    def actual(z,closure=False):
        return unary_union([o['footprint'] for o in rows if o['lo'][2]<z<o['hi'][2] and (o['category']in ('WallsLow','WallsUpper') or closure and o['name'].startswith('储物间柜门顶封'))])
    result={'model':Path(model).name,'wall_regions':len(manifest['walls']),'cad_hatch_paths':sum(len(h['paths'])for h in cad['hatches']if h['pattern']=='SOLID'),'doors':[],'windows':[],'slices':[],'cad_wall_lines':[],'master_layout':master_layout,'relocated_cad_lines':[]}
    # Multiple elevations distinguish real door/window voids from missing full-height walls.
    for z in [.02,.50,1.60,2.10,2.31,2.42,2.60,2.71]:
        expected=unary_union([Polygon(w['p']).buffer(0)for w in records if w['z1']<z<w['z2']]);built=actual(z)
        missing=expected.difference(built.buffer(.0001));extra=built.difference(expected.buffer(.0001))
        result['slices'].append(dict(height_mm=round(z*1000),missing_mm2=round(missing.area*1e6,2),extra_mm2=round(extra.area*1e6,2),missing_bounds_mm=[round(v*1000)for v in missing.bounds]if not missing.is_empty else None))
    # Independent CAD wall layer coverage: no inferred cabinet/door symbol gets filled.
    for i,a in enumerate(cad['lines']):
        if not ('COMM-WALL'in a['layer'] or i in manifest['wall_outline_line_ids']) or i in (862,863,864):continue
        line=LineString([[x/1000,y/1000]for x,y in a['p']])
        if line.length<.001:continue
        if master_layout=='inset' and line.intersection(changed_zone).length>.001:
            result['relocated_cad_lines'].append(i);line=line.difference(changed_zone)
            if line.length<.001:continue
        coverage=unary_union([actual(1.6),*[o['footprint']for o in rows if o['category']=='ServiceEnclosures']])
        gap=line.difference(coverage.buffer(.001))
        result['cad_wall_lines'].append(dict(id=i,uncovered_mm=round(gap.length*1000,2)))
    for d in manifest['doors']:
        x1,x2,y1,y2=d['b'];opening=box(x1+.001,y1+.001,x2-.001,y2-.001)
        samples=[.15,1.60,d['height']-.04];blocked=max(opening.intersection(actual(z)).area for z in samples)
        head=opening.difference(actual(d['height']+.04,True).buffer(.0001)).area
        result['doors'].append(dict(name=d['name'],opening_mm=[round((x2-x1)*1000),round((y2-y1)*1000)],blocked_mm2=round(blocked*1e6,2),head_gap_mm2=round(head*1e6,2)))
        if 'leaf'in d:
            leaf=next(o for o in rows if o['name']==d['leaf'])
            result['doors'][-1]['leaf_wall_overlap_mm2']=round(leaf['footprint'].intersection(actual(1.6)).area*1e6,2)
    for d in manifest['windows']:
        x1,x2,y1,y2=d['b'];opening=box(x1+.001,y1+.001,x2-.001,y2-.001)
        blocked=opening.intersection(actual((d['sill']+d['head'])/2)).area
        gaps=[]
        for z in [d['sill']-.01,d['head']+.05]:gaps.append(opening.difference(actual(z).buffer(.0001)).area)
        result['windows'].append(dict(name=d['name'],blocked_mm2=round(blocked*1e6,2),sill_gap_mm2=round(gaps[0]*1e6,2),head_gap_mm2=round(gaps[1]*1e6,2)))
    # Close only scheduled portals, then check six room regions are separate.
    # This catches a side slit even if sample points miss it; outdoor platforms
    # are outside the residential footprint. Sub-mm bevel pockets are ignored.
    solids=[actual(1.6),*[o['footprint']for o in rows if o['category']=='ServiceEnclosures']]
    for d in manifest['doors']+manifest['windows']:
        x1,x2,y1,y2=d['b'];solids.append(box(x1,y1,x2,y2))
    footprint=Polygon(json.loads((ROOT/'model-data.json').read_text())['footprint'])
    remaining=footprint.difference(unary_union(solids).buffer(.0002))
    regions=[p for p in (remaining.geoms if remaining.geom_type=='MultiPolygon'else[remaining])if p.area>.001]
    seeds={'客餐厨与阳台':[2,5],'主卧':[8.5,7],'次卧':[6.5,2.8],'客卫':[4.7,3],'主卫':[8.8,4.5],'储物间':[7.1,4.7]}
    result['closed_room_regions']={name:[i for i,p in enumerate(regions)if p.covers(Point(pt))]for name,pt in seeds.items()}
    result['exterior_leak_mm']=round(sum(p.boundary.intersection(footprint.boundary).length for p in regions)*1000,3)
    room_ids=[v[0]for v in result['closed_room_regions'].values()if len(v)==1]
    result['room_enclosure_passed']=len(regions)==len(room_ids)==len(set(room_ids))==6 and result['exterior_leak_mm']<1
    result['passed']=result['room_enclosure_passed'] and all(s['missing_mm2']<5 and s['extra_mm2']<5 for s in result['slices']) and all(l['uncovered_mm']<1 for l in result['cad_wall_lines']) and all(d['blocked_mm2']<5 and d['head_gap_mm2']<5 and d.get('leaf_wall_overlap_mm2',0)<5 for d in result['doors']) and all(max(d['blocked_mm2'],d['sill_gap_mm2'],d['head_gap_mm2'])<5 for d in result['windows'])
    if master_layout=='inset':
        door=[o for o in rows if o['name'].startswith('主卧玻璃门边框')]
        store=[o for o in rows if o['name'].startswith('储物间封闭柜门')]
        front=min(o['lo'][0]for o in door);reference=min(o['lo'][0]for o in store)
        result['aligned_front_x_mm']=round(front*1000,2);result['front_difference_mm']=round(abs(front-reference)*1000,3)
        result['passed']=bool(result['passed'] and abs(front-reference)<.0005)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',default=str(ROOT/'home-model.glb'));p.add_argument('--output',required=True);p.add_argument('--baseline',action='store_true');p.add_argument('--master-layout',choices=['current','inset'],default='current');a=p.parse_args()
    report=check(a.model,a.master_layout);Path(a.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
    if not a.baseline:assert report['passed'],'CAD wall / opening audit failed; see report'
