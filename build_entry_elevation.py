from pathlib import Path
import json
r=Path(__file__).resolve().parent
# A dimensioned cabinet elevation, generated from the same module widths.
zones=json.loads((r/'entry-storage.json').read_text());out=[]
def add(x):out.append(x)
def text(x,y,t,size=16,fill='#363c34',anchor='middle'):
 add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}">{t}</text>')
def rect(x,y,w,h,fill='#ebe0ca',stroke='#88765c'):
 add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}"/>')
add('<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="1040" viewBox="0 0 1120 1040"><rect width="1120" height="1040" fill="#f8f5ed"/><g font-family="PingFang SC,Microsoft YaHei,sans-serif">')
text(64,50,'玄关高柜与吊顶 · 五段分区',28,anchor='start');text(64,81,'从入户向餐桌方向展开｜尺寸为概念方案，单位 mm',15,'#77776b',anchor='start')
x0=110;yt=160;sx=.29;sz=.23;Y=lambda z:yt+(2720-z)*sz
text(580,119,'总长 3230  ·  柜体深 420  ·  柜高 2400 + 局部吊顶 320',19)
labels=[['A · 日常鞋','常穿鞋 / 可调鞋层'],['B · 归家随手位','鞋履 / 钥匙小物'],['C · 长靴雨伞','长靴 / 干伞独立格'],['D · 通勤备品','包袋 / 分盒日用品'],['E · 小餐边区','餐具 / 水杯 / 托盘']]
for i,m in enumerate(zones['modules']):
 x=x0+(m['y_mm'][0]-1180)*sx;w=m['width_mm']*sx
 rect(x,yt,w,320*sz,'#e1ded5');rect(x,Y(2400),w,2400*sz,'#b98d5c');rect(x+5,Y(2380),w-10,380*sz,'#e9dfcb')
 text(x+w/2,Y(2170),'低频收纳',15)
 rect(x+5,Y(1980),w-10,(1980-80)*sz,'#f0e8d7')
 if i==0:
  for z in (250,480,710,940,1170,1400,1630,1860):rect(x+9,Y(z),w-18,4,'#d6b68a')
  text(x+w/2,Y(1050),'日常鞋层',16);text(x+w/2,Y(130),'常穿鞋位',13)
 elif i==1:
  rect(x+5,Y(1550),w-10,600*sz,'#d6e2df')
  text(x+w/2,Y(1300),'镜面 / 挂钩',15);text(x+w/2,Y(1110),'钥匙随手台',15)
  text(x+w/2,Y(1850),'随身小物',16);text(x+w/2,Y(550),'鞋履层板',16)
 elif i==2:
  rect(x+w*.7,Y(1160),w*.3-5,1080*sz,'#d6e2df');text(x+w*.34,Y(430),'长靴位',16);text(x+w*.83,Y(650),'干伞',12)
  text(x+w/2,Y(1610),'可调鞋层',16)
 elif i==3:
  for z in (550,1020,1490):rect(x+9,Y(z),w-18,4,'#d6b68a')
  text(x+w/2,Y(1750),'分盒备品',16);text(x+w/2,Y(800),'通勤包',16)
 else:
  rect(x+5,Y(1550),w-10,650*sz,'#d6e2df');text(x+w/2,Y(1830),'杯碟上柜',16)
  text(x+w/2,Y(1260),'水杯 / 托盘',16);text(x+w/2,Y(1060),'900 高餐边台',15)
  rect(x+5,Y(880),w-10,250*sz,'#d3b58d');text(x+w/2,Y(730),'餐具浅抽屉',15)
  text(x+w/2,Y(350),'餐具移门柜',16)
 rect(x,Y(2400),w,20*sz,'#ddd6c8');text(x+w/2,143,str(m['width_mm']),15)
 text(x+w/2,Y(0)+30,labels[i][0],16);text(x+w/2,Y(0)+55,labels[i][1],13,'#757568')
text(68,470,'2400',16);text(580,203,'局部吊顶 · 下吊 320',16);text(64,893,'玄关收纳 2470 mm（约 76.5%）｜餐边收纳 760 mm（约 23.5%）',19,anchor='start')
text(64,930,'柜顶接局部吊顶；全高实板分隔餐具与鞋包，顶层收纳轻物。',16,anchor='start')
text(64,960,'模型静态净距：入户约 1004 mm；餐椅西侧通路约 771 mm。',16,anchor='start')
text(64,990,'柜门 / 抽屉打开时需留操作空间；安装高度、收口、通风与检修须复尺深化。',15,'#77776b',anchor='start')
add('</g></svg>');(r/'entry-zones.svg').write_text('\n'.join(out))
