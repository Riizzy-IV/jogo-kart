# Confere um .fbx do Mixamo: esqueleto, animacao, malha, UVs. Reaplica o material do .glb
# original (cores) e renderiza alguns quadros da animacao.
# Uso: blender -b -P conferir_mixamo.py -- <mixamo.fbx> <personagem.glb> <pasta_saida>
import bpy, sys, os
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
fbx, glb, dst = args[0], args[1], args[2]
os.makedirs(dst, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
malha = next(o for o in bpy.context.scene.objects if o.type == "MESH")
acao = arm.animation_data.action if arm.animation_data else None
tris = sum(len(p.vertices) - 2 for p in malha.data.polygons)
print(f"[mixamo] ossos: {len(arm.data.bones)} | raiz: {arm.data.bones[0].name}")
print(f"[mixamo] malha: {malha.name} {tris} triangulos | UVs: {len(malha.data.uv_layers)} | "
      f"materiais: {[m.name if m else None for m in malha.data.materials]}")
if acao:
    ini, fim = acao.frame_range
    print(f"[mixamo] animacao: {acao.name} quadros {int(ini)}-{int(fim)}")
else:
    print("[mixamo] SEM animacao")
print(f"[mixamo] escala do objeto: {tuple(round(s, 3) for s in arm.scale)}")

# Material com cores do .glb original
antes = set(bpy.data.materials)
bpy.ops.import_scene.gltf(filepath=glb)
mat = next(iter(set(bpy.data.materials) - antes))
for o in [o for o in bpy.context.scene.objects if o.type == "MESH" and o != malha]:
    bpy.data.objects.remove(o)
malha.data.materials.clear()
malha.data.materials.append(mat)

cena = bpy.context.scene
cena.render.engine = "BLENDER_WORKBENCH"
cena.display.shading.light = "STUDIO"
cena.display.shading.color_type = "TEXTURE"
cena.render.resolution_x, cena.render.resolution_y = 700, 700
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cena.collection.objects.link(cam)
cena.camera = cam
cam.data.type = "ORTHO"

base = os.path.splitext(os.path.basename(fbx))[0]
quadros = [int(acao.frame_range[0]), int(sum(acao.frame_range) / 2)] if acao else [1]
for q in quadros:
    cena.frame_set(q)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = malha.evaluated_get(dg)
    pts = [ev.matrix_world @ v.co for v in ev.data.vertices]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c, tam = (mn + mx) / 2, max(mx - mn)
    if q == quadros[0]:
        print(f"[mixamo] altura no quadro {q}: {mx.z - mn.z:.3f} m")
    cam.data.ortho_scale = tam * 1.2
    cam.location = (c.x + tam * 2, c.y - tam * 2, c.z + tam * 0.8)
    cam.rotation_euler = (1.32, 0, 0.785)
    cena.render.filepath = os.path.join(dst, f"{base}_q{q}.png")
    bpy.ops.render.render(write_still=True)
