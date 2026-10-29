"""Reproducible, local assets for the measured concept model."""
from pathlib import Path
import json, random, math
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, box

ROOT = Path(__file__).resolve().parent
TEX = ROOT
TEX.mkdir(exist_ok=True)
rng = np.random.default_rng(603)
W=512; H=1024
x=np.linspace(0,1,W)[None,:]; y=np.linspace(0,1,H)[:,None]
grain=np.zeros((H,W))
for freq,amp in [(14,.12),(39,.045),(87,.025),(173,.012)]:
    grain += amp*np.sin((x+0.013*np.sin(y*13)+0.004*np.sin(y*43))*freq*math.pi)
grain+=rng.normal(0,.015,(H,W))
for name,base in [('walnut',(150,91,48)),('oak',(179,137,89))]:
    rgb=np.clip(np.array(base)[None,None,:]*(1+grain[:,:,None]*(.22 if name=='oak' else .55)),0,255).astype('uint8')
    Image.fromarray(rgb).save(TEX/(name+'.jpg'),quality=92)

# Coordinates are metres, read from the current CAD model-space plan, with
# +Y is plan top / south.
footprint=[(.07,.91),(.07,8.70),(.76,8.70),(.76,10.23),(6.21,10.23),
 (6.21,9.49),(7.20,9.49),(7.20,10.23),(9.80,10.23),(9.80,2.87),
 (8.06,2.87),(8.06,1.59),(4.21,1.59),(4.21,0),(1.87,0),(1.87,.91)]
poly=Polygon(footprint)
kitchen=box(1.79,.0,4.21,2.46)
guestbath=Polygon([(3.71,3.8),(5.22,3.8),(5.22,1.83),(4.21,1.83),(4.21,2.7),(3.71,2.7)])
masterbath=box(8.06,3.11,9.56,5.77)
bay=box(7.2,9.3,9.56,10.23)
wood=poly.difference(kitchen.union(guestbath).union(masterbath).union(bay))
planks=[]
for row in range(69):
    yy=row*.15
    offset=(row%3)*.4
    for col in range(-1,10):
        xx=col*1.2+offset
        q=wood.intersection(box(xx+.0015,yy+.0015,xx+1.1985,yy+.1485))
        if q.is_empty: continue
        for part in ([q] if q.geom_type=='Polygon' else getattr(q,'geoms',[])):
            if part.geom_type=='Polygon' and part.area>.002:
                planks.append({'p':[[round(a,5),round(b,5)] for a,b in list(part.exterior.coords)[:-1]],'variant':(row*7+col)%7})
data={'footprint':footprint,
 'wood_planks':planks,'floor_allowance_m':.10,'raw_height_m':2.82,
 'finished_height_m':2.72,'balcony_beam_raw_underside_m':2.06,
 'source_pdf':'private-source-plan.pdf',
 'source_dwg':'private-source-plan.dwg',
 'style_source':'Private owner style brief',
 'style_revision':2312,
 'design_revision':'使用动线优化 v2',
 'design_changes':['厨房无吊柜','CAD三角洗手台','低鞋柜及换鞋凳','厨房柜门朝工作通道','三把日常餐椅及一把备用折叠椅','床尾正向挂衣浅柜','修正主卧柜前墙','次卧日床转向','家政与储物分区'],
 'assumptions':['地面构造预留100mm，未获现场确认','家具为按图面占位重建的示意模型，非品牌精确模型','饰面、灯具和立面为风格演绎','主卫按当前图保留淋浴，浴缸待后续确认']}
(ROOT/'model-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
print('prepared',len(planks),'floor planks')
