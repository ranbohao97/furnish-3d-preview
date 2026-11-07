"""Build stable whole-item membership from exported node names and chair positions."""
import json,struct,re,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
ROOMS={'living':'客厅','study':'书房','dining':'餐厅','entry':'玄关','kitchen':'厨房','master':'主卧','guest':'次卧','store':'储藏间','masterbath':'主卫','guestbath':'客卫','laundry':'阳台','shared':'全屋'}
# Longest explicit prefix wins. Structural joinery and door hardware stay protected.
RULES={
 'tv':('电视与落地支架',['65英寸电视','电视落地支架','电视支架','回音壁']),
 'sofa':('沙发',['沙发']), 'lounge':('阳台躺椅',['休闲椅']), 'side-table':('休闲边几',['休闲边几']),
 'rug':('客厅地毯',['客厅地毯','地毯深色边线']), 'plant':('窗边绿植',['窗边绿植']),
 'dining-table':('圆餐桌',['圆餐桌']), 'vase':('餐桌花瓶',['餐桌花瓶','花枝','小花']),
 'floor-lamp':('落地灯',['落地灯','砖红落地灯罩']), 'desk-lamp':('书桌台灯',['书桌台灯','台灯臂','红色台灯罩']),
 'monitor':('显示器与键盘',['工位显示器','工位屏幕','显示器支架','键盘']), 'laptop':('笔记本电脑',['笔记本']),
 'desk-upper':('上侧书桌',['新版上侧独立书桌']), 'desk-lower':('下侧书桌',['新版下侧独立书桌']),
 'craft-table':('手工桌与工具板',['手工桌桌面','手工桌侧腿','手工桌背挡','手工桌工具挂板','工具挂钩']),
 'craft-cabinet':('手工小吊柜',['手工小吊柜']), 'spools':('手工线轴架',['手工线轴架','手工线轴']),
 'sewing':('缝纫机',['缝纫机','缝纫线轴']), 'craft-stool':('手工圆凳',['手工桌收起圆凳','手工凳腿']),
 'entry-cabinet':('整排玄关柜与换鞋凳',['玄关']),
 'sideboard':('餐边展示柜',['餐边展示','餐边玻璃','餐边工作台','餐边开放','餐边柜','餐边层板']),
 'coffee':('咖啡机与杯具',['餐边咖啡机','餐边备用杯','餐边咖啡杯']),
 'fridge':('冰箱',['法式冰箱']), 'dishwasher':('洗碗机',['洗碗机箱体','洗碗机面板','洗碗机黑色']),
 'pantry':('冰箱旁高柜',['冰箱旁窄高柜']), 'prep-cabinet':('备餐抽屉柜',['备餐窄抽屉']),
 'robot':('扫地机器人与基站',['扫地机自动上下水基站','扫地机器人','扫地机防水托盘']),
 'robot-cabinet':('窗侧扫地机设备柜',['扫地机设备柜','扫地机洞口','窗侧钢台面']),
 'sink-unit':('水槽半岛与台盆',['水槽柜','岛台不锈钢台面','水槽内','厨房鹅颈','水槽下水口','水槽存水弯','水槽下分类桶','半岛']),
 'hob-cabinet':('灶下橱柜',['灶下橱柜','灶侧钢台面']), 'hob':('燃气灶',['嵌入式燃气灶','炉头','炉架']),
 'hood':('油烟机',['钢制抽油烟机','烟机风管']), 'corner-cabinet':('厨房转角柜',['厨房盲角','厨房转角连续钢台面']),
 'pipe-cabinet':('管井前地柜',['管井前地柜','管井前钢台面']),
 'washer':('洗衣机',['洗衣机门圈','洗衣机玻璃门','洗衣机控制板','洗衣机']),
 'dryer':('烘干机',['烘干机']),
 'laundry-cabinet':('洗烘收纳柜与层板',['洗烘柜','洗烘区收纳','洗烘顶部收纳','洗烘设备','洗烘右侧','洗烘上柜','洗烘叠放','洗衣机上层板','洗烘层板']),
 'master-bed':('主卧床',['主床','床尾橄榄绿毯','极简床头木板']),
 'wardrobe-foot':('主卧床尾衣柜',['主卧床尾衣柜']), 'wardrobe-long':('主卧长衣柜',['主卧长衣金属衣柜','主卧长衣柜']),
 'master-shallow':('主卧入口浅柜',['主卧入口浅柜']), 'bedside-north':('主卧悬浮床头柜',['床侧悬浮小抽屉']),
 'bedside-south':('主卧床头柜',['床头柜南']), 'vanity':('主卧梳妆台',['主卧梳妆台','梳妆浅抽屉','梳妆镜']),
 'vanity-stool':('梳妆圆凳',['梳妆圆凳','圆凳脚']), 'bay-pad':('飘窗软垫',['飘窗软垫']),
 'guest-bed':('次卧床',['次卧床框','次卧床垫','次卧被褥','次卧床头','次卧枕头']),
 'guest-bedside':('次卧床头柜',['次卧床头柜']), 'guest-cabinet':('次卧收纳柜',['次卧分格收纳柜']),
 'store-shelves':('储物层板与收纳箱',['储物间长边浅层板','储物间层板立撑','储物间收纳箱']),
 'master-toilet':('主卫马桶',['主卫马桶主体','主卫马桶座','主卫马桶后背','主卫马桶盖板']),
 'master-basin':('主卫台盆柜',['主卫台盆']), 'master-mirror':('主卫镜柜',['主卫镜柜']),
 'master-toilet-cabinet':('主卫马桶背柜',['主卫马桶背柜']),
 'guest-toilet':('客卫马桶',['客卫马桶']), 'guest-basin':('客卫洗手台',['客卫方形洗手台','客卫排水存水弯']),
 'master-shower':('主卫花洒',['主卫淋浴']), 'guest-shower':('客卫花洒',['客卫淋浴']),
 'master-towel':('主卫毛巾杆与手巾',['主卫毛巾杆','主卫手巾']),
 'master-paper':('主卫纸巾架',['主卫纸巾']), 'guest-paper':('客卫纸巾架',['客卫纸巾']),
 'art':('几何装饰画',['几何画','画作红圆','画作蓝方']), 'photo-board':('餐厅照片板',['餐厅照片板','餐厅装饰卡片','照片板图钉']),
 'dining-light':('餐桌吊灯',['餐桌吊灯']), 'master-light':('主卧纸灯',['主卧纸灯']), 'guest-light':('次卧球灯',['次卧球灯'])
}
PARENTS={'vase':'dining-table','coffee':'sideboard','monitor':'desk-upper','laptop':'desk-lower','desk-lamp':'desk-upper','sewing':'craft-table','hob':'hob-cabinet'}
PROTECTED=('入户门','次卧门','主卫门','客卫平开门','储物间柜门','储物间封闭柜门','装饰隔断','隔断方格','厨房砖缝','厨房小方砖','主卧飘窗台','飘窗木台面','客卫暗装轨道','主卫浴帘轨道','扫地机供水检修阀','洗碗机隔侧板')

