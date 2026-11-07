"""2026-11-07 CAD footprints + designer white-model elevations.
Horizontal coordinates are measured; elevations without dimensions are conceptual.
The owner's no-coffee-table / floor-TV / no-kitchen-upper-cabinet decisions prevail.
"""
import math

def build_entry(api):
    rect,box,tube,cyl,cabinet=[api[n] for n in ('rect','box','tube','cyl','cabinet')]
    H=api['H'];white='kitchen_white'
    # CAD: x=310..690, y=1170..4420. White model p5: niche / coat bay / tall run.
    for ya,yb in [(1.17,2.17),(2.17,2.77),(2.77,4.42)]:
        for yy in (ya,yb-.018):rect('玄关通顶柜侧板',.31,.69,yy,yy+.018,.08,2.40,white,'Storage','entry')
        rect('玄关通顶柜背板',.31,.328,ya,yb,.08,2.40,white,'Storage','entry')
        for zz in (.08,2.382):rect('玄关通顶柜横板',.328,.69,ya+.018,yb-.018,zz,zz+.018,white,'Storage','entry')
    cabinet('玄关鞋履下柜',.328,.672,1.19,2.15,.95,'x+',white,'entry',base=.22)
    cabinet('玄关归家上柜',.328,.672,1.19,2.15,2.38,'x+',white,'entry',base=1.48)
    rect('玄关钥匙台',.328,.70,1.19,2.15,.95,.975,'walnut','Storage','entry')
    rect('玄关凹位镜',.329,.335,1.25,2.09,1.03,1.42,'mirror','Decor','entry')
    box('玄关随手托盘',(.53,1.64,.995),(.21,.27,.03),'steel','Decor','entry',.012)
    for yy in (1.40,1.79):
        for dy in (-.05,.05):api['sphere']('玄关常穿鞋',(.51,yy+dy,.13),(.145,.04,.04),'tan','Storage','entry')
    cabinet('玄关换鞋凳抽屉',.328,.672,2.19,2.75,.44,'x+',white,'entry',drawers=True)
    rect('玄关坐垫',.335,.69,2.20,2.74,.44,.475,'ivory','Furniture','entry',.025)
    rect('玄关挂物洞洞板',.33,.35,2.20,2.74,.49,2.36,'tan','Storage','entry')
    for z in (.8,1.1,1.4,1.7,2.0):
        for yy in (2.29,2.47,2.65):cyl('玄关挂板孔',(.353,yy,z),.012,.004,'black','Decor','entry',12,(0,math.pi/2,0))
    for yy in (2.30,2.62):tube('玄关衣帽挂钩',[(.36,yy,1.65),(.43,yy,1.65),(.43,yy,1.70)],.007,'steel','Storage','entry')
    cabinet('玄关通勤及换季高柜',.328,.672,2.79,4.40,2.38,'x+',white,'entry',base=.10)
    rect('玄关柜顶局部吊顶',.31,.75,1.17,4.42,2.40,H,'ceiling','Ceiling','entry')
    # Separate small sideboard at the dining end; not a TV cabinet.
    cabinet('餐边展示下柜',.31,.742,4.47,6.07,.52,'x+',white,'dining',drawers=True)
    cabinet('餐边玻璃展示柜',.31,.742,4.47,6.07,.94,'x+',white,'dining',base=.54)
    # Replace only the display doors with glass, keeping carcasses opaque.
    for o in list(api['bpy'].data.objects):
        if o.name.startswith('餐边玻璃展示柜柜门') and '拉手' not in o.name:
            o.data.materials.clear();o.data.materials.append(api['M']['glass'])
    rect('餐边工作台',.31,.76,4.47,6.07,.94,.965,'walnut','Storage','dining')
    for zz in (1.35,1.74):rect('餐边开放层板',.32,.56,4.55,6.00,zz,zz+.025,white,'Storage','dining')
    for yy in (4.70,4.91,5.55,5.76):
        cyl('餐边备用杯',(.54,yy,.67),.04,.12,'white','Decor','dining')
    box('餐边咖啡机',(.53,5.50,1.11),(.29,.32,.29),'steel','Appliances','dining',.025)
    box('餐边咖啡机出水口',(.70,5.50,1.10),(.08,.12,.045),'black','Appliances','dining')
    cyl('餐边咖啡杯',(.70,5.50,1.01),.037,.08,'white','Decor','dining')

