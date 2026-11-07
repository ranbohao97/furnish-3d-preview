"""Blender -b --python export_variants.py -- BASE.blend OUTPUT_DIRECTORY
Re-use the furnished scene; rebuild the audited shell, door frames and kitchen variants.
"""
import bpy,ast,sys,math,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from kitchen_config import layout,build_zone
from model_export import batch_finishes
from revised_interior import finish_revision, finish_layout
from construction_details import finish_construction
from architecture import rebuild_shell, finish_door_frames
from living_palette import apply_living_palette
args=sys.argv[sys.argv.index('--')+1:];base=Path(args[0]);out=Path(args[1])
source=ast.parse((ROOT/'build_model.py').read_text())
helpers=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in ('group','tag','finish','box','rect','cyl','tube','cabinet','chair','door','merge_walls')]
material_map={}
for n in source.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='M' for t in n.targets):
  for k,v in zip(n.value.keys,n.value.values):material_map[k.value]=v.args[0].value
material_map.update(glass='透明玻璃',lamp='乳白发光灯罩')
for width in (700,600,800):
 bpy.ops.wm.open_mainfile(filepath=str(base));COL={c.name:c for c in bpy.data.collections};M={k:bpy.data.materials[v]for k,v in material_map.items() if v in bpy.data.materials};scene=bpy.context.scene
 exec(compile(ast.Module(body=helpers,type_ignores=[]),'build_model_helpers','exec'),globals())
 for o in list(bpy.data.objects):
  if o.name.startswith(('扫地机','窗侧钢台面','冰箱旁窄高柜','法式冰箱')):bpy.data.objects.remove(o,do_unlink=True)
 build_zone(globals(),layout(width));finish_revision(globals());finish_layout(globals());rebuild_shell(globals());finish_door_frames(globals());finish_construction(globals());apply_living_palette(bpy);batch_finishes(bpy)
 scene['Project']='新版CAD与设计师白模重建 v12.4 / 客厅中古包豪斯与阿尔托配色';scene['Fridge_width_mm']=width
 for cat in ('WallsUpper','Ceiling','Windows','Curtains','BathroomWalls'):COL[cat].hide_render=True
 for key in ('09 三角洗手台','09 方形洗手台'):
  if key in bpy.data.objects:
   o=bpy.data.objects[key];o.name='09 方形洗手台';o.location=(4.30,5.12,1.62)
   from mathutils import Vector
   o.rotation_euler=(Vector((4.01,4.12,.96))-o.location).to_track_quat('-Z','Y').to_euler()
 dest=out/f'{width}mm';dest.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(dest/'全屋模型.blend'))
 bpy.ops.object.select_all(action='DESELECT');curves=[o for o in bpy.data.objects if o.type=='CURVE']
 for o in curves:o.select_set(True)
 if curves:bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
 filename='home-model.glb' if width==700 else f'home-model-{width}.glb'
 bpy.ops.export_scene.gltf(filepath=str(ROOT/filename),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,export_apply=True,export_yup=True)
 print('VARIANT_COMPLETE',width,flush=True)
