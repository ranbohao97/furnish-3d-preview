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
def size(name):
 lo,hi=bound(name);return [round(float(v)*1000,1) for v in hi-lo]
def near(actual,expected,tol=.5):assert abs(actual-expected)<=tol,(actual,expected)
checks['revision']='v12.1 / construction details / CAD 2026-11-07'
assert size('新版上侧独立书桌')==[700.0,1400.0,40.0]
assert size('新版下侧独立书桌')==[700.0,1400.0,40.0]
lo,hi=bound('圆餐桌桌面');assert abs((lo[0]+hi[0])/2-2.09)<.001 and abs((lo[1]+hi[1])/2-3.42)<.001
checks['dining_chairs']=sum(v['name'].startswith('日常餐椅座面') for v in rows);assert checks['dining_chairs']==4
checks['mesh_count']=len(g['meshes'])
checks['entry_carcass_mm']=size('玄关通顶柜')
assert checks['entry_carcass_mm']==[380.0,3250.0,2320.0]
checks['entry_top_height_mm']=round(bound('玄关通顶柜')[1][2]*1000);assert checks['entry_top_height_mm']==2400
checks['entry_soffit_underside_mm']=round(bound('玄关柜顶局部吊顶')[0][2]*1000)
assert checks['entry_soffit_underside_mm']==2400
checks['entry_clear_mm']=round((1.79-bound(['玄关鞋履','玄关归家','玄关通勤','玄关坐垫'])[1][0])*1000,1)
assert checks['entry_clear_mm']>1040
checks['sideboard_mm']=size('餐边工作台')
assert checks['sideboard_mm']==[450.0,1600.0,25.0]
checks['dry_basin_mm']=size('客卫方形洗手台陶瓷盆沿')[:2]
assert checks['dry_basin_mm']==[600.0,500.0]
assert bound('客卫方形洗手台镜子')[0][1]>3.92
checks['old_triangle_meshes']=sum(any(k in v['name'] for k in ['三角','斜面柜门']) for v in rows)
assert checks['old_triangle_meshes']==0
checks['guest_bed_mm']=size('次卧床框')[:2]
assert checks['guest_bed_mm']==[2000.0,1200.0]
checks['guest_door_hinge_y_mm']=4360
checks['store_door_envelope_mm']=size('储物间柜门框')
assert checks['store_door_envelope_mm']==[60.0,750.0,2400.0]
checks['store_cad_clear_outline_mm']=[[6300,4420],[6500,4420],[6500,4170],[7480,4170],[7480,4420],[7910,4420],[7910,5170],[6300,5170]]
checks['store_closed_door_panels']=sum(v['name'].startswith('储物间封闭柜门')for v in rows)
assert checks['store_closed_door_panels']==2
checks['master_wardrobe_carcass_depth_mm']=size('主卧床尾衣柜底板')[0]
assert checks['master_wardrobe_carcass_depth_mm']==550
checks['master_bed_foot_clear_mm']=round((bound('主床床架')[0][0]-bound('主卧床尾衣柜封闭门')[1][0])*1000,1)
assert 440<checks['master_bed_foot_clear_mm']<460
checks['guest_cabinet_front_clear_mm']=round((bound('次卧分格收纳柜')[0][1]-bound('次卧床框')[1][1])*1000,1)
assert checks['guest_cabinet_front_clear_mm']>580
checks['kitchen_counter_clear_mm']=round((bound('窗侧钢台面')[0][0]-bound('岛台不锈钢台面')[1][0])*1000,1)
near(checks['kitchen_counter_clear_mm'],960)
checks['kitchen_upper_cabinets']=sum(v['extras'].get('room')=='kitchen' and '吊柜'in v['name']for v in rows)
checks['coffee_tables']=sum('茶几'in v['name'] for v in rows)
checks['tv_cabinets']=sum('电视柜'in v['name']or '电视悬浮矮柜'in v['name'] for v in rows)
assert checks['kitchen_upper_cabinets']==checks['coffee_tables']==checks['tv_cabinets']==0
lo,hi=bound('65英寸电视屏幕');checks['tv_inches']=round(float(np.hypot(hi[1]-lo[1],hi[2]-lo[2])/.0254),3);near(checks['tv_inches'],65,.01)
checks['handcraft_desktop_mm']=size('手工桌桌面');assert checks['handcraft_desktop_mm']==[560.0,1280.0,30.0]
checks['spool_shelves']=sum(v['name'].startswith('手工线轴架层板')for v in rows);assert checks['spool_shelves']==3
checks['study_monitors']=sum(v['name'].startswith('工位显示器')for v in rows);assert checks['study_monitors']==1
assert bound('工位显示器')[0][1]>7.5 and bound('笔记本底座')[1][1]<7.0
checks['robot_room']=[v['extras']['room']for v in rows if v['name']=='扫地机自动上下水基站'][0];assert checks['robot_room']=='kitchen'
checks['service_meshes']=sum(v['extras'].get('category')=='Services'for v in rows);assert checks['service_meshes']>=16
checks['front_panels']=sum(bool(v['extras'].get('front_panel'))for v in rows)
checks['wardrobe_end_panels']=sum('端侧板' in v['name']for v in rows)
assert checks['wardrobe_end_panels']==4
assert not any('侧移门' in v['name']for v in rows)
for prefix,axis,edges,depth_axis,depth in [
 ('主卧床尾衣柜',1,[6.99,9.282],0,[6.525,7.05]),
 ('主卧长衣金属衣柜',0,[6.38,7.892],1,[5.335,5.89])]:
 panels=sorted([v for v in rows if v['name'].startswith(prefix+'端侧板')],key=lambda v:v['min'][axis])
 for v,edge in zip(panels,edges):
  near(v['min'][axis],edge,.0001);near(v['max'][axis]-v['min'][axis],.018,.0001)
  near(v['min'][2],.08,.0001);near(v['max'][2],2.43,.0001)
  near(v['min'][depth_axis],depth[0],.0001);near(v['max'][depth_axis],depth[1],.0001)
  assert not v['extras'].get('front_panel'), 'End panels must remain visible in interior mode'
