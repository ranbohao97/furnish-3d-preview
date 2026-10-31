"""Run in Blender 4.5: blender -b --python build_model.py"""
import bpy, math, random, json, sys, subprocess, os
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT=Path(__file__).resolve().parent
OUTPUT=Path(os.environ.get('MODEL_OUTPUT_DIR',ROOT/'generated'));OUTPUT.mkdir(parents=True,exist_ok=True)
D=json.loads((ROOT/'model-data.json').read_text())
random.seed(603)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name!='Collection' and not c.objects: bpy.data.collections.remove(c)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='METERS'
H=D['finished_height_m'];CUT=1.10
COL={}; META=[]; WALLS=[]
def group(name):
    if name not in COL:
        c=bpy.data.collections.new(name);scene.collection.children.link(c);COL[name]=c
    return COL[name]
def tag(o,name,cat='Furniture',room='shared',source='style interpretation'):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    group(cat).objects.link(o)
    o['category']=cat;o['room']=room;o['source']=source
    return o
def srgb(v): return v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4
def mat(name,hex,rough=.55,metal=0,texture=None):
    m=bpy.data.materials.new(name);m.use_nodes=True
    rgb=tuple(int(hex[i:i+2],16)/255 for i in (0,2,4));m.diffuse_color=(*rgb,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*map(srgb,rgb),1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if texture:
        t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/texture));t.image.pack()
        m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
    return m
M={
 'fridge_white':mat('冰箱富士白玻璃配色','F1F3F0',.20,.03),
 'wall':mat('暖白矿物涂料','E9E4D7',.82), 'ceiling':mat('顶面暖白','F3EEE4',.85),
 'walnut':mat('柚木色木饰面','965B30',.46,texture='walnut.jpg'), 'oak':mat('温润橡木地板','B38959',.6,texture='oak.jpg'),
 'steel':mat('拉丝不锈钢','B9C1BF',.3,.88),'chrome':mat('抛光管状金属','D2D8D7',.17,.96),
 'black':mat('石墨黑金属','262925',.37,.38),'leather':mat('炭黑皮革','30302C',.45),
 'ivory':mat('米白织物','D9D0BA',.94),'white':mat('暖白陶瓷','F1EDE3',.22),
 'green':mat('橄榄绿织物','667359',.9),'red':mat('砖红点缀','9E3927',.4),
 'blue':mat('客卫钴蓝','335983',.36),'tile':mat('米白小方砖','E1DCD0',.3),
 'grout':mat('暖灰砖缝','A9A49A',.9),'screen':mat('电视深色屏幕','152322',.15,.25),
 'mirror':mat('镜面','D5DDD9',.04,1),'tan':mat('藤编与棉麻','BEA16C',.8),
 'leaf':mat('叶片绿','3C6240',.7),'soil':mat('花盆土壤','30291F',1),
 'rug':mat('亚麻地毯','C9BDA1',1),'floorbase':mat('模型基座','DDD7C9',.8),
 'orange':mat('琥珀暖色','D3933B',.5),'book':mat('书籍米白','E5DBBA',.9)
}
glass=mat('透明玻璃','C7D9D5',.08)
p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=.86;p.inputs['IOR'].default_value=1.45
glass.diffuse_color=(.62,.78,.74,.22);p.inputs['Alpha'].default_value=.22;glass.surface_render_method='DITHERED';M['glass']=glass
lightmat=mat('乳白发光灯罩','FFF1CC',.5)
p=lightmat.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.72,.38,1);p.inputs['Emission Strength'].default_value=.7;M['lamp']=lightmat

def finish(o,name,m,cat='Furniture',room='shared',bevel=0,source='style interpretation'):
    tag(o,name,cat,room,source);o.data.materials.append(M[m] if isinstance(m,str) else m)
    if bevel:
        mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bevel;mod.segments=3
        mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o
def box(name,loc,size,m='wall',cat='Furniture',room='shared',bevel=.006,rot=0,source='style interpretation'):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.rotation_euler.z=rot
    return finish(o,name,m,cat,room,bevel,source)
def rect(name,x1,x2,y1,y2,z1,z2,m='wall',cat='Furniture',room='shared',bevel=.004,source='CAD plan footprint / assumed elevation'):
    return box(name,((x1+x2)/2,(y1+y2)/2,(z1+z2)/2),(x2-x1,y2-y1,z2-z1),m,cat,room,bevel,source=source)
def prism(name,pts,z1,z2,m='wall',cat='Architecture',room='shared'):
    clean=[]
    for v in pts:
        q=(float(v[0]),float(v[1]))
        if not clean or Vector(q)-Vector(clean[-1])!=Vector((0,0)):clean.append(q)
    if clean[0]==clean[-1]:clean.pop()
    if sum(clean[i][0]*clean[(i+1)%len(clean)][1]-clean[(i+1)%len(clean)][0]*clean[i][1]for i in range(len(clean)))<0:clean.reverse()
    n=len(clean);verts=[(x,y,z1)for x,y in clean]+[(x,y,z2)for x,y in clean]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);group(cat).objects.link(o)
    finish(o,name,m,cat,room,0,'CAD model-space coordinates')
    # Planar UVs for texture export, preserved in GLB.
    uv=mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(v.y/.15,v.x/1.2)
    return o
def cyl(name,loc,r,depth,m='chrome',cat='Furniture',room='shared',vertices=32,rot=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc)
    o=bpy.context.object
    if rot:o.rotation_euler=rot
    finish(o,name,m,cat,room,.003)
    for p in o.data.polygons:p.use_smooth=True
    return o
def sphere(name,loc,scale,m='ivory',cat='Furniture',room='shared'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=loc)
    o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,name,m,cat,room)
    for p in o.data.polygons:p.use_smooth=True
    return o
def tube(name,pts,r=.012,m='chrome',cat='Furniture',room='shared'):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=2;c.bevel_depth=r;c.bevel_resolution=3
    s=c.splines.new('POLY');s.points.add(len(pts)-1)
    for p,co in zip(s.points,pts):p.co=(*co,1)
    o=bpy.data.objects.new(name,c);group(cat).objects.link(o);o.data.materials.append(M[m]);tag(o,name,cat,room)
    return o
def wall(name,x1,x2,y1,y2,height=H,z=0,m='wall'):
    if z<CUT:WALLS.append({'name':name,'p':[(x1,y1),(x2,y1),(x2,y2),(x1,y2)],'z1':z,'z2':min(CUT,height)})
    if height>CUT:WALLS.append({'name':name,'p':[(x1,y1),(x2,y1),(x2,y2),(x1,y2)],'z1':max(CUT,z),'z2':height})
def wallpoly(name,pts):
    WALLS.append({'name':name,'p':pts,'z1':0,'z2':CUT})
    WALLS.append({'name':name,'p':pts,'z1':CUT,'z2':H})
def merge_walls():
    inp=ROOT/'wall-footprints.json';out=ROOT/'merged-wall-slabs.json'
    inp.write_text(json.dumps(WALLS,ensure_ascii=False))
    py=Path(os.environ.get('MODEL_PYTHON','python3'))
    subprocess.run([str(py),str(ROOT/'union_walls.py'),str(inp),str(out)],check=True)
    for i,s in enumerate(json.loads(out.read_text())):
        vs=[];fs=[];lo=s['z1'];hi=s['z2']
        for tri in s['triangles']:
            area=sum(tri[k][0]*tri[(k+1)%3][1]-tri[(k+1)%3][0]*tri[k][1]for k in range(3))
            if area<0:tri.reverse()
            n=len(vs);vs.extend([(x,y,lo)for x,y in tri]);fs.append((n+2,n+1,n))
            n=len(vs);vs.extend([(x,y,hi)for x,y in tri]);fs.append((n,n+1,n+2))
        for ring in s['rings']:
            for a,b in zip(ring,ring[1:]+ring[:1]):
                n=len(vs);vs.extend([(a[0],a[1],lo),(b[0],b[1],lo),(b[0],b[1],hi),(a[0],a[1],hi)]);fs.append((n,n+1,n+2,n+3))
        mesh=bpy.data.meshes.new('Unified walls');mesh.from_pydata(vs,[],fs);mesh.update()
        o=bpy.data.objects.new('CAD墙体_%02d'%i,mesh);group('WallsLow'if hi<=CUT+.001 else 'WallsUpper').objects.link(o)
        finish(o,o.name,'wall','WallsLow'if hi<=CUT+.001 else 'WallsUpper',source='Union of current CAD wall footprints')

# Measured shell and floor. Interior elevations are from a provisional finished
# floor 100mm above CAD raw slab. All horizontal positions remain CAD based.
prism('完整户型基座',D['footprint'],-.20,-.035,'floorbase','Base')
prism('地面基层',D['footprint'],-.035,0,'grout','Floor')
for i,p in enumerate(D['wood_planks']):
    prism('木地板_%04d'%i,p['p'],0,.014,'oak','Floor')
# Structural solids are taken directly from DWG hatches, excluding the entry arrow.
geom=json.loads((ROOT/'current-geometry.json').read_text())
for i,h in enumerate(geom['hatches']):
    if h['pattern']!='SOLID':continue
    for j,pts in enumerate(h['paths']):
        if len(pts)<3:continue
        if i==len(geom['hatches'])-1:continue
        wallpoly('原图实心墙_%s_%s'%(i,j),[(x/1000,y/1000)for x,y in pts])
