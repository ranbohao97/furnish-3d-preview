"""Batch repeated finishes while retaining room/category visibility metadata."""
def batch_finishes(bpy):
    for cat in ('Floor','BathroomWalls'):
        buckets={}
        for o in list(bpy.data.objects):
            if o.type=='MESH' and o.get('category')==cat:
                key=(o.get('room','shared'),tuple(m.name for m in o.data.materials))
                buckets.setdefault(key,[]).append(o)
        for (room,mats),objects in buckets.items():
            if len(objects)<2:continue
            bpy.ops.object.select_all(action='DESELECT')
            for o in objects:
                bpy.context.view_layer.objects.active=o
                for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
                o.select_set(True)
            bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join()
            o=objects[0];o.name=cat+'_'+room+'_'+mats[0];o['source']='Batched CAD floor/finish geometry'
