"""Alternative to the CAD layout: align master door front with the store doors.

CAD x is eastward / inward. Door fronts: 5590 -> 6260 mm (+670 mm).
This is an owner-requested comparison, not a revision to the source CAD.
"""
from architecture import rebuild_shell
from living_palette import apply_living_palette


def apply_master_inset(api):
    bpy,rect,cabinet=api['bpy'],api['rect'],api['cabinet']
    if api['scene'].get('Master_door_layout')=='inset':return
    rebuild_shell(api,'inset')
    for o in list(bpy.data.objects):
        if o.name.startswith(('主卧双门','主卧玻璃门','主卧门竖纹')):o.location.x+=.67
        if o.name.startswith('主卧入口浅柜') or o.name=='主卧入口吊顶':bpy.data.objects.remove(o,do_unlink=True)
        elif o.get('category')in ('WallsLow','WallsUpper'):
            o['source']='CAD shell with owner-requested master entrance alternative'
    # The old bedroom-side shallow cabinet conflicts with the new door jamb.
    # Replace it with a 480 x 310 mm shallow cupboard opening toward the hall.
    cabinet('过道浅柜',6.278,6.588,5.29,5.77,2.40,'x-','kitchen_white','hall',base=.10)
    for y in (5.29,5.752):rect('过道浅柜踢脚端回板',6.278,6.368,y,y+.018,.02,.10,'kitchen_white','Storage','hall',.002)
    rect('过道浅柜顶封',6.260,6.588,5.29,5.77,2.40,2.43,'kitchen_white','Storage','hall',.002)
    rect('内移门外过道吊顶',5.54,6.36,5.17,6.99,2.43,2.72,'ceiling','Ceiling','hall')
    rect('浅柜凹位顶封吊顶',6.36,6.708,5.29,5.89,2.43,2.72,'ceiling','Ceiling','hall')
    rect('主卧入口吊顶',6.36,9.56,5.89,6.30,2.40,2.72,'ceiling','Ceiling','master')
    # Recessed cabinet front shares the 6260 mm door plane.
    apply_living_palette(bpy)
    api['scene']['Master_door_layout']='inset'
    api['scene']['Master_door_offset_mm']=670
    api['scene']['Master_door_front_x_mm']=6260