# Continuous envelope with real openings.
wall('西外墙',.07,.31,.91,8.7)
wall('南阳台左立柱',.76,1.00,8.41,8.70)
wall('南阳台左墙上段',.76,1.00,9.34,10.23)
wall('左侧高窗窗台',.76,1.00,8.70,9.34,1.23)
wall('左侧高窗窗楣',.76,1.00,8.70,9.34,H,2.50)
wall('南窗左边框',.76,1.00,9.99,10.23)
wall('南窗中柱',5.56,5.75,9.99,10.23)
wall('洗烘侧墙',6.21,6.33,9.49,10.23)
wall('主卧飘窗左柱',6.96,7.20,9.49,10.23)
wall('东外墙',9.56,9.80,2.87,10.23)
wall('主卧南梁',7.20,9.56,9.30,9.49,H,2.28)
wall('主卧飘窗下墙',7.20,9.56,9.99,10.23,.52)
wall('主卧飘窗窗楣',7.20,9.56,9.99,10.23,H,2.50)
wall('阳台低梁',.76,6.26,8.41,8.70,H,1.96)
wall('主卧衣柜背墙',6.26,6.50,6.99,9.30)
wall('主卧门上过梁',5.54,5.68,5.89,6.99,H,2.20)
wall('主卧衣柜背隔墙',5.54,7.91,5.17,5.29)
wall('主卫门左墙',8.06,8.10,5.77,5.89)
wall('主卫门右墙',8.90,9.56,5.77,5.89)
wall('主卫门过梁',8.10,8.90,5.77,5.89,H,2.16)
wall('主卫西墙',7.91,8.06,4.20,5.77)
wall('主卫南侧窗台',8.06,8.71,2.87,3.11,.87)
wall('主卫南侧墙',8.71,9.56,2.87,3.11)
wall('主卫南侧窗楣',8.06,8.71,2.87,3.11,H,2.29)
wall('次卧西墙',5.22,5.34,1.83,3.92)
wall('次卧门左墙',5.34,5.41,3.80,3.92)
wall('次卧门右墙',6.24,6.50,3.80,3.92)
wall('次卧门楣',5.41,6.24,3.80,3.92,H,2.20)
wall('储物间下隔墙',6.38,7.48,4.20,4.32)
wall('储物间左墙脚',6.38,6.50,3.92,4.32)
wall('次卧窗左墙',5.22,5.85,1.59,1.83)
wall('次卧窗台',5.85,7.28,1.59,1.83,.84)
wall('次卧窗楣',5.85,7.28,1.59,1.83,H,2.27)
wall('次卫西墙',3.47,3.71,2.70,4.60)
wall('次卫门左墙',3.71,4.40,3.80,3.92)
wall('次卫门右墙',5.18,5.22,3.80,3.92)
wall('次卫门楣',4.40,5.18,3.80,3.92,H,2.16)
wall('次卫南窗左墙',4.21,4.41,1.59,1.83)
wall('次卫南窗台',4.41,5.04,1.59,1.83,.87)
wall('次卫南窗右墙',5.04,5.22,1.59,1.83)
wall('次卫南窗楣',4.41,5.04,1.59,1.83,H,2.30)
wall('厨房东下墙',3.97,4.21,.24,.67)
wall('厨房窗台',3.97,4.21,.67,1.50,.81)
wall('厨房窗楣',3.97,4.21,.67,1.50,H,2.23)
wall('厨房东上墙',3.97,4.21,1.50,2.46)
wall('入口左门墩',.07,.71,.91,1.15)
wall('入口右门墩',1.79,2.10,.91,1.15)
wall('入口门楣',.71,1.79,.91,1.15,H,2.06)
wall('厨房北墙',1.87,4.21,0,.24)
wall('厨房左返回墙',1.87,2.10,.24,.91)
merge_walls()
# Ceiling is separately selectable in the viewer.
prism('全屋顶面',D['footprint'],H,H+.04,'ceiling','Ceiling')
for r,b in [('主卫',(8.06,9.56,3.11,5.77)),('次卫',(3.71,5.22,1.83,3.80))]:
    rect(r+'吊顶',*b,2.34,2.39,'ceiling','Ceiling',r)
# Bay seat and external equipment platforms are distinct from living floors.
rect('主卧飘窗台',7.20,9.56,9.30,9.99,0,.52,'wall','Furniture','master',.005)
rect('飘窗木台面',7.20,9.56,9.30,9.99,.52,.55,'walnut','Furniture','master',.008)
rect('厨房外设备平台',4.21,5.04,0,1.59,-.12,-.09,'grout','Exterior')
rect('南侧设备平台',6.33,6.96,9.49,10.23,-.12,-.09,'grout','Exterior')

def window(name,a,b,sill,top,panels=2):
    ax,ay=a;bx,by=b;dx=bx-ax;dy=by-ay;L=math.hypot(dx,dy);angle=math.atan2(dy,dx)
    for z in (sill,top):box(name+'横框',((ax+bx)/2,(ay+by)/2,z),(L,.045,.045),'black','Windows',bevel=.003,rot=angle)
    for i in range(panels+1):
        u=i/panels;c=(ax+dx*u,ay+dy*u,(sill+top)/2)
        box(name+'立框',c,(.04,.06,top-sill),'black','Windows',bevel=.002,rot=angle)
    for i in range(panels):
        u=(i+.5)/panels
        box(name+'玻璃', (ax+dx*u,ay+dy*u,(sill+top)/2),(L/panels-.04,.012,top-sill-.04),'glass','Windows',bevel=0,rot=angle)
window('南向封窗',(1,10.11),(5.56,10.11),.03,2.43,4)
window('洗烘区窗',(5.75,10.11),(6.21,10.11),.03,2.43,1)
window('阳台侧高窗',(.88,8.70),(.88,9.34),1.23,2.50,1)
window('主卧窗',(7.22,10.11),(9.54,10.11),.52,2.50,2)
window('次卧窗',(5.85,1.71),(7.28,1.71),.84,2.27,2)
window('次卫窗',(4.41,1.71),(5.04,1.71),.87,2.30,1)
window('主卫窗',(8.11,2.99),(8.71,2.99),.87,2.29,1)
window('厨房窗',(4.09,.67),(4.09,1.50),.81,2.23,1)

def curtain(name,a,b,z0=.05,z1=2.56,material='ivory'):
    ax,ay=a;bx,by=b;dx=bx-ax;dy=by-ay;L=math.hypot(dx,dy);nx=-dy/L;ny=dx/L
    seg=max(24,int(L*85));verts=[]
    for zz in [z0,z1]:
        for i in range(seg+1):
            t=i/seg;wave=.035*math.sin(t*L*2*math.pi/.10)
            verts.append((ax+dx*t+nx*wave,ay+dy*t+ny*wave,zz))
    faces=[(i,i+1,i+1+seg+1,i+seg+1)for i in range(seg)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);group('Curtains').objects.link(o);finish(o,name,material,'Curtains')
    for p in mesh.polygons:p.use_smooth=True
    sol=o.modifiers.new('布料厚度','SOLIDIFY');sol.thickness=.002
    return o
curtain('南窗纱帘左',(1.04,9.91),(1.75,9.91))
curtain('南窗纱帘右',(5.02,9.91),(5.48,9.91))
curtain('主卧遮光帘左',(7.24,9.88),(7.65,9.88),.56,2.56,'green')
curtain('主卧遮光帘右',(9.08,9.88),(9.48,9.88),.56,2.56,'green')
curtain('次卧窗帘左',(5.87,1.98),(6.13,1.98),.87,2.50)
curtain('次卧窗帘右',(7.0,1.98),(7.25,1.98),.87,2.50)

def cabinet(name,x1,x2,y1,y2,height,face='y+',material='walnut',room='shared',base=.10,drawers=False):
    # Actual 18 mm carcass. Front panels can be hidden in the viewer to inspect storage.
    width=(y2-y1) if face[0]=='x' else (x2-x1)
    depth=(x2-x1) if face[0]=='x' else (y2-y1)
    def point(u,v,z):
        if face=='x+':return (x1+v,y1+u,z)
        if face=='x-':return (x2-v,y1+u,z)
        if face=='y+':return (x1+u,y1+v,z)
        return (x1+u,y2-v,z)
    def part(label,u1,u2,v1,v2,z1,z2,ma=material,front=False):
        q=point(u1,v1,z1);r=point(u2,v2,z2)
        o=rect(name+label,min(q[0],r[0]),max(q[0],r[0]),min(q[1],r[1]),max(q[1],r[1]),z1,z2,ma,'Storage',room,.002)
        if front:o['front_panel']=True
        return o
    t=.018
    part('背板',0,width,0,t,base,height)
    for u in (0,width-t):part('侧板',u,u+t,t,depth,base,height)
    for z in (base,height-t):part('横板',t,width-t,t,depth,z,z+t)
    # Recessed toe space; doors do not run to the floor.
    if base<.20:part('内退踢脚',.04,width-.04,depth-.09,depth-.075,.02,base)
    n=max(1,round(width/.48) if drawers else math.ceil(width/.48));bay=width/n
    for i in range(n):
        lo=i*bay+t;hi=(i+1)*bay-t
        if i:part('竖隔',i*bay-t/2,i*bay+t/2,t,depth,base,height)
        if drawers:
            levels=3 if height-base>.5 else 2
            dh=(height-base-t)/levels
            for j in range(levels):
                z=base+t+j*dh
                part('抽屉底',lo+.008,hi-.008,t+.02,depth-.02,z,z+.012,'ivory')
                for u in (lo+.008,hi-.02):part('抽屉侧',u,u+.012,t+.02,depth-.02,z+.012,z+dh-.06,'ivory')
                part('抽屉后挡',lo+.008,hi-.008,t+.02,t+.032,z+.012,z+dh-.06,'ivory')
                part('抽屉面',i*bay+.003,(i+1)*bay-.003,depth,depth+.018,z-.012,z+dh-.018,front=True)
                tube(name+'抽屉拉手',[point((lo+hi)/2-.09,depth+.039,z+dh-.065),point((lo+hi)/2+.09,depth+.039,z+dh-.065)],.007,room=room)
        else:
            for z in [base+.24+k*.28 for k in range(int((height-base-.1)/.28))]:
                if z<height-.10:part('可调层板',lo,hi,t,depth-.035,z,z+t,'ivory')
            part('柜门',i*bay+.003,(i+1)*bay-.003,depth,depth+.018,base+.006,height-.006,front=True)
            hz=max(base+.12,min(height-.12,1.10))
            tube(name+'柜门拉手',[point((lo+hi)/2-.075,depth+.039,hz),point((lo+hi)/2+.075,depth+.039,hz)],.007,room=room)
    return
def door(name,hinge,width,angle,material='walnut',height=2.15,room='shared'):
    x,y=hinge;dx=math.cos(angle);dy=math.sin(angle)
    box(name,(x+dx*width/2,y+dy*width/2,height/2),(width,.038,height),material,'Doors',room,.006,angle)
    tube(name+'拉手',[(x+dx*(width-.14)-dy*.035,y+dy*(width-.14)+dx*.035,.98),(x+dx*(width-.03)-dy*.035,y+dy*(width-.03)+dx*.035,.98)],.009,room=room)
