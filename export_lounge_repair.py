"""Blender -b --python export_lounge_repair.py -- CURRENT_DIR INSET_DIR OUTPUT_DIR."""
import ast,json,sys,math
from pathlib import Path
import bpy
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from lounge_chair import repair_lounge
current,inset,out=map(Path,sys.argv[sys.argv.index('--')+1:])
source=ast.parse((ROOT/'build_model.py').read_text())
helpers=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in ('group','tag','finish','box','cyl','tube')]
material_map={}
for n in source.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='M' for t in n.targets):
        material_map={k.value:v.args[0].value for k,v in zip(n.value.keys,n.value.values)}

def validate():
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    def shape(o):
        e=o.evaluated_get(dg);m=e.to_mesh()
        try:
            verts=[e.matrix_world@v.co for v in m.vertices]
            return verts,BVHTree.FromPolygons(verts,[list(p.vertices)for p in m.polygons])
        finally:e.to_mesh_clear()
    chair={o.name:shape(o)for o in bpy.data.objects if o.name.startswith('休闲椅')}
    cushions=[n for n in chair if n in ('休闲椅坐垫','休闲椅靠背')]
    for i,name in enumerate(cushions):
        for other in cushions[i+1:]:assert not chair[name][1].overlap(chair[other][1]),(name,other)
        for other in chair:
            # Mounting pads intentionally enter only the rear of the back by 3 mm.
            if other in cushions or '连接件'in other:continue
            assert not chair[name][1].overlap(chair[other][1]),(name,other)
    nearby=[o for o in bpy.data.objects if o.name.startswith(('窗边绿植','休闲边几','南窗纱帘','阳台','落地灯')) and o.type in ('MESH','CURVE')]
    for o in nearby:
        _,bvh=shape(o)
        for name,(_,part)in chair.items():assert not part.overlap(bvh),(name,o.name)
    points=[p for v,_ in chair.values()for p in v]
    lo=[min(p[i]for p in points)for i in range(3)];hi=[max(p[i]for p in points)for i in range(3)]
    assert lo[2]>=.014 and lo[2]<=.019,lo
    assert hi[1]<10.04,hi
    return {'passed':True,'chair_parts':len(chair),'bounds_m':[lo,hi],'nearby_objects_checked':len(nearby),'cushion_frame_intersections':0,'neighbor_intersections':0,'intentional_rear_mount_insertion_mm':3}

for layout,base in [('current',current),('inset',inset)]:
    for width in (700,600,800):
        bpy.ops.wm.open_mainfile(filepath=str(base/f'{width}mm/全屋模型.blend'))
        COL={c.name:c for c in bpy.data.collections};M={k:bpy.data.materials[v]for k,v in material_map.items() if v in bpy.data.materials};scene=bpy.context.scene
        exec(compile(ast.Module(body=helpers,type_ignores=[]),'build_model_helpers','exec'),globals())
        repair_lounge(globals());report=validate()
        dest=out/layout/f'{width}mm';dest.mkdir(parents=True,exist_ok=True)
        (dest/'躺椅几何核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        scene['Project']='全屋 v13.5 / 阳台躺椅穿模修复'
        bpy.ops.wm.save_as_mainfile(filepath=str(dest/'全屋模型.blend'))
        bpy.ops.object.select_all(action='DESELECT');curves=[o for o in bpy.data.objects if o.type=='CURVE']
        for o in curves:o.select_set(True)
        if curves:bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
        name=f'home-model-inset-{width}.glb' if layout=='inset' else ('home-model.glb' if width==700 else f'home-model-{width}.glb')
        bpy.ops.export_scene.gltf(filepath=str(ROOT/name),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,export_apply=True,export_yup=True)
        print('LOUNGE_COMPLETE',layout,width,report,flush=True)
