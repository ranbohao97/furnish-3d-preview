"""Blender -b --python export_palette.py -- BASE_VARIANTS_DIR OUTPUT_DIR.

Recolour already audited variants without regenerating geometry.
"""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from living_palette import apply_living_palette
base,out=map(Path,sys.argv[sys.argv.index('--')+1:])
for width in (700,600,800):
    bpy.ops.wm.open_mainfile(filepath=str(base/f'{width}mm/全屋模型.blend'))
    changed=apply_living_palette(bpy)
    bpy.context.scene['Project']='全屋 v12.4 / 客厅中古包豪斯与阿尔托配色'
    dest=out/f'{width}mm';dest.mkdir(parents=True,exist_ok=True)
    (dest/'配色对象.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(dest/'全屋模型.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    curves=[o for o in bpy.data.objects if o.type=='CURVE']
    for o in curves:o.select_set(True)
    if curves:
        bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
    name='home-model.glb' if width==700 else f'home-model-{width}.glb'
    bpy.ops.export_scene.gltf(filepath=str(ROOT/name),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,export_apply=True,export_yup=True)
    print('PALETTE_COMPLETE',width,len(changed),flush=True)