door('入户门',(.71,1.02),1.06,math.radians(-65),'walnut',2.04,'entry')
door('次卧门',(5.41,3.86),.80,math.radians(-80),'walnut',2.18,'guest')
door('主卫门',(8.10,5.83),.78,math.radians(-70),'walnut',2.14,'masterbath')
# compact folded leaves match the plan's bifold swing
door('客卫折叠门A',(5.18,3.86),.39,math.radians(230),'blue',2.14,'guestbath')
door('客卫折叠门B',(4.93,3.56),.39,math.radians(130),'blue',2.14,'guestbath')
door('主卧折叠门下叶',(5.61,5.94),.50,math.radians(8),'walnut',2.18,'master')
door('主卧折叠门上叶',(5.61,6.94),.50,math.radians(-8),'walnut',2.18,'master')

# Continuous 3230 mm west-wall run: 2470 mm entry + 760 mm dining.
# 2400 mm cabinet includes a 20 mm scribe; local ceiling drops 320 mm above.
ENTRY_ZONES=json.loads((ROOT/'entry-storage.json').read_text())
def entry_part(name,x1,x2,y1,y2,z1,z2,material='walnut',room='entry',front=False):
    o=rect(name,x1,x2,y1,y2,z1,z2,material,'Storage',room,.002,'Owner revision 2026-10-31 / concept dimensions')
    if front:o['front_panel']=True
    return o
def entry_shelf(name,a,b,z,room='entry'):
    return entry_part(name+'层板',.338,.705,a+.018,b-.018,z,z+.018,'ivory',room)
def entry_front(name,a,b,z0,z1,room='entry',sliding=False):
    # Two narrow leaves; dining lower storage uses bypass doors to avoid swing.
    for i in range(2):
        lo=a+i*(b-a)/2+.003;hi=a+(i+1)*(b-a)/2-.003
        xx=.740+(.020*i if sliding else 0)
        o=entry_part(name+('移门' if sliding else '柜门'),xx,xx+.018,lo,hi,z0+.006,z1-.006,room=room,front=True)
        o['opening']='sliding' if sliding else 'hinged';o['zone']=name
        # Handle stays within the existing 786 mm front envelope.
        yy=(lo+hi)/2;zz=max(z0+.10,min(z1-.10,1.12))
        if sliding:
            entry_part(name+'柜门拉手',xx+.018,xx+.025,yy-.045,yy+.045,zz-.012,zz+.012,'black',room)
        else:tube(name+'柜门拉手',[(.779,yy-.065,zz),(.779,yy+.065,zz)],.007,'chrome','Storage',room)
for zone in ENTRY_ZONES['modules']:
    name=zone['name'];a,b=[v/1000 for v in zone['y_mm']];room=zone['room']
    for yy in (a,b-.018):entry_part(name+'通顶侧板',.338,.740,yy,yy+.018,.08,2.38,room=room)
    entry_part(name+'封闭背板',.320,.338,a,b,.08,2.38,room=room)
    for zz in (.08,1.982,2.362):entry_part(name+'固定横板',.338,.740,a+.018,b-.018,zz,zz+.018,room=room)
    entry_part(name+'内退踢脚',.640,.658,a+.018,b-.018,.02,.08,room=room)
    entry_part(name+'到顶收口',.320,.758,a,b,2.38,2.40,room=room)
    entry_front(name+'顶层低频收纳',a,b,2.00,2.38,room)
    # Separate closed boxes for seasonal shoes/bags, all above normal reach.
    box(name+'顶层收纳盒',(.51,(a+b)/2,2.18),(.30,b-a-.10,.28),'tan','Storage',room,.012)
# A: frequently worn shoes, bottom open slot; shoes lie perpendicular to front.
a,b=1.18,1.78
for z in (.25,.48,.71,.94,1.17,1.40,1.63,1.86):entry_shelf('玄关A鞋履',a,b,z)
entry_front('玄关A日常鞋下区',a,b,.25,1.05);entry_front('玄关A日常鞋上区',a,b,1.05,1.98)
for yy in (1.34,1.60):
 for dy in (-.046,.046):
  for z in (.14,.32,.55,1.24,1.70):sphere('玄关A鞋履',(.52,yy+dy,z),(.145,.04,.045),'tan','Storage','entry')
# B: keys, small bags and mirror niche at standing reach, shoes below.
a,b=1.78,2.38
for z in (.31,.55,.79,.95,1.532,1.82):entry_shelf('玄关B归家',a,b,z)
entry_front('玄关B鞋履下柜',a,b,.08,.95);entry_front('玄关B随身物品上柜',a,b,1.55,1.98)
entry_part('玄关B随手凹位台面',.338,.758,a+.018,b-.018,.95,.97,'steel')
rect('玄关B镜面背板',.340,.350,1.84,2.32,1.00,1.48,'mirror','Decor','entry',.002)
rect('玄关B钥匙托盘',.48,.68,1.95,2.18,.97,.986,'steel','Decor','entry',.01)
box('玄关B钥匙碗',(.57,2.07,1.01),(.12,.12,.04),'blue','Decor','entry',.015)
for yy in (1.87,2.28):tube('玄关B挂钩',[(.355,yy,1.38),(.405,yy,1.38),(.405,yy,1.41)],.007,'chrome','Storage','entry')
entry_part('玄关B凹位灯带',.68,.70,1.82,2.34,1.518,1.527,'lamp')
# C: 420 mm main bay for boots + adjustable shoes, 164 mm dry umbrella bay.
a,b=2.38,3.00
entry_part('玄关C雨伞独立竖隔',.338,.71,2.80,2.818,.098,1.18,'ivory')
for z in (.63,.88):entry_shelf('玄关C长靴鞋履',a,2.80,z)
for z in (1.16,1.47,1.80):entry_shelf('玄关C鞋履备品',a,b,z)
entry_front('玄关C长靴雨伞区',a,b,.08,1.16);entry_front('玄关C换季鞋区',a,b,1.16,1.98)
entry_part('玄关C雨伞沥水托盘',.37,.68,2.84,2.96,.10,.125,'steel')
for yy in (2.48,2.64):
    box('玄关C长靴筒',(.49,yy,.34),(.12,.10,.38),'black','Storage','entry',.018)
    box('玄关C长靴鞋头',(.56,yy,.16),(.27,.10,.10),'black','Storage','entry',.025)
for yy in (2.87,2.93):
    cyl('玄关C收拢雨伞',(.51,yy,.53),.018,.78,'green','Storage','entry')
    tube('玄关C雨伞弯柄',[(.51,yy,.92),(.51,yy,1.00),(.56,yy,1.00),(.56,yy,.96)],.007,'black','Storage','entry')
# D: bags and boxed household supplies; no impractical sideways clothes rail.
a,b=3.00,3.65
for z in (.55,1.02,1.49):entry_shelf('玄关D通勤备品',a,b,z)
entry_front('玄关D通勤包下区',a,b,.08,1.02);entry_front('玄关D日用备品上区',a,b,1.02,1.98)
for yy,z in [(3.18,.30),(3.46,.77)]:
    box('玄关D通勤包',(.51,yy,z),(.27,.23,.35),'green','Storage','entry',.025)
    tube('玄关D包提手',[(.51,yy-.06,z+.17),(.51,yy-.06,z+.24),(.51,yy+.06,z+.24),(.51,yy+.06,z+.17)],.009,'black','Storage','entry')
for z in (1.18,1.65):box('玄关D日用备品盒',(.51,3.31,z),(.30,.48,.24),'ivory','Storage','entry',.008)
# E: a small food-only zone; solid full-height panels separate it from shoes.
a,b=3.65,4.41
for z in (.35,.63,1.532,1.82):entry_shelf('餐边E独立收纳',a,b,z,'dining')
entry_front('餐边E下部餐具移门',a,b,.08,.63,'dining',sliding=True)
# One shallow cutlery drawer: actual tray and a removable front.
entry_part('餐边E餐具抽屉底',.37,.70,a+.045,b-.045,.66,.675,'ivory','dining')
for yy in (a+.045,b-.057):entry_part('餐边E餐具抽屉侧',.37,.70,yy,yy+.012,.675,.83,'ivory','dining')
entry_part('餐边E餐具抽屉后挡',.37,.382,a+.045,b-.045,.675,.83,'ivory','dining')
entry_part('餐边E餐具抽屉面',.74,.758,a+.003,b-.003,.64,.875,room='dining',front=True)
tube('餐边E餐具抽屉拉手',[(.779,3.94,.81),(.779,4.12,.81)],.007,'chrome','Storage','dining')
entry_part('餐边E不锈钢台面',.338,.758,a+.018,b-.018,.88,.90,'steel','dining')
entry_front('餐边E杯碟上柜',a,b,1.55,1.98,'dining')
entry_part('餐边E凹位灯带',.68,.70,3.70,4.36,1.518,1.527,'lamp','dining')
# Everyday serving objects stay entirely within the 420 mm deep niche.
rect('餐边E托盘',.40,.69,3.78,4.22,.90,.918,'walnut','Decor','dining',.012)
for yy in (3.87,4.06):
    cyl('餐边E水杯',(.53,yy,.973),.038,.11,'white','Decor','dining')
    cyl('餐边E杯口',(.53,yy,1.030),.031,.004,'grout','Decor','dining')
for z in (.374,.386,.398):cyl('餐边E餐盘',(.52,4.00,z),.13,.012,'white','Storage','dining')
for yy in (3.84,4.11):cyl('餐边E备用杯',(.51,yy,1.90),.045,.12,'white','Storage','dining')
# Local plasterboard bulkhead joins the 2400 mm cabinet to the assumed 2720 mm ceiling.
rect('玄关柜顶局部吊顶',.31,.82,1.18,4.41,2.40,H,'ceiling','Ceiling','entry')
cabinet('客厅杂物低柜',.32,.67,4.50,5.80,.58,'x+','walnut','living',drawers=True)
# Sofa faces west, with two full-sized seats, armrests, piping and cushions.
box('沙发底座',(2.94,7.06,.28),(.89,2.43,.25),'black','Furniture','living',.055)
box('沙发靠背',(3.31,7.06,.65),(.19,2.45,.60),'leather','Furniture','living',.085)
for yy in (5.91,8.21):box('沙发扶手',(2.94,yy,.55),(.93,.17,.50),'leather','Furniture','living',.07)
for yy in (6.49,7.62):
    box('沙发坐垫',(2.88,yy,.48),(.78,1.08,.21),'leather','Furniture','living',.085)
    o=box('沙发软靠垫',(3.18,yy,.79),(.23,1.03,.52),'leather','Furniture','living',.09);o.rotation_euler.y=-.12
