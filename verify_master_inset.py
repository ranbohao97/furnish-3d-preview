"""Verify the intended door displacement and all untouched model geometry."""
import argparse,json,struct
from pathlib import Path
import numpy as np
from audit_architecture import check,read_meshes
from shapely.ops import unary_union
from shapely.geometry import box


def meshes(path):
    raw=Path(path).read_bytes();n=struct.unpack_from('<I',raw,12)[0]
    g=json.loads(raw[20:20+n]);blob=raw[28+n:];result={}
    def vertices(index):
        a=g['accessors'][index];v=g['bufferViews'][a['bufferView']]
        return np.ndarray((a['count'],3),dtype='<f4',buffer=blob,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',12),4)).copy()
    for o in g['nodes']:
        if 'mesh'not in o:continue
        points=np.concatenate([vertices(p['attributes']['POSITION'])for p in g['meshes'][o['mesh']]['primitives']])
        # Vertex ordering can change during a fresh GLB export; compare the set.
        result[o['name']]={'category':o.get('extras',{}).get('category'),'points':np.unique(np.round(points,5),axis=0),'translation':np.array(o.get('translation',[0,0,0])),'rotation':o.get('rotation',[0,0,0,1]),'scale':o.get('scale',[1,1,1])}
    return result


def verify(base,variant):
    a,b=meshes(base),meshes(variant);unchanged=0;moved=0
    assert not any(n.startswith('主卧入口浅柜')for n in b)
    assert not any(n.startswith('过道浅柜')for n in b)
    for name,old in a.items():
        if old['category']in ('WallsLow','WallsUpper') or name.startswith('主卧入口浅柜') or name=='主卧入口吊顶':continue
        new=b[name]
        assert old['points'].shape==new['points'].shape and np.allclose(old['points'],new['points'],atol=.00002),name
        assert np.allclose(old['rotation'],new['rotation']) and np.allclose(old['scale'],new['scale']),name
        delta=new['translation']-old['translation']
        if name.startswith(('主卧双门','主卧玻璃门','主卧门竖纹')):
            assert np.allclose(delta,[.67,0,0],atol=.00001),name;moved+=1
        else:assert np.allclose(delta,[0,0,0],atol=.00001),name;unchanged+=1
    audit=check(variant,'inset');assert audit['passed']
    rows=read_meshes(variant)
    # The plain frontage must span the full former cabinet bay at every height.
    for z in (.05,.50,1.60,2.39,2.60):
        walls=unary_union([o['footprint']for o in rows if o['category']in ('WallsLow','WallsUpper') and o['lo'][2]<z<o['hi'][2]])
        section=walls.intersection(box(6.0,5.30,6.50,5.76))
        assert np.allclose(section.bounds,[6.26,5.30,6.38,5.76],atol=.0001),section.bounds
        assert box(6.261,5.291,6.379,5.889).difference(walls.buffer(.0001)).area<1e-6
    return {'unchanged_meshes':unchanged,'translated_door_meshes':moved,'door_offset_mm':670,'old_entry_cabinet_removed':True,'hall_cabinet_removed':True,'plain_wall_front_x_mm':6260,'plain_wall_thickness_mm':120,'architecture':audit,'passed':True}



if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--model',required=True);p.add_argument('--output',required=True);args=p.parse_args()
    report=verify(args.base,args.model);Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items()if k!='architecture'},ensure_ascii=False))
