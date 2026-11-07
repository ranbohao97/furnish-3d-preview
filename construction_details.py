"""Finish the model's physical enclosures, without changing CAD footprints.

Idempotent on both a fresh build and saved scenes. Deliberate openings (shoe
slot, robot entrance, hanging vanities, open shelves) remain open.
"""
from mathutils import Vector


def finish_construction(api):
    bpy, rect = api['bpy'], api['rect']
    # Remove our previous pass and obsolete sliding leaves behind the new doors.
    for o in list(bpy.data.objects):
        if o.get('construction_detail') or o.name.startswith((
                '主卧床尾衣柜侧移门', '主卧长衣金属衣柜侧移门', '厨房转角封板')):
            bpy.data.objects.remove(o, do_unlink=True)

    def panel(name, b, room, material='kitchen_white', front=False):
        o = rect(name, *b, material, 'Storage', room, .001)
        o['construction_detail'] = True
        o['front_panel'] = front
        return o

    # Full-height end panels close both metal-system wardrobes. The hanging
    # hardware remains inside; end panels never disappear in interior mode.
    for name, b, face in [
        ('主卧床尾衣柜', (6.50, 7.05, 6.99, 9.30), 'x+'),
        ('主卧长衣金属衣柜', (6.38, 7.91, 5.31, 5.89), 'y+')]:
        x1, x2, y1, y2 = b
        if face == 'x+':
            for yy in (y1, y2-.018):
                panel(name+'端侧板', (x1+.025,x2,yy,yy+.018,.08,2.43), 'master')
            panel(name+'顶前收口', (x2,x2+.018,y1,y2,2.42,2.47), 'master')
            panel(name+'底前收口', (x2,x2+.018,y1,y2,.05,.08), 'master')
        else:
            for xx in (x1, x2-.018):
                panel(name+'端侧板', (xx,xx+.018,y1+.025,y2,.08,2.43), 'master')
            panel(name+'顶前收口', (x1,x2,y2,y2+.018,2.42,2.47), 'master')
            panel(name+'底前收口', (x1,x2,y2,y2+.018,.05,.08), 'master')
        panel(name+'内退底座', (x1+.04,x2-.06,y1+.04,y2-.04,.016,.05), 'master')

    # Close the ends of existing recessed plinths. Derive each return from its
    # actual back panel, so all four front orientations and fridge variants work.
    bpy.context.view_layer.update()
    for kick in list(bpy.data.objects):
        if '内退踢脚' not in kick.name:
            continue
        stem=kick.name.split('内退踢脚')[0]
        back=bpy.data.objects.get(stem+'背板')
        if back is None:
            continue
        def bounds(o):
            pts=[o.matrix_world @ Vector(p) for p in o.bound_box]
            return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]
        a,b=bounds(kick); c,d=bounds(back)
        axis=0 if b[0]-a[0] < b[1]-a[1] else 1
        span=1-axis
        rear=(c[axis]+d[axis])/2
        front=(a[axis]+b[axis])/2
        # Start just inside the rear carcass; meet the existing front plinth.
        r=rear+(.04 if front>rear else -.04)
        for u in (a[span],b[span]-.018):
            lo=a.copy();hi=b.copy()
            lo[axis],hi[axis]=sorted((r,front))
            lo[span],hi[span]=u,u+.018
            panel(stem+'踢脚端回板',(lo[0],hi[0],lo[1],hi[1],a[2],b[2]),kick.get('room','shared'))

    # Washer bay has two full-depth uprights and a true stacking adapter.
    # Back clearance is 10 mm; rear service access is conceptual, not a product spec.
    panel('洗烘设备分隔立板',(5.54,6.18,9.10,9.14,.016,2.47),'laundry')
    panel('洗烘设备右立板',(5.54,6.18,9.82,9.84,.016,2.47),'laundry')
    panel('洗烘右侧收口',(5.54,5.56,9.84,9.96,.03,2.47),'laundry')
    panel('洗烘上柜顶封',(5.54,5.56,9.14,9.82,2.40,2.47),'laundry')
    panel('洗烘上柜底封',(5.54,5.56,9.14,9.82,1.76,1.78),'laundry')
    panel('洗烘叠放连接托架',(5.56,6.16,9.17,9.77,.84,.89),'laundry','white')
    old=bpy.data.objects.get('洗衣机上层板')
    if old:bpy.data.objects.remove(old,do_unlink=True)
    panel('洗衣机上层板',(5.54,6.18,9.14,9.82,1.73,1.76),'laundry')
    for name in ('洗衣机','烘干机'):
        o=bpy.data.objects.get(name)
        if o:
            # The old 620 mm body protruded 10 mm through the rear board.
            o.location.x=5.86
    # Solid supports to the recessed machine shelf, inside its side uprights.
    for yy in (9.14,9.80):
        panel('洗烘层板托条',(5.57,6.17,yy,yy+.02,1.70,1.73),'laundry','steel')

    # Peninsula: actual hollow corner, fully enclosed dining end and plinths.
    for suffix,b in [
        ('背板',(2.10,2.118,.84,1.17,.10,.85)),
        ('侧板',(2.118,2.39,.84,.858,.10,.85)),
        ('底板',(2.118,2.372,.858,1.152,.10,.118)),
        ('另一侧板',(2.118,2.39,1.152,1.17,.10,.85)),
        ('检修面板',(2.372,2.39,.858,1.152,.118,.85))]:
        panel('厨房盲角'+suffix,b,'kitchen',front=suffix=='检修面板')
    panel('半岛餐厅端封板',(1.79,1.81,1.17,2.97,.10,.85),'kitchen')
    # Replace the overlapping old dining back panel with the continuous end.
    old=bpy.data.objects.get('水槽柜餐厅侧背板')
    if old:bpy.data.objects.remove(old,do_unlink=True)
    for suffix,b in [
        ('操作侧',(2.30,2.318,1.17,2.93,.016,.10)),
        ('餐厅侧',(1.84,1.858,1.17,2.93,.016,.10)),
        ('餐桌端',(1.84,2.318,2.912,2.93,.016,.10)),
        ('入户端',(1.84,2.318,1.17,1.188,.016,.10)),
        ('转角',(2.30,2.318,.858,1.17,.016,.10))]:
        panel('半岛踢脚'+suffix,b,'kitchen')
    # Close the small counter bridging in front of the shafts with a removable
    # front and structural ends; do not fill the pipe service cavity.
    panel('管井前地柜检修面',(3.30,3.35,.84,.858,.10,.85),'kitchen',front=True)
    panel('管井前地柜前板',(3.35,3.97,.84,.858,.10,.85),'kitchen',front=True)
    for xx in (3.30,3.952):
        panel('管井前地柜端板',(xx,xx+.018,.62,.84,.10,.85),'kitchen')
    panel('管井前地柜底板',(3.318,3.952,.62,.84,.10,.118),'kitchen')
    panel('管井前地柜踢脚',(3.30,3.97,.76,.778,.016,.10),'kitchen')

    # Shelf stacks should meet, objects should rest on their actual surfaces.
    panel('餐边柜层间收口',(.31,.742,4.47,6.07,.52,.54),'dining')
    for o in bpy.data.objects:
        if o.name.startswith('餐边备用杯'):o.location.z=.618
        if o.name.startswith('储物间收纳箱'):
            # Keep each box 0 mm above its shelf top instead of hovering 20 mm.
            if not o.get('supported_surface_fixed'):
                o.location.z-=.02;o['supported_surface_fixed']=True
        if o.name.startswith(('几何画木框','几何画底纸','画作红圆','画作蓝方')):
            if not o.get('shelf_collision_fixed'):
                o.location.z+=.58;o['shelf_collision_fixed']=True
    # Concealed brackets now represented where floating shelves meet the wall.
    for zz in (1.35,1.74):
        for yy in (4.70,5.83):
            panel('餐边层板墙托',(.312,.47,yy,yy+.025,zz-.025,zz),'dining','steel')