for xx in (2.60,3.22):
    for yy in (6.03,8.08):cyl('沙发金属脚',(xx,yy,.10),.023,.20,'chrome',room='living')
for yy,ma in [(6.25,'tan'),(7.85,'ivory')]:
    o=box('沙发抱枕',(2.91,yy,.73),(.20,.40,.38),ma,'Furniture','living',.085);o.rotation_euler.y=-.25
rect('客厅地毯',.70,2.72,5.99,8.20,.017,.025,'rug','Furniture','living',.015)
for y in (6.05,8.14):rect('地毯深色边线',.76,2.66,y,y+.018,.026,.028,'black','Furniture','living',0)
# 65-inch 16:9 active screen; frame and freestanding hardware are conceptual.
TV_DIAGONAL=65*.0254;TV_WIDTH=TV_DIAGONAL*16/math.sqrt(16**2+9**2);TV_HEIGHT=TV_DIAGONAL*9/math.sqrt(16**2+9**2)
box('65英寸电视机身',(.59,7.06,1.12),(.045,TV_WIDTH+.020,TV_HEIGHT+.020),'black','Furniture','living',.008)
box('65英寸电视屏幕',(.615,7.06,1.12),(.006,TV_WIDTH,TV_HEIGHT),'screen','Furniture','living',.002)
# Low weighted steel plate, central cable column and rear mounting rails.
rect('电视落地支架底座',.33,.87,6.65,7.47,.025,.050,'black','Furniture','living',.018)
rect('电视落地支架立柱',.485,.545,7.02,7.10,.050,1.28,'black','Furniture','living',.008)
for zz in (1.02,1.22):rect('电视落地支架横梁',.540,.574,6.77,7.35,zz,zz+.03,'black','Furniture','living',.004)
for yy in (6.88,7.22):rect('电视落地支架背挂臂',.55,.574,yy,yy+.035,.94,1.31,'black','Furniture','living',.003)
# Retain the soundbar on a small support attached to the stand, not floating.
rect('电视支架回音壁托盘',.54,.69,6.55,7.57,.595,.6075,'black','Furniture','living',.004)
for yy in (6.84,7.28):tube('电视支架托盘撑',[(.52,7.06,.50),(.61,yy,.595)],.012,'black','Furniture','living')
box('回音壁',(.625,7.06,.640),(.09,.95,.065),'black','Furniture','living',.014)
tube('电视支架背部理线',[(.568,7.08,1.12),(.474,7.08,1.05),(.474,7.08,.08),(.34,7.08,.06)],.006,'black','Furniture','living')
# Double desk and perforated-height divider behind the sofa.
# CAD yellow footprint is a decorative partition, not a cabinet.
rect('装饰隔断墙下段',3.47,3.59,6.99,8.70,0,.92,'wall','Furniture','study',.008)
rect('装饰隔断墙上段',3.47,3.59,6.99,8.70,2.10,2.40,'wall','Furniture','study',.008)
for ya,yb in [(6.99,7.49),(8.19,8.70)]:rect('装饰隔断墙侧段',3.47,3.59,ya,yb,.92,2.10,'wall','Furniture','study',.008)
rect('装饰隔断透光玻璃',3.525,3.535,7.49,8.19,.94,2.08,'glass','Furniture','study')
for yy in (7.49,8.17):rect('隔断木饰收口',3.46,3.60,yy,yy+.02,.92,2.10,'walnut','Furniture','study')
rect('双人工位长桌',3.61,4.25,5.72,8.60,.735,.775,'walnut','Furniture','study',.012)
for yy in (5.84,8.47):
    tube('长桌钢架',[(3.73,yy,.06),(3.73,yy,.73),(4.20,yy,.73),(4.20,yy,.06)],.018,room='study')
cabinet('工位抽屉',3.67,4.18,7.0,7.36,.70,'x+','black','study',drawers=True)
for yy in (7.88,):
    box('工位显示器',(3.77,yy,1.14),(.045,.61,.36),'black','Furniture','study',.008)
    box('工位屏幕',(3.797,yy,1.14),(.006,.58,.33),'screen','Furniture','study',.002)
    tube('显示器支架',[(3.75,yy,.775),(3.75,yy,.96),(3.77,yy,.96)],.018,room='study')
    box('键盘',(4.04,yy,.79),(.16,.40,.018),'black','Furniture','study',.003)

# Lower workstation: laptop only, its screen faces the chair on the east.
box('笔记本底座',(3.98,6.35,.789),(.25,.34,.022),'steel','Furniture','study',.008)
box('笔记本键盘',(4.00,6.35,.802),(.15,.29,.004),'black','Furniture','study',.002)
o=box('笔记本屏幕外壳',(3.85,6.35,.91),(.012,.34,.23),'steel','Furniture','study',.006);o.rotation_euler.y=-.18
box('笔记本屏幕',(3.861,6.35,.91),(.005,.315,.20),'screen','Furniture','study',.003)

def chair(name,x,y,angle=0,office=False,material='tan',room='dining'):
    # local forward is -Y
    def pt(a,b,z):return (x+a*math.cos(angle)-b*math.sin(angle),y+a*math.sin(angle)+b*math.cos(angle),z)
    box(name+'座面',pt(0,0,.46),(.43,.43,.065),material,'Furniture',room,.045,angle)
    box(name+'靠背',pt(0,.20,.73),(.43,.065,.37),material,'Furniture',room,.055,angle)
    if office:
        cyl(name+'气压杆',pt(0,0,.27),.028,.34,'chrome',room=room)
        for k in range(5):
            a=k*math.tau/5
            tube(name+'五星脚',[pt(0,0,.13),pt(.26*math.cos(a),.26*math.sin(a),.07)],.018,room=room)
            sphere(name+'脚轮',pt(.26*math.cos(a),.26*math.sin(a),.045),(.035,.035,.035),'black',room=room)
        for xx in (-.25,.25):
            tube(name+'扶手支架',[pt(xx,0,.46),pt(xx,.06,.66),pt(xx,-.15,.66)],.012,room=room)
    else:
        for xx in (-.19,.19):
            tube(name+'悬臂钢管',[pt(xx,.19,.78),pt(xx,.19,.46),pt(xx,-.19,.46),pt(xx,-.19,.06),pt(xx,.22,.06)],.013,room=room)
for yy in (6.35,7.87):chair('人体工学椅',4.58,yy,-math.pi/2,True,'ivory','study')
# Daily dining layout: 900 mm table shifted east; west entrance route remains clear.
cyl('圆餐桌桌面',(2.45,3.70,.76),.45,.045,'walnut',room='dining',vertices=64)
cyl('圆餐桌中柱',(2.45,3.70,.39),.075,.70,'black',room='dining')
cyl('圆餐桌底座',(2.45,3.70,.045),.30,.045,'black',room='dining',vertices=48)
for a in [math.pi/3,2*math.pi/3,math.pi]:
    chair('日常餐椅',2.45+.66*math.cos(a),3.70+.66*math.sin(a),a-math.pi/2,False,'tan','dining')
# Kitchen: exact peninsula/U outline; sink and hob have real recessed bowls.
# Work-side access: dishwasher, utensil pull-out and sink unit face east.
rect('洗碗机隔侧板',1.79,2.39,1.17,1.188,.10,.85,'walnut','Storage','kitchen')
rect('洗碗机隔侧板',1.79,2.39,1.79,1.808,.10,.85,'walnut','Storage','kitchen')
rect('水槽柜餐厅侧背板',1.79,1.808,1.17,2.97,.10,.85,'walnut','Storage','kitchen')
cabinet('备餐窄抽屉',1.81,2.37,1.81,2.07,.85,'x+','walnut','kitchen',drawers=True)
for yy in (2.09,2.952):rect('水槽柜侧板',1.81,2.39,yy,yy+.018,.10,.85,'walnut','Storage','kitchen')
rect('水槽柜底板',1.81,2.39,2.09,2.97,.10,.118,'walnut','Storage','kitchen')
for y1,y2 in [(2.09,2.525),(2.535,2.97)]:
 o=rect('水槽柜内侧对开门',2.39,2.408,y1,y2,.11,.84,'walnut','Storage','kitchen');o['front_panel']=True
 tube('水槽柜门拉手',[(2.43,(y1+y2)/2-.07,.74),(2.43,(y1+y2)/2+.07,.74)],.007,room='kitchen')
tube('水槽存水弯',[(2.09,2.41,.66),(2.09,2.41,.35),(2.0,2.41,.28),(1.9,2.41,.35)],.025,'white','Appliances','kitchen')
box('水槽下分类桶',(2.14,2.78,.31),(.32,.27,.36),'ivory','Storage','kitchen',.018)
rect('厨房转角封板',2.10,2.39,.84,1.17,.10,.85,'walnut','Storage','kitchen')
rect('厨房转角连续钢台面',2.10,2.39,.84,1.17,.85,.88,'steel','Furniture','kitchen')
cabinet('灶下橱柜',2.10,3.28,.24,.84,.85,'y+','walnut','kitchen',drawers=True)
# Automatic-water robot dock under window; 430 x 300 mm clear front opening.
rect('扫地机设备柜背板',3.94,3.97,.86,1.50,.02,.85,'walnut','Storage','kitchen')
for yy in (.86,1.48):rect('扫地机设备柜侧板',3.37,3.94,yy,yy+.02,.02,.85,'walnut','Storage','kitchen')
rect('扫地机设备柜上隔板',3.37,3.94,.88,1.48,.34,.36,'walnut','Storage','kitchen')
for ya,yb in [(.88,.96),(1.39,1.48)]:rect('扫地机洞口侧封板',3.35,3.37,ya,yb,.02,.34,'walnut','Storage','kitchen')
o=rect('扫地机设备柜检修门',3.35,3.37,.88,1.48,.36,.84,'walnut','Storage','kitchen');o['front_panel']=True
box('扫地机自动上下水基站',(3.70,1.175,.1445),(.450,.381,.249),'white','Appliances','kitchen',.018)
cyl('扫地机器人归位',(3.48,1.175,.070),.165,.100,'white','Appliances','kitchen',48)
rect('扫地机防水托盘',3.38,3.94,.91,1.44,.016,.025,'steel','Appliances','kitchen')
# Narrow tall pantry in front of the boxed stack, divided for daily / spare items.
cabinet('冰箱旁窄高柜下区',3.37,3.71,2.23,2.46,1.20,'x-','walnut','kitchen')
cabinet('冰箱旁窄高柜上区',3.37,3.71,2.23,2.46,2.40,'x-','walnut','kitchen',base=1.20)
rect('灶侧钢台面',2.08,3.30,.23,.86,.85,.88,'steel','Furniture','kitchen')
rect('管井前钢台面',3.30,3.97,.62,.86,.85,.88,'steel','Furniture','kitchen')
rect('窗侧钢台面',3.35,3.99,.86,1.50,.85,.88,'steel','Furniture','kitchen')
# Sink opening split into four strips, leaving a genuine recess.
for b in [(1.79,2.39,1.17,2.10),(1.79,2.39,2.72,2.97),(1.79,1.87,2.10,2.72),(2.31,2.39,2.10,2.72)]:
    rect('岛台不锈钢台面',*b,.85,.88,'steel','Furniture','kitchen')
