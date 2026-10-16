# Reduz os personagens .glb para uso em jogo e exporta .fbx (para Mixamo) e .glb leve.
# Uso: blender -b -P decimar.py -- <pasta_entrada> <pasta_saida> [alvo_triangulos]
import bpy, sys, os

args = sys.argv[sys.argv.index("--") + 1:]
src, dst = args[0], args[1]
alvo = int(args[2]) if len(args) > 2 else 30000
os.makedirs(dst, exist_ok=True)

for nome in sorted(os.listdir(src)):
    if not nome.lower().endswith(".glb"):
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(src, nome))

    for obj in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        mod = obj.modifiers.new("Decimate", "DECIMATE")
        mod.ratio = min(1.0, alvo / max(tris, 1))
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        novos = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        print(f"[decimar] {nome}: {tris} -> {novos} triangulos")

    base = os.path.splitext(nome)[0]
    bpy.ops.export_scene.gltf(filepath=os.path.join(dst, base + ".glb"), export_format="GLB")
    bpy.ops.export_scene.fbx(filepath=os.path.join(dst, base + ".fbx"),
                             path_mode="COPY", embed_textures=True)
