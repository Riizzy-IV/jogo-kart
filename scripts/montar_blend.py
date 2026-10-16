# Junta os personagens .glb lado a lado num .blend pronto para visualizar.
# Uso: blender -b -P montar_blend.py -- <arquivo_saida.blend> <arquivo1.glb> [arquivo2.glb ...]
import bpy, sys
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
saida, arquivos = args[0], args[1:]

bpy.ops.wm.read_homefile(use_empty=True)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)

for i, caminho in enumerate(arquivos):
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=caminho)
    for o in set(bpy.data.objects) - antes:
        if o.parent is None:
            o.location.x += (i - (len(arquivos) - 1) / 2) * 1.0  # 1 m entre eles

pts = [o.matrix_world @ Vector(c) for o in bpy.data.objects if o.type == "MESH" for c in o.bound_box]
centro = sum(pts, Vector()) / len(pts)
largura = max(p.x for p in pts) - min(p.x for p in pts)

for tela in bpy.data.screens:
    for area in tela.areas:
        if area.type == "VIEW_3D":
            esp = area.spaces[0]
            esp.shading.type = "MATERIAL"
            esp.region_3d.view_location = centro
            esp.region_3d.view_distance = max(largura, 2.0) * 1.6

bpy.ops.wm.save_as_mainfile(filepath=saida)
