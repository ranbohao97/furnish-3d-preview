"""Balcony lounge chair: every part shares one local frame (metres, Z up)."""
import math

CENTER = (1.90, 9.30)
ANGLE = math.radians(-25)
LEAN = math.radians(12)
TABLE_CENTER = (2.85, 9.32)


def build_lounge_chair(api):
    box, tube = api['box'], api['tube']
    c, s = math.cos(ANGLE), math.sin(ANGLE)
    def point(u, v, z):
        return (CENTER[0] + c*u - s*v, CENTER[1] + s*u + c*v, z)
    def rail(name, points, radius=.018):
        return tube('休闲椅' + name, [point(*p) for p in points], radius, room='living')
    def pad(name, v, z, size, bevel, lean=0, material='green'):
        o = box('休闲椅' + name, point(0,v,z), size, material,
                'Furniture','living',bevel,ANGLE)
        o.rotation_euler.x = -lean
        return o
    # Seat platform carries the cushion; no steel tube runs through upholstery.
    pad('坐垫',-.04,.445,(.72,.76,.14),.06)
    pad('坐垫底托',-.04,.362,(.74,.78,.024),.012,material='steel')
    pad('靠背',.34+.325*math.sin(LEAN),.54+.325*math.cos(LEAN),
        (.74,.12,.65),.055,LEAN)
    # Two side frames stay outside the cushions; feet sit on the finished floor.
    for side, u in [('左',-.395),('右',.395)]:
        rail(side+'椅脚',[(u,-.35,.019),(u,-.35,.333),
                        (u,.38,.333),(u,.43,.019)])
        rail(side+'靠背支撑',[(u,.38,.333),(u,.445,.52),
                            (u,.445+.64*math.sin(LEAN),.52+.64*math.cos(LEAN))])
    for side,v in [('前',-.29),('后',.25)]:
        rail(side+'座下横撑',[(-.395,v,.333),(.395,v,.333)])
    for label,z in [('下',.64),('上',1.08)]:
        v=.445+(z-.52)*math.tan(LEAN)
        rail(label+'背后横撑',[(-.395,v,z),(.395,v,z)])
    # Short mounting pads meet the back from behind, never cross its front face.
    for u in (-.27,.27):
        for z in (.64,1.08):
            v=.445+(z-.52)*math.tan(LEAN)
            rear=.34+(z-.54)*math.tan(LEAN)+.06/math.cos(LEAN)
            rail('靠背连接件',[(u,v,z),(u,rear-.003,z)],.012)


def repair_lounge(api):
    import bpy
    for o in list(bpy.data.objects):
        if o.name.startswith('休闲椅'):
            bpy.data.objects.remove(o,do_unlink=True)
    build_lounge_chair(api)
    for name in ('休闲边几','休闲边几柱'):
        o=bpy.data.objects[name]
        o.location.x,o.location.y=TABLE_CENTER