def build_detail(api):
    rect,box,tube,cyl,cabinet=[api[n] for n in ('rect','box','tube','cyl','cabinet')]
    H=api['H'];white='kitchen_white'
    # Master entrance: framed double leaves, glazed middle, fluted privacy inserts.
    for ya,yb in [(5.89,5.925),(6.955,6.99)]:rect('主卧双门门套',5.53,5.69,ya,yb,0,2.43,white,'Doors','master')
    rect('主卧双门上门套',5.53,5.69,5.89,6.99,2.39,2.43,white,'Doors','master')
    for ya,yb in [(5.93,6.433),(6.447,6.95)]:
        # Closed pose keeps the white-model composition; pass-through mode crosses doors.
        for a,b in [(ya,ya+.035),(yb-.035,yb)]:rect('主卧玻璃门边框',5.59,5.63,a,b,.02,2.38,white,'Doors','master')
        for z0,z1 in [(.02,.30),(1.78,1.82),(2.34,2.38)]:rect('主卧玻璃门横框',5.59,5.63,ya,yb,z0,z1,white,'Doors','master')
        rect('主卧双门磨砂玻璃',5.605,5.615,ya+.035,yb-.035,.30,2.34,'glass','Doors','master')
        for i in range(15):
            yy=ya+.05+i*(yb-ya-.10)/14
            rect('主卧门竖纹',5.604,5.618,yy,yy+.004,.32,1.76,'ivory','Doors','master',0)
        tube('主卧双门把手',[(5.56,(ya+yb)/2,1.02),(5.56,(ya+yb)/2,1.18)],.008,'steel','Doors','master')
    # White-model craft wall: three shallow spool shelves below the upper cabinets.
    for z in (1.08,1.31,1.54):
        rect('手工线轴架层板',6.04,6.18,7.20,8.30,z,z+.018,white,'Storage','study')
        for i in range(11):cyl('手工线轴',(6.10,7.25+i*.095,z+.085),.027,.13,['ivory','tan','green'][i%3],'Decor','study',12)
    # Closed cupboard over the stacked machines, as in the white-model elevation.
    cabinet('洗烘顶部收纳',5.54,6.18,9.14,9.82,2.40,'x-',white,'laundry',base=1.78)
    # Gallery notice board on the dining / guest-bath wall; avoids the new sink niche.
    rect('餐厅照片板',3.438,3.456,2.70,4.34,1.12,2.20,'ivory','Decor','dining')
    for i,(y,z,w,h) in enumerate([(2.88,1.45,.20,.28),(3.16,1.68,.24,.34),(3.48,1.45,.22,.25),(3.82,1.77,.24,.35),(4.10,1.49,.20,.29),(2.85,1.96,.16,.20),(3.49,2.00,.18,.18),(4.12,2.04,.19,.17)]):
        box('餐厅装饰卡片',(3.428,y,z),(.008,w,h),['white','tan','ivory'][i%3],'Decor','dining',.002)
        cyl('照片板图钉',(3.42,y,z+h/2-.025),.009,.008,'steel','Decor','dining',12,(0,math.pi/2,0))
    # Beam / dropped ceiling composition seen on PDF p1, p11, p16, p18–24.
    for name,b,z in [
        ('走廊横向吊顶',(3.47,6.38,4.42,5.42),2.40),
        ('主卧入口吊顶',(5.54,9.56,5.89,6.30),2.40),
        ('主卧柜顶吊顶',(6.50,7.10,6.30,9.30),2.43),
        ('次卧柜顶吊顶',(6.38,7.91,3.63,4.30),2.40),
        ('玄关横梁吊顶',(.31,3.47,2.12,2.30),2.40),
        ('工位纵向吊顶',(3.47,3.72,5.42,8.41),2.40)]:rect(name,*b,z,H,'ceiling','Ceiling')
    for y in (9.51,9.76):box('飘窗软垫',(8.35,y,.60),(1.65,.23,.10),'ivory','Furniture','master',.035)
    # Designer white cabinetry beyond the kitchen; timber remains on selected desktops.
    for o in api['bpy'].data.objects:
        if o.type=='MESH' and o.get('room') in ('master','guest','laundry') and o.get('category')=='Storage':
            for slot in o.material_slots:
                if slot.material==api['M']['walnut']:slot.material=api['M'][white]
        if o.name.startswith(('主卧床尾衣柜侧移门','主卧长衣金属衣柜侧移门')):
            o['front_panel']=True