rect('水槽内底',1.87,2.31,2.10,2.72,.66,.68,'steel','Furniture','kitchen',.025)
for b in [(1.87,1.885,2.10,2.72),(2.295,2.31,2.10,2.72),(1.87,2.31,2.10,2.115),(1.87,2.31,2.705,2.72)]:
    rect('水槽内壁',*b,.68,.88,'steel','Furniture','kitchen',.006)
tube('厨房鹅颈水龙头',[(1.835,2.24,.88),(1.835,2.24,1.18),(1.87,2.28,1.23),(2.01,2.42,1.23),(2.04,2.45,1.17)],.018,room='kitchen')
cyl('水槽下水口',(2.09,2.41,.686),.035,.006,'black',room='kitchen')
rect('嵌入式燃气灶',2.47,3.27,.35,.80,.882,.90,'black','Furniture','kitchen',.016)
for xx in (2.66,3.08):
    cyl('炉头',(xx,.56,.92),.076,.018,'steel',room='kitchen')
    for a in range(4):
        ang=a*math.pi/2
        tube('炉架',[(xx+.025*math.cos(ang),.56+.025*math.sin(ang),.95),(xx+.12*math.cos(ang),.56+.12*math.sin(ang),.95)],.007,'black',room='kitchen')
rect('钢制抽油烟机',2.43,3.33,.25,.75,1.62,1.70,'steel','Furniture','kitchen')
rect('烟机风管',2.68,3.08,.25,.57,1.7,2.72,'steel','Furniture','kitchen')
# Services: shaft positions follow plan symbols, diameters and branches are schematic.
def service(o,kind,source='CAD shaft position; diameter / routing schematic'):
 o['service_kind']=kind;o['source']=source;return o
service(rect('厨房排烟竖井',3.61,3.90,.30,.54,0,H,'steel','Services','kitchen'),'exhaust')
for name,x,y,r,room in [('厨房下水立管',3.42,.43,.055,'kitchen'),('厨房冰箱侧下水立管',3.85,2.34,.055,'kitchen'),('客卫排污立管',3.82,2.85,.055,'guestbath'),('客卫排水立管',3.82,3.04,.0375,'guestbath'),('客卫通气立管',3.82,3.20,.0375,'guestbath'),('主卫排污立管',9.43,3.25,.055,'masterbath'),('主卫排水立管',9.43,3.45,.0375,'masterbath'),('主卫通气立管',9.43,3.64,.0375,'masterbath')]:
 service(tube(name,[(x,y,-.06),(x,y,H)],r,'white','Services',room),'drain')
for name,b,room in [('厨房烟道砌筑包封',(3.55,3.97,.24,.62),'kitchen'),('厨房下水包管',(3.30,3.55,.24,.62),'kitchen'),('厨房冰箱侧包管',(3.73,3.97,2.23,2.46),'kitchen'),('客卫砖砌包管',(3.71,3.94,2.70,3.29),'guestbath'),('主卫砖砌包管',(9.30,9.56,3.11,3.76),'masterbath')]:
 rect(name,*b,0,H,'tile' if room!='kitchen' else 'wall','ServiceEnclosures',room)
service(tube('烟机接入烟道示意',[(2.88,.41,2.48),(3.75,.41,2.48)],.09,'steel','Services','kitchen'),'exhaust')
# Supply/drain routes are proposals, not surveyed construction drawings.
for name,pts,r,kind,room in [
 ('厨房水槽排水支管示意',[(1.90,2.41,.35),(1.90,2.41,-.04),(2.22,2.41,-.04),(2.22,.70,-.04),(3.42,.70,-.04),(3.42,.43,.20)],.025,'drain','kitchen'),
 ('扫地机排水接入示意',[(3.92,1.17,.23),(3.92,1.17,.33),(3.88,.70,.33),(3.42,.70,.33),(3.42,.43,.33)],.012,'drain','kitchen'),
 ('扫地机冷水支管示意',[(3.92,1.21,.20),(3.92,1.21,.58),(3.48,.70,.58),(3.48,.43,.58)],.008,'supply','kitchen'),
 ('主卫马桶排水支管示意',[(9.10,4.32,-.04),(9.43,4.32,-.04),(9.43,3.25,-.04)],.055,'drain','masterbath'),
 ('主卫台盆排水支管示意',[(9.25,5.20,.62),(9.25,5.20,-.04),(9.43,5.20,-.04),(9.43,3.45,-.04)],.025,'drain','masterbath'),
 ('客卫马桶排水支管示意',[(4.10,3.27,-.04),(3.82,3.27,-.04),(3.82,2.85,-.04)],.055,'drain','guestbath'),
 ('客卫洗手台排水支管示意',[(3.94,4.15,.58),(3.94,4.15,-.04),(3.82,4.15,-.04),(3.82,3.04,-.04)],.025,'drain','guestbath')]:
 service(tube(name,pts,r,'blue' if kind=='supply' else 'white','Services',room),kind,'Proposed branch route; verify on site')
box('扫地机供水检修阀',(3.90,1.21,.58),(.035,.055,.055),'blue','Appliances','kitchen')
# Keep kitchen cabinetry outside the full-height shafts.
# Tile backsplash with explicit grout, no full-wall stone.
rect('厨房砖缝基层',2.10,3.95,.238,.251,.89,1.65,'grout','Furniture','kitchen')
for i in range(12):
 for j in range(5):
    xx=2.10+i*.154;zz=.89+j*.152
    rect('厨房小方砖',xx,xx+.150,.251,.259,zz,zz+.148,'tile','Furniture','kitchen',.002)
# No wall cabinets or floating shelves over the kitchen worktop.
# Refrigerator occupies the CAD fridge block on east run.
rect('冰箱箱体',3.37,3.97,1.51,2.21,0,1.91,'fridge_white','Appliances','kitchen',.035)
for y1,y2 in [(1.52,1.855),(1.865,2.20)]:
    rect('冰箱对开门',3.345,3.37,y1,y2,.04,1.89,'fridge_white','Appliances','kitchen',.014)
    tube('冰箱把手',[(3.325,(y1+y2)/2,.95),(3.325,(y1+y2)/2,1.42)],.009,'steel',room='kitchen')
rect('洗碗机箱体',1.82,2.37,1.20,1.78,.10,.82,'steel','Appliances','kitchen')
rect('洗碗机面板',2.395,2.42,1.20,1.78,.10,.81,'steel','Appliances','kitchen')
rect('洗碗机黑色控制条',2.422,2.426,1.21,1.77,.73,.79,'black','Appliances','kitchen')
# Kitchen and bathroom floor tiles.
def tilefloor(name,b,matname='tile',size=.30):
 x1,x2,y1,y2=b
 for i in range(math.ceil((x2-x1)/size)):
  for j in range(math.ceil((y2-y1)/size)):
   a=x1+i*size;b=min(a+size,x2);c=y1+j*size;d=min(c+size,y2)
   rect(name,a+.002,b-.002,c+.002,d-.002,.002,.016,matname,'Floor',bevel=.001)
tilefloor('厨房地砖',(1.79,4.21,0,2.46),'tile',.45)
tilefloor('主卫地砖',(8.06,9.56,3.11,5.77),'tile',.3)
tilefloor('客卫地砖',(3.71,5.22,2.70,3.80),'tile',.3)
tilefloor('客卫淋浴地砖',(4.21,5.22,1.83,2.70),'tile',.3)

# Laundry stacked washer/dryer in the south-east end of the balcony.
rect('洗烘柜背板',6.18,6.21,8.70,9.99,.03,2.50,'walnut','Storage','laundry')
rect('洗烘柜顶板',5.54,6.21,8.70,9.99,2.47,2.50,'walnut','Storage','laundry')
for yy in (8.70,9.96):rect('洗烘柜侧板',5.54,6.21,yy,yy+.03,.03,2.50,'walnut','Storage','laundry')
cabinet('洗烘区收纳台',5.54,6.18,8.73,9.10,.85,'x-','walnut','laundry')
# Machine units face west, top view matches the drawing footprint.
for z,name in [(.43,'洗衣机'),(1.30,'烘干机')]:
    box(name,(5.88,9.47,z),(.62,.62,.82),'white','Appliances','laundry',.022)
    cyl(name+'门圈',(5.553,9.47,z),.225,.025,'steel','Appliances','laundry',48,(0,math.pi/2,0))
    cyl(name+'玻璃门',(5.536,9.47,z),.18,.024,'screen','Appliances','laundry',48,(0,math.pi/2,0))
    box(name+'控制板',(5.533,9.47,z+.30),(.012,.48,.07),'black','Appliances','laundry',.004)
