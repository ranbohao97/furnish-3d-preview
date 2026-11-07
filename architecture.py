"""CAD-audited wall solids and openings shared by fresh builds and re-exports."""
import json


def wall_records(root, master_layout='current'):
    manifest=json.loads((root/'architecture.json').read_text())
    geom=json.loads((root/'current-geometry.json').read_text())
    solids=list(manifest['walls'])
    if master_layout=='inset':
        for w in solids:
            if w['name']=='主卧门上过梁':w['p']=[[x+.67,y]for x,y in w['p']]
            elif w['name']=='主卧门手工侧封墙':w['p']=[[6.21,6.99],[6.50,6.99],[6.50,7.11],[6.21,7.11]]
            elif w['name']=='主卧入口折墙':w['p']=[[7.93,5.17],[7.93,5.29],[6.38,5.29],[6.38,5.89],[6.21,5.89],[6.21,5.17]]
    elif master_layout!='current':raise ValueError(master_layout)
    for i,h in enumerate(geom['hatches']):
        if h['pattern']!='SOLID':continue
        for j,p in enumerate(h['paths']):
            if len(p)<3:continue
            solids.append(dict(name=f'CAD实心结构_{i}_{j}',p=[[x/1000,y/1000]for x,y in p],z1=0,z2=2.72))
    # Every wall uses the same 1100 mm cut, including low sills and lintels.
    result=[]
    for w in solids:
        for lo,hi in [(w['z1'],min(1.10,w['z2'])),(max(1.10,w['z1']),w['z2'])]:
            if hi>lo:result.append(dict(name=w['name'],p=w['p'],z1=lo,z2=hi))
    return result


def rebuild_shell(api, master_layout='current'):
    """Replace the entire shell so corrections can remove excess wall as well."""
    bpy=api['bpy']
    for o in list(bpy.data.objects):
        if o.get('category')in ('WallsLow','WallsUpper'):bpy.data.objects.remove(o,do_unlink=True)
    api['WALLS']=wall_records(api['ROOT'],master_layout)
    api['CUT']=1.10
    api['merge_walls']()
    api['scene']['Architecture_revision']='v12.3 / CAD walls and opening audit'


def finish_door_frames(api):
    """Align four single-leaf doors and their reveals to the CAD jambs / hinges."""
    bpy,rect=api['bpy'],api['rect']
    doors=json.loads((api['ROOT']/'architecture.json').read_text())['doors']
    for d in doors:
        if 'leaf'not in d:continue
        for o in list(bpy.data.objects):
            if o.name.startswith(d['leaf']):bpy.data.objects.remove(o,do_unlink=True)
        x1,x2,y1,y2=d['b'];h=d['height']
        # CAD door-frame profiles give 25 mm rebates at the two jambs.
        for a,b in [(x1,x1+.025),(x2-.025,x2)]:
            rect(d['leaf']+'完整门套',a,b,y1-.035,y2+.015,.014,h,d['material'],'Doors',d['id'],.002)
        rect(d['leaf']+'顶门套',x1,x2,y1-.035,y2+.015,h-.020,h+.015,d['material'],'Doors',d['id'],.002)
        api['door'](d['leaf'],d['hinge'],d['width'],api['math'].radians(d['angle']),d['material'],d['leaf_height']-.014,d['id'])
        for o in bpy.data.objects:
            if o.name==d['leaf'] or o.name==d['leaf']+'拉手':o.location.z+=.014
        for z in (.30,1.10,d['leaf_height']-.25):
            api['cyl'](d['leaf']+'铰链',(*d['hinge'],z),.009,.085,'steel','Doors',d['id'])
    # Meeting stile hides the oversized seam without changing the double doors.
    for o in list(bpy.data.objects):
        if o.name.startswith('主卧双门中缝盖条'):bpy.data.objects.remove(o,do_unlink=True)
    rect('主卧双门中缝盖条',5.586,5.604,6.428,6.452,.02,2.38,'kitchen_white','Doors','master',.001)
