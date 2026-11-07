"""Living-area colour study: warm timber, lacquer and restrained colour blocks.

Only material slots change; room geometry, glazing and metal hardware stay intact.
Apply after construction_details, both for fresh builds and saved-scene exports.
"""

PALETTE = {
    'cream': ('客厅暖米白漆面', 'E6E0D0', .55),
    'red': ('餐边红棕漆面', '914638', .47),
    'sage': ('手工灰橄榄绿漆面', '7D876E', .55),
    'ink': ('门框深石墨绿漆面', '354239', .43),
}


def apply_living_palette(bpy):
    def linear(v):return v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4
    mats={}
    for key,(name,colour,rough) in PALETTE.items():
        m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes=True
        rgb=tuple(int(colour[i:i+2],16)/255 for i in (0,2,4))
        m.diffuse_color=(*rgb,1)
        bsdf=m.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value=(*map(linear,rgb),1)
        bsdf.inputs['Roughness'].default_value=rough
        mats[key]=m
    # A separate copy preserves the existing floor material and packed wood grain.
    mats['wood']=bpy.data.materials.get('客厅浅蜜木色')
    if mats['wood'] is None:
        mats['wood']=bpy.data.materials['温润橡木地板'].copy()
        mats['wood'].name='客厅浅蜜木色'
        mats['wood'].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.48
    changes=[]
    for o in bpy.data.objects:
        if o.type not in ('MESH','CURVE'):continue
        n=o.name;cat=o.get('category');key=None
        if any(t in n for t in ('拉手','把手','铰链','挂钩','孔','层板墙托')):continue
        if cat=='Storage' and n.startswith('玄关') and '常穿鞋'not in n:
            key='wood' if n.startswith(('玄关钥匙台','玄关挂物洞洞板')) or ('玄关换鞋凳抽屉'in n and '抽屉面'in n) else 'cream'
        if n.startswith('餐边展示下柜'):
            key='red' if any(t in n for t in ('抽屉面','侧板','内退踢脚','踢脚端回板')) else 'wood'
        elif n.startswith(('餐边玻璃展示柜','餐边工作台','餐边开放层板','餐边柜层间收口')):
            if not n.startswith('餐边玻璃展示柜柜门'):key='wood'
        if n.startswith('手工小吊柜'):key='sage' if '柜门'in n or '侧板'in n else 'wood'
        if n.startswith(('手工线轴架层板','手工桌桌面','手工桌背挡','手工桌侧腿','手工桌工具挂板')):key='wood'
        if n.startswith(('储物间封闭柜门','储物间柜门框')):key='cream'
        if cat=='Doors' and n.startswith(('主卧双门门套','主卧双门上门套','主卧玻璃门边框','主卧玻璃门横框','主卧双门中缝盖条')):key='ink'
        if cat=='Doors' and n.startswith('次卧门'):key='wood'
        if cat=='Doors' and n.startswith('客卫平开门'):key='cream'
        if key:
            if o.data.users>1:o.data=o.data.copy()
            o.data.materials.clear();o.data.materials.append(mats[key])
            o['colour_scheme']='Living / Mid-century Bauhaus + Aalto / v12.4'
            changes.append({'object':n,'material':mats[key].name})
    bpy.context.scene['Palette_revision']='v12.4 / Living Mid-century Bauhaus + Aalto'
    return changes
