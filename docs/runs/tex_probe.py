import bpy, colorsys, collections
bpy.ops.wm.open_mainfile(filepath=r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
ob=bpy.data.objects["Wukong_LOD0"]; me=ob.data
mat=me.materials[0]
imgs=[n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
print("images:", [(i.name, i.size[0], i.size[1]) for i in imgs])
for i in imgs:
    print(" ", i.name, "colorspace", i.colorspace_settings.name)