def load(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);blob=b[28+n:]
 def center(o):
  points=[]
  for p in g['meshes'][o['mesh']]['primitives']:
   a=g['accessors'][p['attributes']['POSITION']];points.extend([a['min'],a['max']])
  # All current GLB furniture nodes are unparented. Apply quaternion + scale.
  x,y,z,w=o.get('rotation',[0,0,0,1]);rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
  return (np.mean(points,axis=0)*o.get('scale',[1,1,1]))@rot.T+o.get('translation',[0,0,0])
 rows=[(n,center(n))for n in g['nodes']if 'mesh'in n]
 return rows

def build():
 result={'version':1,'items':{},'models':{}}
 for layout in ('current','inset'):
  for width in (600,700,800):
   key=f'{layout}-{width}';suffix=f'-inset-{width}'if layout=='inset'else(''if width==700 else f'-{width}')
   path=ROOT/f'home-model{suffix}.glb';rows=load(path);members={}
   seeds={prefix:sorted([(o['name'],pos)for o,pos in rows if o['name'].startswith(prefix)],key=lambda x:tuple(x[1]))for prefix in ('日常餐椅座面','人体工学椅座面','明装筒灯','床头阅读灯罩')}
   for o,pos in rows:
    name=o['name'];cat=o.get('extras',{}).get('category');room=o.get('extras',{}).get('room','shared')
    if cat not in ('Furniture','Storage','Appliances','Decor','Lighting')or name.startswith(PROTECTED):continue
    ident=None;label=None
    for prefix,seed,labelbase in [('日常餐椅','日常餐椅座面','餐椅'),('人体工学椅','人体工学椅座面','办公椅'),('明装筒灯','明装筒灯','筒灯'),('筒灯发光面','明装筒灯','筒灯'),('床头阅读灯','床头阅读灯罩','床头阅读灯')]:
     if name.startswith(prefix):
      i=min(range(len(seeds[seed])),key=lambda i:np.linalg.norm((pos-seeds[seed][i][1])[[0,2]]));ident=f'{seed}-{i}';label=f'{labelbase} {i+1}';break
    if name.startswith('独立书桌钢架'):ident='desk-upper' if -pos[2]>7 else 'desk-lower';label=RULES[ident][0]
    if not ident:
     matches=[(len(p),i,l)for i,(l,ps)in RULES.items()for p in ps if name.startswith(p)]
     if matches:_,ident,label=max(matches)
    if not ident:
     # A complete unclassified decor object remains selectable as a named item.
     ident='item-'+re.sub(r'\.\d+$','',name);label=re.sub(r'\.\d+$','',name)
    members[name]=ident
    info={'label':label,'room':ROOMS.get(room,room)}
    if ident in PARENTS:info['parent']=PARENTS[ident]
    result['items'][ident]=info
   result['models'][key]={'model_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'members':members}
 (ROOT/'edit-catalog.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
 print('Items:',len(result['items']),'members per model:',{k:len(v['members'])for k,v in result['models'].items()})
if __name__=='__main__':build()
