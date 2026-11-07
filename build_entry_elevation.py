"""Anonymous elevation corresponding to the revised CAD and white model."""
from pathlib import Path
import json
r=Path(__file__).resolve().parent
modules=[{'name':'归家鞋履','y_mm':[1170,2170],'width_mm':1000,'use':'下部鞋履 / 中部随手凹位 / 上部杂物'}, {'name':'挂物换鞋','y_mm':[2170,2770],'width_mm':600,'use':'坐凳抽屉 / 洞洞板 / 衣帽挂钩'}, {'name':'通勤换季','y_mm':[2770,4420],'width_mm':1650,'use':'包袋 / 换季鞋盒 / 日用品'}]
data={'revision':'v12-20261107','length_mm':3250,'carcass_depth_mm':380,'height_mm':2400,'ceiling_underside_mm':2400,'soffit_drop_mm':320,'modules':modules,'sideboard':{'bounds_mm':[310,760,4470,6070],'height_mm':965},'notes':['平面占位依新版 CAD；立面参考白模第5页，分区宽度与高度为暂定深化。']}
(r/'entry-storage.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
o=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 1200 900"><rect width="1200" height="900" fill="#f5f2eb"/><g font-family="PingFang SC,Microsoft YaHei,sans-serif" fill="#33473f">']
def text(x,y,t,size=18):o.append(f'<text x="{x}" y="{y}" font-size="{size}">{t}</text>')
def rect(x,y,w,h,fill):o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#7e887e"/>')
text(60,60,'玄关与餐边 · 新版白模立面分区',30);text(60,96,'CAD 整排 3250 × 380 mm；柜高暂取 2400 mm，上方局部吊顶 320 mm',18)
x=70;sy=.20;sx=.31;top=170
for i,m in enumerate(modules):
 w=m['width_mm']*sx;rect(x,top,w,64,'#dadbd5');rect(x,top+64,w,480,'#efeee8');text(x+15,top-18,str(m['width_mm'])+' mm')
 if i==0:
  rect(x+5,top+64+(2400-1480)*sy,w-10,(1480-950)*sy,'#d2c2a6')
  for z in (220,950,1480):o.append(f'<path d="M{x},{top+64+(2400-z)*sy}h{w}" stroke="#7e887e"/>')
 elif i==1:rect(x+7,top+73,w-14,370,'#d2c2a6');text(x+20,top+250,'挂物位');text(x+20,top+480,'换鞋坐凳')
 else:
  for j in range(1,4):o.append(f'<path d="M{x+w*j/4},{top+64}v480" stroke="#7e887e"/>')
 text(x+15,top+580,m['name'],22);text(x+15,top+611, f"{m['width_mm']} mm",17);x+=w
text(70,840,'餐边柜独立设于 y=4470..6070 mm：1600 × 450 mm，台面高暂取 965 mm。',19)
o.append('</g></svg>');(r/'entry-zones.svg').write_text(''.join(o))