washer=next(v for v in rows if v['name']=='洗衣机')
checks['washer_back_clearance_mm']=round((bound('洗烘柜背板')[0][0]-washer['max'][0])*1000,1)
assert checks['washer_back_clearance_mm']>=9.9
for machine,z in [('洗衣机',.02),('烘干机',.89)]:
 row=next(v for v in rows if v['name']==machine)
 near(row['min'][2],z,.0001)
 if machine=='烘干机':near(row['min'][2],bound('洗烘叠放连接托架')[1][2],.0001)
assert bound('洗烘设备分隔立板')[1][1]<=washer['min'][1]+.001
assert bound('洗烘设备右立板')[0][1]>=washer['max'][1]-.001
near(bound('洗衣机上层板')[1][0],bound('洗烘柜背板')[0][0],.0001)
checks['plinth_end_returns']=sum('踢脚端回板' in v['name']for v in rows)
assert checks['plinth_end_returns']>=20
near(bound('餐边备用杯')[0][2],.558,.0001)
assert bound('几何画木框')[0][2]>bound('餐边开放层板')[1][2]
for v in rows:
 if v['name'].startswith('储物间收纳箱'):
  assert min(abs(v['min'][2]-z) for z in [.62,1.12,1.62])<.0001
assert not any(v['name']=='厨房转角封板'for v in rows)
checks['construction_details']=sum(bool(v['extras'].get('construction_detail'))for v in rows)
checks['floor_meshes']=sum(v['extras'].get('category')=='Floor'for v in rows);assert checks['floor_meshes']<12
# Independent point checks against unioned walls: old portals were removed and new ones remain open.
from shapely.geometry import Polygon, Point
walls=json.loads((r/'wall-footprints.json').read_text())
def blocked(x,y):return any(w['z1']<1.6<w['z2'] and Polygon(w['p']).covers(Point(x,y))for w in walls)
for pt in [(4.8,4.35),(5.8,4.36),(6.28,4.80),(5.61,6.40)]:assert not blocked(*pt),('doorway blocked',pt)
for pt in [(4.0,3.86),(6.7,4.11),(6.7,5.23),(5.6,5.70)]:assert blocked(*pt),('wall missing',pt)
checks['wall_opening_point_checks']='passed'
(r/args.output).write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(json.dumps(checks,ensure_ascii=False,indent=2))
