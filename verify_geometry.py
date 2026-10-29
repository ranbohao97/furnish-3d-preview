from pathlib import Path
import struct,json,itertools,numpy as np
r=Path(__file__).resolve().parent;b=(r/'home-model.glb').read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);rows=[]
for nd in g['nodes']:
 if 'mesh'not in nd:continue
 t=np.array(nd.get('translation',[0,0,0]));scale=np.array(nd.get('scale',[1,1,1]));x,y,z,w=nd.get('rotation',[0,0,0,1]);R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
 ps=[]
 for primitive in g['meshes'][nd['mesh']]['primitives']:
  ac=g['accessors'][primitive['attributes']['POSITION']]
  for v in itertools.product(*zip(ac['min'],ac['max'])):
   q=R@(np.array(v)*scale)+t;ps.append([q[0],-q[2],q[1]])
 ps=np.array(ps);rows.append({'name':nd['name'],'min':ps.min(axis=0).tolist(),'max':ps.max(axis=0).tolist(),'extras':nd.get('extras',{})})
def bound(prefix):
 a=[v for v in rows if any(v['name'].startswith(p)for p in ([prefix]if isinstance(prefix,str)else prefix))];assert a,prefix
 return np.min([v['min']for v in a],axis=0),np.max([v['max']for v in a],axis=0)
checks={}
checks['kitchen_counter_clear_mm']=round((bound('窗侧钢台面')[0][0]-bound('岛台不锈钢台面')[1][0])*1000,1)
checks['entry_clear_mm']=round((1.79-bound(['玄关鞋柜','换鞋凳'])[1][0])*1000,1)
checks['dining_west_route_mm']=round((bound('日常餐椅')[0][0]-bound(['餐边成品柜','餐边不锈钢台面'])[1][0])*1000,1)
checks['desk_rear_conservative_mm']=round((bound(['家政分区柜门','家政柜门把手'])[0][0]-bound('人体工学椅')[1][0])*1000,1)
checks['bed_foot_min_mm']=round((bound('主床床架')[0][0]-bound(['床尾浅柜','床尾浅衣柜'])[1][0])*1000,1)
checks['guest_storage_front_mm']=round((bound('次卧分格收纳柜')[0][1]-bound('次卧日床框架')[1][1])*1000,1)
checks['kitchen_wall_cabinets']=len([v for v in rows if '吊柜'in v['name'] or '厨房开放层板'in v['name'] or '厨房高柜'in v['name']])
checks['front_panels_with_inspection_toggle']=sum(bool(v['extras'].get('front_panel'))for v in rows)
checks['triangle_counter_outline_mm']=[[3710,3935],[4380,3935],[3750,4600],[3710,4600]]
checks['mesh_count']=len(g['meshes']);checks['embedded_images']=len(g.get('images',[]))
assert checks['kitchen_wall_cabinets']==0
assert abs(checks['kitchen_counter_clear_mm']-960)<.5
assert checks['entry_clear_mm']>=1000 and checks['dining_west_route_mm']>=750 and checks['bed_foot_min_mm']>=630 and checks['guest_storage_front_mm']>=840
(r/'geometry-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(json.dumps(checks,ensure_ascii=False,indent=2))
