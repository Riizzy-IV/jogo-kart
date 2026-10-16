# Renderiza corpo inteiro e rosto de cada .glb para conferir o resultado.
# Uso: blender -b -P preview.py -- <pasta_saida> <arquivo1.glb> [arquivo2.glb ...]
import bpy, sys, os
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
dst, arquivos = args[0], args[1:]
os.makedirs(dst, exist_ok=True)

for caminho in arquivos:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=caminho)
    malhas = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in malhas for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centro, altura = (mn + mx) / 2, mx.z - mn.z

    cena = bpy.context.scene
    cena.render.engine = "BLENDER_WORKBENCH"
    cena.display.shading.light = "FLAT"
    cena.display.shading.color_type = "TEXTURE"
    cena.render.resolution_x, cena.render.resolution_y = 600, 800

    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cena.collection.objects.link(cam)
    cena.camera = cam
    cam.rotation_euler = (1.5708, 0, 0)  # olhando para +Y (frente do glTF fica em -Y)

    base = os.path.splitext(os.path.basename(caminho))[0]
    tag = os.path.basename(os.path.dirname(caminho))
    # (nome, altura do alvo, enquadramento)
    for vista, z, tamanho in (("corpo", centro.z, altura * 1.1),
                              ("rosto", mx.z - altura * 0.07, altura * 0.18)):
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = tamanho
        cam.location = (centro.x, mn.y - altura * 2, z)
        cena.render.filepath = os.path.join(dst, f"{base}_{tag}_{vista}.png")
        bpy.ops.render.render(write_still=True)
