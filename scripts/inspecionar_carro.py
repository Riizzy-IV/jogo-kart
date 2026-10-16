# Mostra dimensoes, pecas soltas e renderiza 4 vistas do carro.
# Uso: blender -b -P inspecionar_carro.py -- <arquivo.glb> <pasta_saida>
import bpy, bmesh, sys, os
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
caminho, dst = args[0], args[1]
os.makedirs(dst, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=caminho)
obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]

pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
tam = mx - mn
print(f"[carro] dimensoes X={tam.x:.3f} Y={tam.y:.3f} Z={tam.z:.3f}")

bm = bmesh.new()
bm.from_mesh(obj.data)
bm.verts.ensure_lookup_table()
visto, ilhas = set(), []
for v in bm.verts:
    if v.index in visto:
        continue
    pilha, n = [v], 0
    visto.add(v.index)
    while pilha:
        a = pilha.pop()
        n += 1
        for e in a.link_edges:
            b = e.other_vert(a)
            if b.index not in visto:
                visto.add(b.index)
                pilha.append(b)
    ilhas.append(n)
ilhas.sort(reverse=True)
print(f"[carro] pecas soltas: {len(ilhas)} | maiores (vertices): {ilhas[:10]}")

cena = bpy.context.scene
cena.render.engine = "BLENDER_WORKBENCH"
cena.display.shading.light = "STUDIO"
cena.display.shading.color_type = "TEXTURE"
cena.render.resolution_x, cena.render.resolution_y = 800, 600
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cena.collection.objects.link(cam)
cena.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = max(tam) * 1.15
c = (mn + mx) / 2
d = max(tam) * 3
vistas = {
    "frente": ((c.x, mn.y - d, c.z), (1.5708, 0, 0)),
    "lado": ((mx.x + d, c.y, c.z), (1.5708, 0, 1.5708)),
    "cima": ((c.x, c.y, mx.z + d), (0, 0, 0)),
    "diagonal": ((c.x + d * 0.6, c.y - d * 0.6, c.z + d * 0.5), (1.1, 0, 0.785)),
}
for nome, (loc, rot) in vistas.items():
    cam.location, cam.rotation_euler = loc, rot
    cena.render.filepath = os.path.join(dst, f"carro_{nome}.png")
    bpy.ops.render.render(write_still=True)