rect('洗衣机上层板',5.54,6.21,9.12,9.82,1.73,1.76,'walnut','Storage','laundry')
# Handcraft station in CAD recess: 1280 x 560, 750 mm working height.
rect('手工桌桌面',5.66,6.22,7.12,8.40,.72,.75,'walnut','Furniture','study',.012)
for yy in (7.14,8.36):rect('手工桌侧腿',5.70,6.20,yy,yy+.025,.02,.72,'walnut','Furniture','study')
rect('手工桌背挡',6.18,6.20,7.16,8.36,.12,.72,'walnut','Furniture','study')
# Compact upper cupboards only 280 mm deep, with 800 mm clear above desktop.
for ya,yb in [(7.14,7.74),(7.78,8.38)]:cabinet('手工小吊柜',5.92,6.20,ya,yb,2.15,'x-','walnut','study',base=1.55)
rect('手工桌工具挂板',6.18,6.20,7.20,8.30,.84,1.44,'tan','Furniture','study')
for yy in (7.30,7.60,7.90,8.20):tube('工具挂钩',[(6.17,yy,1.20),(6.12,yy,1.20),(6.12,yy,1.24)],.006,room='study')
box('缝纫机底座',(5.94,7.91,.775),(.29,.31,.045),'white','Furniture','study',.018)
box('缝纫机机身',(6.01,7.93,.90),(.10,.28,.22),'white','Furniture','study',.035)
box('缝纫机机臂',(5.93,7.93,.98),(.25,.10,.09),'white','Furniture','study',.025)
cyl('缝纫线轴',(6.01,7.92,1.04),.025,.06,'red',room='study')
# Tucked movable stool, leaving the shared aisle clear.
cyl('手工桌收起圆凳',(5.98,7.45,.44),.18,.06,'green',room='study')
for yy in (7.34,7.56):tube('手工凳腿',[(5.88,yy,.02),(5.88,yy,.41),(6.08,yy,.41),(6.08,yy,.02)],.012,room='study')
# Metal hanging wardrobes: open upper part, sliding/folding doors set aside.
def metalwardrobe(name,b,face,room):
 x1,x2,y1,y2=b
 rect(name+'底板',x1,x2,y1,y2,.05,.08,'white','Storage',room)
 rect(name+'顶板',x1,x2,y1,y2,2.43,2.47,'white','Storage',room)
 if face=='x+':
  rect(name+'背板',x1,x1+.025,y1,y2,.08,2.43,'wall','Storage',room)
  for yy in [y1+.03,(y1+y2)/2,y2-.03]:
   tube(name+'立轨',[(x1+.04,yy,.08),(x1+.04,yy,2.43)],.014,'steel',room=room)
  for z in [1.12,2.12]:tube(name+'挂衣杆',[(x1+.34,y1+.06,z),(x1+.34,y2-.06,z)],.014,'steel',room=room)
  for i in range(max(2,int((y2-y1)/.17))):
   yy=y1+.1+i*.17
   tube(name+'衣架',[(x1+.34,yy,2.12),(x1+.12,yy,1.98),(x1+.53,yy,1.98),(x1+.34,yy,2.12)],.005,'chrome',room=room)
   box(name+'悬挂衣物',(x1+.33,yy,1.63),(.40,.065,.66),['ivory','green','tan','blue'][i%4],'Storage',room,.035)
  rect(name+'侧移门',x2,x2+.025,y1,y1+.38,0,2.48,'ivory','Storage',room)
 else:
  rect(name+'背板',x1,x2,y1,y1+.025,.08,2.43,'wall','Storage',room)
  tube(name+'挂衣杆',[(x1+.06,y1+.34,2.12),(x2-.06,y1+.34,2.12)],.014,'steel',room=room)
  for i in range(max(2,int((x2-x1)/.18))):
   xx=x1+.11+i*.18
   tube(name+'衣架',[(xx,y1+.34,2.12),(xx,y1+.12,1.98),(xx,y1+.53,1.98),(xx,y1+.34,2.12)],.005,'chrome',room=room)
   box(name+'悬挂衣物',(xx,y1+.33,1.63),(.065,.40,.66),['ivory','green','tan','black'][i%4],'Storage',room,.03)
  for xx in [x1+.03,(x1+x2)/2,x2-.03]:tube(name+'立轨',[(xx,y1+.04,.08),(xx,y1+.04,2.43)],.014,'steel',room=room)
  rect(name+'侧移门',x1,x1+.38,y2,y2+.025,0,2.48,'ivory','Storage',room)
# The CAD bed-end gap is tight: 360 mm shallow storage uses front-facing hanging,
# with front-facing pull-out hanging rails rather than transverse 600 mm hangers.
rect('床尾浅衣柜背板',6.50,6.52,6.99,9.30,.05,2.40,'white','Storage','master')
for yy in (7.02,8.145,9.27):tube('床尾浅柜金属立柱',[(6.83,yy,.06),(6.83,yy,2.4)],.012,'steel','Storage','master')
for z in (.08,1.12,2.38):rect('床尾浅柜层板',6.52,6.86,6.99,9.30,z,z+.018,'white','Storage','master')
for yy in (7.28,7.86,8.44,9.02):
 for hz in (1.06,2.14):
  tube('浅柜前后抽拉挂衣杆',[(6.54,yy,hz),(6.82,yy,hz)],.013,'steel','Storage','master')
  for xx in (6.58,6.68,6.78):
   tube('浅柜正向衣架',[(xx,yy,hz),(xx,yy-.21,hz-.14),(xx,yy+.21,hz-.14),(xx,yy,hz)],.004,'steel','Storage','master')
   box('浅柜正挂短衣',(xx,yy,hz-.45),(.045,.40,.60),'ivory','Storage','master',.02)
o=rect('床尾浅柜侧停移门',6.865,6.88,6.99,7.36,.05,2.40,'ivory','Storage','master');o['front_panel']=True
metalwardrobe('主卧长衣金属衣柜',(5.68,7.91,5.31,5.89),'y+','master')

# Master bed: 1.80m wide, approximately 1.95m long, headboard against east wall.
box('主床床架',(8.53,7.85,.23),(2.03,1.83,.32),'walnut','Furniture','master',.035)
box('主床床垫',(8.52,7.85,.49),(1.95,1.79,.24),'ivory','Furniture','master',.09)
box('主床被褥',(8.28,7.85,.64),(1.45,1.80,.13),'ivory','Furniture','master',.095)
box('床尾橄榄绿毯',(7.90,7.85,.72),(.48,1.82,.055),'green','Furniture','master',.03)
for yy in (7.43,8.27):
    o=box('主床枕头',(9.18,yy,.71),(.43,.65,.16),'white','Furniture','master',.10);o.rotation_euler.y=-.12
rect('极简床头木板',9.51,9.56,6.99,9.30,.10,1.08,'walnut','Furniture','master')
cabinet('床侧悬浮小抽屉',9.15,9.51,6.65,6.92,.58,'x-','walnut','master',base=.40,drawers=True)
cabinet('床头柜南',9.06,9.51,8.79,9.29,.52,'x-','walnut','master',drawers=True)
rect('主卧梳妆台',9.03,9.53,5.98,6.61,.74,.78,'walnut','Furniture','master')
cabinet('梳妆浅抽屉',9.05,9.51,6.02,6.57,.74,'x-','walnut','master',base=.58,drawers=True)
cyl('梳妆圆凳',(8.65,6.35,.42),.22,.08,'green',room='master')
for x in (8.52,8.78):
 for y in (6.22,6.48):tube('圆凳脚',[(x,y,.05),(x,y,.40)],.012,room='master')
box('梳妆镜',(9.535,6.38,1.38),(.012,.52,.75),'mirror','Furniture','master',.02)

# Guest daybed rotates along the window wall: 2.0 x 0.9 m, open cabinet aisle.
box('次卧日床框架',(6.74,2.45,.22),(2.00,.90,.34),'walnut','Furniture','guest',.035)
box('次卧日床床垫',(6.74,2.46,.48),(1.94,.84,.21),'ivory','Furniture','guest',.07)
box('次卧低靠背',(6.74,2.02,.66),(2.00,.10,.27),'ivory','Furniture','guest',.04)
for xx in (5.77,7.71):box('次卧日床端板',(xx,2.45,.48),(.06,.90,.52),'walnut','Furniture','guest',.02)
for xx,ma in [(6.12,'red'),(7.32,'tan')]:box('次卧抱枕',(xx,2.18,.68),(.42,.18,.32),ma,'Furniture','guest',.07)
cyl('次卧可移边几',(7.58,3.24,.49),.18,.025,'steel',room='guest')
cyl('次卧边几立柱',(7.58,3.24,.27),.022,.42,'chrome',room='guest')
cabinet('次卧分格收纳柜',6.50,7.80,3.80,4.18,1.02,'y-','walnut','guest')
# CAD niche: x=6.38..7.91, y=4.32..5.17, 1530 x 850 mm before door lining.
# Shelves along its long north side replace the old end-on narrow rack.
for z in (.10,.60,1.10,1.60,2.10):rect('储物间长边浅层板',6.48,7.87,4.82,5.14,z,z+.02,'walnut','Storage','store')
for xx in (6.50,7.20,7.85):rect('储物间层板立撑',xx,xx+.018,4.84,5.14,.08,2.12,'steel','Storage','store')
for xx in (6.76,7.43):
 for z in (.63,1.13,1.63):box('储物间收纳箱',(xx,4.99,z+.13),(.48,.27,.24),'ivory','Storage','store',.015)
for ya,yb in [(4.32,4.35),(5.14,5.17)]:rect('储物间柜门框',6.38,6.46,ya,yb,0,2.40,'walnut','Storage','store')
rect('储物间柜门顶封',6.38,6.46,4.32,5.17,2.36,H,'wall','Storage','store')
for ya,yb in [(4.353,4.739),(4.745,5.137)]:
 o=rect('储物间封闭柜门',6.38,6.40,ya,yb,.025,2.355,'walnut','Storage','store');o['front_panel']=True
 o=tube('储物间柜门拉手',[(6.355,(ya+yb)/2,1.00),(6.355,(ya+yb)/2,1.18)],.007,room='store');o['front_panel']=True