def finish_revision(api):
    """Additional white-model details, idempotent for exports from a saved scene."""
    bpy=api['bpy']
    mirror=bpy.data.objects.get('客卫方形洗手台镜子')
    if mirror:mirror.location.y=3.932
    if '主卫马桶背柜台面' in bpy.data.objects:return
    rect,box,tube,cyl,cabinet=[api[n] for n in ('rect','box','tube','cyl','cabinet')]
    # CAD L-shaped vanity returns along the wall behind the toilet (PDF p24).
    rect('主卫马桶背柜',9.30,9.54,3.93,4.80,0,.80,'kitchen_white','Storage','masterbath')
    rect('主卫马桶背柜台面',9.28,9.54,3.93,4.80,.80,.825,'white','Furniture','masterbath')
    rect('主卫台盆衔接台面',9.00,9.54,4.73,4.80,.80,.825,'white','Furniture','masterbath')
    cabinet('主卫镜柜',9.40,9.53,4.80,5.60,1.96,'x-','kitchen_white','masterbath',base=1.12)
    for o in list(bpy.data.objects):
        if o.name.startswith('主卫台盆镜子'):bpy.data.objects.remove(o,do_unlink=True)
        elif o.name.startswith('主卫镜柜柜门') and '拉手' not in o.name:
            o.data.materials.clear();o.data.materials.append(api['M']['mirror'])
        elif o.name.startswith('主卫台盆悬空柜'):
            for slot in o.material_slots:
                if slot.material==api['M']['walnut']:slot.material=api['M']['kitchen_white']
    # Small blinds match the bedroom / bath white-model elevations.
    for name,x1,x2,y,z0,z1 in [('主卧百叶',7.22,9.54,9.96,1.20,2.48),('次卧百叶',5.85,7.28,1.87,1.12,2.25),('主卫百叶',8.11,8.71,3.14,1.12,2.27)]:
        n=math.ceil((z1-z0)/.085)
        for i in range(n):rect(name+'叶片',x1,x2,y-.026,y+.026,z0+i*(z1-z0)/n,z0+i*(z1-z0)/n+.008,'ivory','Curtains',bevel=.001)
    # White model p18: a lightweight headboard and small side work surface.
    for o in bpy.data.objects:
        if o.name=='极简床头木板':o.data.materials.clear();o.data.materials.append(api['M']['ivory'])
    for yy in (7.00,8.70):tube('主床金属床头柱',[(9.49,yy,.10),(9.49,yy,1.12)],.015,'steel','Furniture','master')
    tube('主床金属床头横杆',[(9.49,7.00,1.09),(9.49,8.70,1.09)],.015,'steel','Furniture','master')

def finish_layout(api):
    """Reconcile remaining furniture footprints to the revised CAD, not legacy offsets."""
    bpy=api['bpy']
    if '新版上侧独立书桌' in bpy.data.objects:return
    rect,tube,chair=[api[n] for n in ('rect','tube','chair')]
    for o in list(bpy.data.objects):
        if o.name.startswith(('双人工位长桌','长桌钢架','工位抽屉','日常餐椅')):bpy.data.objects.remove(o,do_unlink=True)
    for label,ya,yb in [('下侧',5.71,7.11),('上侧',7.21,8.61)]:
        rect('新版'+label+'独立书桌',3.61,4.31,ya,yb,.735,.775,'walnut','Furniture','study',.012)
        for yy in (ya+.10,yb-.10):tube('独立书桌钢架',[(3.70,yy,.02),(3.70,yy,.73),(4.23,yy,.73),(4.23,yy,.02)],.018,'steel','Furniture','study')
    # Measured table circle: x=1640..2540, y=2970..3870 mm. Four chairs;
    # the rectangle to the south is the kitchen island, not a fifth chair.
    for o in bpy.data.objects:
        if o.name.startswith(('圆餐桌','餐桌花瓶','花枝','小花','餐桌吊灯')):
            o.location.x-=.36;o.location.y-=.28
    for a in (0,math.pi/3,2*math.pi/3,math.pi):
        chair('日常餐椅',2.09+.66*math.cos(a),3.42+.66*math.sin(a),a-math.pi/2,False,'tan','dining')
