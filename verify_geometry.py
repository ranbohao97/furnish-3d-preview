from pathlib import Path
import struct,json,itertools,numpy as np, argparse
args=argparse.ArgumentParser();args.add_argument('--model',default='home-model.glb');args.add_argument('--output',default='geometry-checks.json');args=args.parse_args()
r=Path(__file__).resolve().parent;b=(r/args.model).read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);rows=[]
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
checks['entry_clear_mm']=round((1.79-bound(['玄关通顶柜','玄关A','玄关B','玄关C','玄关D'])[1][0])*1000,1)
checks['dining_west_route_mm']=round((bound('日常餐椅')[0][0]-bound(['餐边通顶柜E','餐边E'])[1][0])*1000,1)
checks['desk_rear_conservative_mm']=round((bound('手工桌桌面')[0][0]-bound('人体工学椅')[1][0])*1000,1)
checks['bed_foot_min_mm']=round((bound('主床床架')[0][0]-bound(['床尾浅柜','床尾浅衣柜'])[1][0])*1000,1)
checks['guest_storage_front_mm']=round((bound('次卧分格收纳柜')[0][1]-bound('次卧日床框架')[1][1])*1000,1)
checks['kitchen_wall_cabinets']=len([v for v in rows if v['extras'].get('room')=='kitchen' and ('吊柜'in v['name'] or '厨房开放层板'in v['name'] or '厨房高柜'in v['name'])])
checks['front_panels_with_inspection_toggle']=sum(bool(v['extras'].get('front_panel'))for v in rows)
checks['triangle_counter_outline_mm']=[[3710,3935],[4380,3935],[3750,4600],[3710,4600]]
checks['entry_run_height_mm']=round(bound(['玄关通顶柜','餐边通顶柜E'])[1][2]*1000,1)
checks['entry_run_length_mm']=round((bound(['玄关通顶柜','餐边通顶柜E'])[1][1]-bound(['玄关通顶柜','餐边通顶柜E'])[0][1])*1000,1)
checks['entry_modules']=json.loads((r/'entry-storage.json').read_text())['modules']
for module in checks['entry_modules']:
 lo,hi=bound(module['name'])
 assert abs(hi[2]-2.40)<.001 and abs((hi[1]-lo[1])*1000-module['width_mm'])<.5
lo,hi=bound('玄关柜顶局部吊顶')
checks['entry_soffit_underside_mm']=round(lo[2]*1000,1)
checks['entry_soffit_drop_mm']=round((hi[2]-lo[2])*1000,1)
assert checks['entry_soffit_underside_mm']==2400 and checks['entry_soffit_drop_mm']==320
checks['sideboard_width_mm']=760
partition=[v for v in rows if v['name'].startswith('餐边通顶柜E通顶侧板') and abs(v['min'][1]-3.65)<.001]
checks['entry_sideboard_partition_full_height']=any(v['min'][2]<=.081 and v['max'][2]>=2.379 for v in partition)
assert checks['entry_sideboard_partition_full_height']
checks['old_entry_bench_or_low_sideboard']=sum(v['name'].startswith(('换鞋凳','餐边成品柜','玄关鞋柜')) for v in rows)
assert checks['old_entry_bench_or_low_sideboard']==0
assert checks['entry_run_height_mm']==2400 and checks['entry_run_length_mm']==3230
lo,hi=bound('65英寸电视屏幕')
checks['tv_screen_width_mm']=round((hi[1]-lo[1])*1000,1)
checks['tv_screen_height_mm']=round((hi[2]-lo[2])*1000,1)
checks['tv_screen_diagonal_inches']=round(float(np.hypot(hi[1]-lo[1],hi[2]-lo[2])/.0254),3)
checks['tv_center_height_mm']=round((hi[2]+lo[2])*500,1)
checks['old_tv_cabinet_or_wall_tv']=sum(v['name'].startswith(('电视悬浮矮柜','壁挂电视'))for v in rows)
assert abs(checks['tv_screen_diagonal_inches']-65)<.01 and checks['old_tv_cabinet_or_wall_tv']==0
lo,hi=bound('电视落地支架底座');checks['tv_stand_base_mm']=[round((hi[i]-lo[i])*1000,1)for i in range(3)]
assert abs(lo[2]-.025)<.001
checks['coffee_tables']=sum('茶几'in v['name'] for v in rows)
assert checks['coffee_tables']==0
checks['handcraft_desktop_mm']=[round(float(v)*1000,1) for v in (bound('手工桌桌面')[1]-bound('手工桌桌面')[0])]
assert checks['handcraft_desktop_mm']==[560.0,1280.0,30.0]
assert abs(bound('手工桌桌面')[1][2]-.75)<.001
checks['store_cad_envelope_mm']=[1530,850]
checks['store_closed_door_panels']=sum(v['name'].startswith('储物间封闭柜门') for v in rows)
assert checks['store_closed_door_panels']==2
checks['study_monitors']=sum(v['name'].startswith('工位显示器') for v in rows)
assert checks['study_monitors']==1 and bound('工位显示器')[0][1]>7.5
assert bound('笔记本底座')[1][1]<7.0
checks['robot_room']=[v['extras']['room']for v in rows if v['name']=='扫地机自动上下水基站'][0]
assert checks['robot_room']=='kitchen'
assert bound('厨房鹅颈水龙头')[0][0]<1.84
checks['service_meshes']=sum(v['extras'].get('category')=='Services' for v in rows)
assert checks['service_meshes']>=16
assert not any(v['name'].startswith('家政柜') for v in rows)
checks['mesh_count']=len(g['meshes']);checks['embedded_images']=len(g.get('images',[]))
assert checks['kitchen_wall_cabinets']==0
assert abs(checks['kitchen_counter_clear_mm']-960)<.5
assert checks['entry_clear_mm']>=1000 and checks['dining_west_route_mm']>=750 and checks['bed_foot_min_mm']>=630 and checks['guest_storage_front_mm']>=840
(r/args.output).write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(json.dumps(checks,ensure_ascii=False,indent=2))