def toilet(name,x,y,angle=0,room='guestbath'):
    # toilet length along X, outlet at east/right side, as in the CAD.
    sphere(name+'主体',(x,y,.29),(.31,.20,.25),'white',room=room)
    o=cyl(name+'座圈',(x-.03,y,.47),.22,.045,'white',room=room,vertices=48);o.scale.x=1.3
    o=cyl(name+'座圈内凹',(x-.05,y,.494),.155,.005,'grout',room=room,vertices=48);o.scale.x=1.25
    box(name+'后背',(x+.26,y,.50),(.16,.37,.42),'white','Furniture',room,.045)
    box(name+'盖板',(x-.03,y,.512),(.49,.36,.024),'white','Furniture',room,.07)
    if angle:
        for o in list(bpy.data.objects):
            if o.name.startswith(name):
                dx=o.location.x-x;dy=o.location.y-y
                o.location.x=x+dx*math.cos(angle)-dy*math.sin(angle);o.location.y=y+dx*math.sin(angle)+dy*math.cos(angle);o.rotation_euler.z+=angle
def basin(name,b,room,wallmount='x+'):
    x1,x2,y1,y2=b
    cabinet(name+'悬空柜',x1,x2,y1,y2,.64,'x-' if wallmount=='x+' else 'y+','walnut',room,base=.28)
    for ob in list(bpy.data.objects):
        if ob.name.startswith(name+'悬空柜可调层板'):bpy.data.objects.remove(ob,do_unlink=True)
    # rim with four strips and recessed basin center
    cx=(x1+x2)/2;cy=(y1+y2)/2
    for bb in [(x1,x1+.07,y1,y2),(x2-.07,x2,y1,y2),(x1+.07,x2-.07,y1,y1+.10),(x1+.07,x2-.07,y2-.10,y2)]:
        rect(name+'陶瓷盆沿',*bb,.64,.82,'white','Furniture',room,.012)
    rect(name+'盆底',x1+.07,x2-.07,y1+.10,y2-.10,.66,.68,'white','Furniture',room,.03)
    for bb in [(x1+.07,x1+.085,y1+.10,y2-.10),(x2-.085,x2-.07,y1+.10,y2-.10),(x1+.07,x2-.07,y1+.10,y1+.115),(x1+.07,x2-.07,y2-.115,y2-.10)]:
        rect(name+'陶瓷盆内壁',*bb,.68,.79,'white','Furniture',room,.004)
    if wallmount=='x+':
        tube(name+'墙出水龙头',[(x2+.01,cy,1.04),(cx,cy,1.04),(cx,cy,.99)],.012,room=room)
        box(name+'镜子',(x2+.008,cy,1.53),(.012,y2-y1, .86),'mirror','Furniture',room,.015)
    else:
        tube(name+'墙出水龙头',[(cx,y1-.01,1.04),(cx,cy,1.04),(cx,cy,.99)],.012,room=room)
        box(name+'镜子',(cx,y1-.015,1.53),(x2-x1,.012,.86),'mirror','Furniture',room,.015)
toilet('主卫马桶',9.10,4.32,room='masterbath')
toilet('客卫马桶',4.10,3.27,angle=math.pi,room='guestbath')
basin('主卫台盆',(9.00,9.53,4.80,5.60),'masterbath','x+')
# CAD corner countertop: (3710,3935)-(4380,3935)-(3750,4600)-(3710,4600).
TRI=[(3.710,3.935),(4.380,3.935),(3.750,4.600),(3.710,4.600)]
prism('客卫三角柜底板',TRI,.28,.298,'walnut','Storage','guestbath')
prism('客卫三角转角层板',TRI,.46,.478,'ivory','Storage','guestbath')
for a,b in [(TRI[0],TRI[1]),(TRI[2],TRI[3]),(TRI[3],TRI[0])]:
 dx=b[0]-a[0];dy=b[1]-a[1];box('三角盆柜靠墙侧板',((a[0]+b[0])/2,(a[1]+b[1])/2,.53),(math.hypot(dx,dy),.018,.50),'walnut','Storage','guestbath',.003,math.atan2(dy,dx))
a,b=TRI[1],TRI[2];dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
for t in (.25,.75):
 o=box('三角盆柜斜面柜门',(a[0]+dx*t,a[1]+dy*t,.54),(length/2-.006,.018,.47),'walnut','Storage','guestbath',.003,math.atan2(dy,dx));o['front_panel']=True
 tube('三角盆柜斜面拉手',[(a[0]+dx*(t-.07)+.014,a[1]+dy*(t-.07)+.014,.69),(a[0]+dx*(t+.07)+.014,a[1]+dy*(t+.07)+.014,.69)],.006,'steel','Storage','guestbath')
# Boolean cut makes an actual recess; bowl remains round as drawn in the CAD.
top=prism('CAD三角洗手台面',TRI,.78,.815,'white','Furniture','guestbath')
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.165,depth=.30,location=(3.915,4.140,.80));cutter=bpy.context.object
bpy.context.view_layer.objects.active=top;mod=top.modifiers.new('真实盆洞','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
verts=[];faces=[];rings=[(.180,.820),(.157,.815),(.145,.720),(.035,.675)]
for rad,z in rings:
 for i in range(64):verts.append((3.915+rad*math.cos(i*math.tau/64),4.140+rad*math.sin(i*math.tau/64),z))
for j in range(3):
 for i in range(64):faces.append((j*64+i,j*64+(i+1)%64,(j+1)*64+(i+1)%64,(j+1)*64+i))
mesh=bpy.data.meshes.new('嵌入盆曲面');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('三角台面内嵌圆盆',mesh);group('Furniture').objects.link(o);finish(o,o.name,'white','Furniture','guestbath')
for q in mesh.polygons:q.use_smooth=True
cyl('洗手盆下水口',(3.915,4.140,.676),.034,.006,'steel',room='guestbath')
tube('客卫墙出水龙头',[(3.72,4.14,1.03),(3.94,4.14,1.03),(3.94,4.14,.98)],.012,room='guestbath')
tube('客卫排水存水弯',[(3.915,4.14,.675),(3.915,4.14,.53),(3.76,4.14,.53)],.022,'white','Appliances','guestbath')
box('客卫圆角镜', (3.725,4.23,1.48),(.014,.48,.70),'mirror','Furniture','guestbath',.025)
cyl('洗手液',(3.77,4.38,.90),.034,.17,'green',room='guestbath')
def shower(name,x,y,room):
    tube(name+'淋浴立管',[(x,y,.93),(x,y,2.05),(x-.28,y,2.05)],.012,room=room)
    cyl(name+'顶喷',(x-.28,y,2.035),.105,.025,'chrome',room=room)
    box(name+'混水器',(x-.02,y,.97),(.10,.27,.045),'chrome','Furniture',room,.015)
    for k in range(2):rect(name+'壁架',x-.17,x+.02,y-.22,y+.22,1.18+k*.28,1.20+k*.28,'steel','Furniture',room)
shower('主卫淋浴',9.29,3.53,'masterbath')
shower('客卫淋浴',4.28,2.25,'guestbath')
curtain('主卫浴帘收拢',(8.17,3.87),(8.54,3.87),.08,2.20,'ivory')
curtain('客卫浴帘收拢',(4.27,2.80),(4.62,2.80),.08,2.20,'ivory')
tube('主卫浴帘轨道',[(8.09,3.87,2.23),(9.53,3.87,2.23)],.012,'steel','Furniture','masterbath')
tube('客卫暗装轨道',[(4.23,2.80,2.23),(5.20,2.80,2.23)],.012,'steel','Furniture','guestbath')
# Reachable daily bathroom accessories, outside the door sweep.
tube('主卫纸巾架',[(9.53,4.65,.74),(9.43,4.65,.74)],.008,'steel','Furniture','masterbath')
cyl('主卫纸巾卷',(9.43,4.65,.74),.055,.11,'ivory','Furniture','masterbath',32,(0,math.pi/2,0))
tube('主卫毛巾杆',[(8.08,4.78,1.20),(8.15,4.78,1.20),(8.15,5.03,1.20),(8.08,5.03,1.20)],.008,'steel','Furniture','masterbath')
box('主卫手巾',(8.15,4.90,1.05),(.025,.22,.29),'ivory','Furniture','masterbath',.008)
tube('客卫纸巾架',[(3.73,3.62,.74),(3.84,3.62,.74)],.008,'steel','Furniture','guestbath')
cyl('客卫纸巾卷',(3.84,3.62,.74),.055,.11,'ivory','Furniture','guestbath',32,(0,math.pi/2,0))
# Tile wainscoting provides a restrained blue accent.
for room,x,y1,y2 in [('masterbath',9.545,3.12,5.76),('guestbath',5.205,1.85,3.78)]:
    rect(room+'墙面砖基层',x,x+.008,y1,y2,.02,2.30,'grout','BathroomWalls',room)
    for j in range(math.ceil((y2-y1)/.15)):
     for k in range(15):
      ya=y1+j*.15;yb=min(ya+.147,y2-.001);za=.035+k*.15
      if yb>ya:rect(room+'小方砖',x-.008,x,ya,yb,za,za+.147,'blue' if k<5 and room=='guestbath' else 'tile','BathroomWalls',room,.002)

# A lounge chair by the south window, on a light tubular frame.
cx,cy=1.60,9.39;a=math.radians(-25)
box('休闲椅坐垫',(cx,cy,.43),(.72,.80,.19),'green','Furniture','living',.10,a)
o=box('休闲椅靠背',(cx-.18,cy+.32,.78),(.74,.20,.77),'green','Furniture','living',.12,a);o.rotation_euler.x=-.18
for xx in (-.34,.34):
 tube('休闲椅钢管',[(cx+xx,cy-.36,.06),(cx+xx,cy-.36,.38),(cx+xx,cy+.35,.38),(cx+xx,cy+.38,.88)],.018,room='living')
cyl('休闲边几',(2.47,9.43,.48),.24,.035,'steel',room='living')
cyl('休闲边几柱',(2.47,9.43,.26),.024,.44,'chrome',room='living')

def lamp(name,x,y,z=2.1,r=.20,room='shared'):
    tube(name+'吊线',[(x,y,z+r),(x,y,H)],.006,'black','Lighting',room)
    sphere(name+'乳白球罩',(x,y,z),(r,r,r),'lamp','Lighting',room)
    data=bpy.data.lights.new(name,'POINT');data.energy=25;data.color=(1,.78,.52);data.shadow_soft_size=.20
    o=bpy.data.objects.new(name,data);group('Lights').objects.link(o);o.location=(x,y,z-.08)
lamp('餐桌吊灯',2.45,3.70,1.80,.22,'dining')
lamp('主卧纸灯',8.40,8.10,2.18,.26,'master')
lamp('次卧球灯',6.48,2.88,2.20,.17,'guest')
for xx,yy in [(2.0,6.2),(4.7,7.0),(2.8,4.9),(5.8,4.5),(3.0,1.3)]:
    cyl('明装筒灯',(xx,yy,H-.07),.055,.14,'white','Lighting')
    cyl('筒灯发光面',(xx,yy,H-.144),.044,.005,'lamp','Lighting')
for yy in (6.70,9.02):
    tube('床头阅读灯杆',[(9.50,yy,1.18),(9.35,yy,1.18)],.012,'chrome','Lighting','master')
    sphere('床头阅读灯罩',(9.29,yy,1.18),(.07,.07,.07),'lamp','Lighting','master')
cyl('落地灯底座',(1.10,8.40,.03),.18,.04,'black','Lighting','living')
tube('落地灯杆',[(1.10,8.40,.05),(1.10,8.40,1.60),(1.37,8.40,1.60)],.012,'chrome','Lighting','living')
sphere('砖红落地灯罩',(1.37,8.40,1.56),(.18,.18,.10),'red','Lighting','living')
for yy in (6.4,7.9):
    box('书桌台灯底座',(4.10,yy+.27,.79),(.13,.13,.018),'red','Lighting','study',.02)
    tube('台灯臂',[(4.10,yy+.27,.80),(4.10,yy+.27,1.15),(3.98,yy+.27,1.25)],.008,'chrome','Lighting','study')
    sphere('红色台灯罩',(3.98,yy+.27,1.24),(.10,.10,.06),'red','Lighting','study')

def plant(name,x,y,scale=1):
    cyl(name+'盆',(x,y,.19*scale),.16*scale,.36*scale,'tan','Decor',vertices=32)
    cyl(name+'土',(x,y,.373*scale),.145*scale,.01,'soil','Decor')
    for k in range(8):
        a=k*2.4;h=(.65+random.random()*.55)*scale;ex=x+math.cos(a)*.26*scale;ey=y+math.sin(a)*.26*scale
        tube(name+'茎',[(x,y,.34*scale),(ex,ey,h)],.005*scale,'leaf','Decor')
        o=sphere(name+'叶',(ex,ey,h),(.13*scale,.055*scale,.22*scale),'leaf','Decor');o.rotation_euler=(.5,math.sin(a)*.6,a)
plant('窗边绿植',1.16,8.98,.85)
# Old floor plant in the new tall-cabinet footprint removed.
# restrained Bauhaus art at west dining wall, physically modelled geometry.
box('几何画木框',(.335,4.90,1.58),(.04,.63,.78),'walnut','Decor',bevel=.004)
box('几何画底纸',(.358,4.90,1.58),(.008,.59,.74),'ivory','Decor',bevel=0)
o=cyl('画作红圆',(.364,4.84,1.70),.17,.006,'red','Decor',vertices=48,rot=(0,math.pi/2,0))
box('画作蓝方',(.367,5.01,1.45),(.007,.24,.25),'blue','Decor',bevel=0)
# Old countertop books removed with the former low sideboard.
cyl('餐桌花瓶',(2.47,3.70,.88),.055,.19,'white','Decor')
tube('花枝',[(2.47,3.70,.9),(2.44,3.71,1.15)],.003,'leaf','Decor')
for i in range(3):sphere('小花',(2.44+i*.025,3.71,1.15+i*.02),(.025,.025,.025),'orange','Decor')
# HVAC is schematic: slot details and local bulkhead, no speculative duct network.
rect('客厅边吊',.31,.66,4.45,8.38,2.42,H,'ceiling','Ceiling')
rect('空调条形风口',.665,.675,6.20,7.95,2.45,2.56,'black','Ceiling')
for z in (2.47,2.50,2.53):rect('风口细格栅',.677,.685,6.22,7.93,z,z+.006,'steel','Ceiling')

# Lighting and named cameras. Full model is exported before display hiding.
world=bpy.data.worlds.new('Warm daylight');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.84,.90,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
def area(name,loc,target,power,size,color=(1,.91,.77)):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    o=bpy.data.objects.new(name,data);group('Lights').objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('South daylight',(4,11.8,5.0),(4,5,0),1100,5,(1,.91,.78))
area('East softbox',(11,6,6),(4,5,0),900,5,(.78,.86,1))
area('Large overhead',(4.5,4.5,9),(4.5,4.5,0),1600,7)
area('Interior fill',(2,4,2.5),(2,6,1),90,2.5)
area('Master fill',(8,6.5,2.4),(8,8,1),70,2)
area('Kitchen fill',(2.8,2.0,2.61),(2.8,2.0,0),130,1.3,(1,.95,.85))
area('Guest fill',(6.5,2.8,2.62),(6.5,2.8,0),100,1.5,(1,.95,.85))
area('Master bath fill',(8.7,4.9,2.28),(9,4.2,0),100,1.1,(1,.96,.88))
area('Guest bath fill',(4.6,3,2.28),(4.6,3,0),65,.8,(1,.96,.88))
area('Dry basin fill',(4.5,4.7,2.10),(3.91,4.14,.80),45,1,(1,.96,.88))
def camera(name,loc,target,lens=24,ortho=None):
    data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);group('Cameras').objects.link(o);o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.lens=lens;data.clip_start=.02;data.clip_end=200
    if ortho:data.type='ORTHO';data.ortho_scale=ortho
    return o
