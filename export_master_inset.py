"""Blender -b --python export_master_inset.py -- CURRENT_VARIANTS_DIR OUTPUT_DIR."""
import bpy,ast,sys,math,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from master_door_layout import apply_master_inset
base,out=map(Path,sys.argv[sys.argv.index('--')+1:])
source=ast.parse((ROOT/'build_model.py').read_text())
helpers=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in ('group','tag','finish','box','rect','cyl','tube','cabinet','merge_walls')]
material_map={}
for n in source.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name)and t.id=='M'for t in n.targets):
        for k,v in zip(n.value.keys,n.value.values):material_map[k.value]=v.args[0].value
material_map.update(glass='透明玻璃',lamp='乳白发光灯罩')
for width in (700,600,800):
    bpy.ops.wm.open_mainfile(filepath=str(base/f'{width}mm/全屋模型.blend'))
    COL={c.name:c for c in bpy.data.collections};M={k:bpy.data.materials[v]for k,v in material_map.items() if v in bpy.data.materials};scene=bpy.context.scene
    exec(compile(ast.Module(body=helpers,type_ignores=[]),'build_model_helpers','exec'),globals())
    apply_master_inset(globals())
    scene['Project']='全屋 v13.1 / 主卧门内移至储藏室门齐平'
    for cat in ('WallsUpper','Ceiling','Windows','Curtains','BathroomWalls'):COL[cat].hide_render=True
    dest=out/'inset'/f'{width}mm';dest.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(dest/'全屋模型.blend'))
    bpy.ops.object.select_all(action='DESELECT');curves=[o for o in bpy.data.objects if o.type=='CURVE']
    for o in curves:o.select_set(True)
    if curves:bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
    bpy.ops.export_scene.gltf(filepath=str(ROOT/f'home-model-inset-{width}.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,export_apply=True,export_yup=True)
    print('INSET_COMPLETE',width,flush=True)