CAMS={
 '01_全屋轴测':camera('01 全屋轴测',(-9,-12,16),(4.7,5.2,.4),ortho=15.8),
 '02_客厅与双人工位':camera('02 客厅与双人工位',(1.12,4.55,1.55),(3.2,8.15,1.15),23),
 '11_65英寸电视支架':camera('11 65英寸电视支架',(2.45,5.70,1.40),(.56,7.06,1.0),25),
 '03_餐厨':camera('03 餐厨',(3.05,5.20,1.60),(2.20,1.55,1.08),24),
 '04_主卧':camera('04 主卧',(7.55,6.16,1.60),(8.65,8.30,1.10),22),
 '05_次卧':camera('05 次卧',(5.58,3.61,1.55),(6.92,2.48,.72),22),
 '06_全屋俯视':camera('06 全屋俯视',(4.95,5.10,18),(4.95,5.10,0),ortho=11.5),
 '08_玄关通顶柜':camera('08 玄关通顶柜',(3.10,2.78,1.64),(.52,2.80,1.37),22),
 '10_玄关柜内分区':camera('10 玄关柜内分区',(3.10,2.78,1.64),(.52,2.80,1.37),22),
 '09_三角洗手台':camera('09 三角洗手台',(4.96,4.91,1.62),(3.92,4.16,.89),30),
 '14_厨房高柜与白桃配色':camera('14 厨房高柜与白桃配色',(2.25,2.80,1.40),(3.58,1.95,1.20),24),
 '12_手工桌':camera('12 手工桌',(4.55,6.7,1.55),(5.98,7.78,1.15),22),
 '13_储物柜':camera('13 储物柜',(4.80,4.45,1.45),(6.42,4.76,1.2),22),
 '07_主卫':camera('07 主卫',(8.68,5.56,1.58),(9.00,4.0,1.0),18),
}
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.cycles.max_bounces=6;scene.cycles.transparent_max_bounces=6
scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.4
scene.render.image_settings.color_mode='RGB';scene.camera=CAMS['01_全屋轴测']
# Root custom properties keep assumptions alongside the geometry.
scene['Project']='中古 / 包豪斯 · 厨房窄高柜 / 富士白配色 v8'
scene['CAD_source']=D['source_dwg'];scene['Style_source']=D['style_source'];scene['Style_revision']=2312
scene['Height_note']='Raw clear height 2.820m; provisional floor build-up 0.100m; model clear height 2.720m.'
scene['Balcony_beam_note']='Original opening MH=2060mm; model underside 1960mm above provisional finished floor.'
for name,o in CAMS.items():o['view_label']=name
# Export complete geometry; curves are converted to mesh for portable GLB.
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT/'全屋模型.blend'))
bpy.ops.object.select_all(action='DESELECT')
curves=[o for o in bpy.data.objects if o.type=='CURVE']
for o in curves:o.select_set(True)
if curves:
    bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'home-model.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,export_apply=True,export_yup=True)
print('MODEL_SAVED',len(bpy.data.objects),flush=True)
render_views=os.environ.get('MODEL_RENDER_VIEWS','01_全屋轴测,06_全屋俯视,02_客厅与双人工位,03_餐厨,04_主卧,05_次卧,07_主卫,08_玄关通顶柜,09_三角洗手台,10_玄关柜内分区,11_65英寸电视支架').split(',')
for name in filter(None,render_views):
    for o in bpy.data.objects:
        if o.get('room') in ('entry','dining') and (o.get('front_panel') or '柜门拉手' in o.name or '抽屉拉手' in o.name):o.hide_render=name.startswith('10')
    overview=name.startswith(('01','06'))
    for cat in ['WallsUpper','Ceiling','Windows','Curtains']:
        if cat in COL:COL[cat].hide_render=overview
    # Small bath wall finish is hidden only in the dollhouse so it cannot float.
    if 'BathroomWalls' in COL:COL['BathroomWalls'].hide_render=overview
    scene.camera=CAMS[name]
    if name.startswith('06'):
        scene.render.resolution_x=1300;scene.render.resolution_y=1400
    else:scene.render.resolution_x=1400;scene.render.resolution_y=1100
    scene.render.filepath=str(OUTPUT/f'{name}.png')
    bpy.ops.render.render(write_still=True)
    print('RENDERED',name,flush=True)
for o in bpy.data.objects:
    if o.get('room') in ('entry','dining'):o.hide_render=False
# Save a friendly default dollhouse view, with full-height model in collections.
for cat in ['WallsUpper','Ceiling','Windows','Curtains','BathroomWalls']:
    COL[cat].hide_render=True
scene.camera=CAMS['01_全屋轴测']
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT/'全屋模型.blend'))
(ROOT/'build-stats.json').write_text(json.dumps({'objects':len(bpy.data.objects),'meshes':len(bpy.data.meshes),'materials':len(bpy.data.materials),'collections':{k:len(v.objects)for k,v in COL.items()},'cameras':list(CAMS)},ensure_ascii=False,indent=2))
print('DONE',flush=True)
