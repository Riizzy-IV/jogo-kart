# Prepara o buggy para o Chaos Vehicle da Unreal:
# separa as 4 rodas, reduz os poligonos, coloca a frente em +X, ajusta a escala
# e cria um esqueleto com osso raiz + 4 ossos de roda. Exporta .fbx, .glb e .blend.
# Uso: blender -b -P preparar_carro.py -- <carro.glb> <pasta_saida> [comprimento_m] [tris_carroceria] [tris_roda]
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix

args = sys.argv[sys.argv.index("--") + 1:]
src, dst = args[0], args[1]
comprimento = float(args[2]) if len(args) > 2 else 3.0
ALVO_CARROCERIA = int(args[3]) if len(args) > 3 else 400000
ALVO_RODA = int(args[4]) if len(args) > 4 else 40000
os.makedirs(dst, exist_ok=True)

# Rodas no arquivo original (frente em -X): centro X por eixo, centro Z, raio e |Y| minimo
EIXOS = {"F": -0.337, "R": 0.2815}
CENTRO_Z, RAIO, Y_MIN = 0.115, 0.125, 0.17

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
corpo = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
corpo.name = corpo.data.name = "Carroceria"
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = corpo
corpo.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def roda_de(co):
    """Retorna o nome da roda que contem o ponto, ou None."""
    if abs(co.y) < Y_MIN:
        return None
    for eixo, cx in EIXOS.items():
        if math.hypot(co.x - cx, co.z - CENTRO_Z) <= RAIO:
            lado = "L" if co.y < 0 else "R"  # vira esquerda/direita depois do giro de 180
            return f"wheel_{eixo}{lado}".lower()
    return None

# Agrupa as pecas soltas inteiramente dentro de cada roda
bpy.ops.object.mode_set(mode="EDIT")
bm = bmesh.from_edit_mesh(corpo.data)
bm.verts.ensure_lookup_table()
visto, por_roda = set(), {}
for v in bm.verts:
    if v.index in visto:
        continue
    pilha, ilha = [v], []
    visto.add(v.index)
    while pilha:
        a = pilha.pop()
        ilha.append(a)
        for e in a.link_edges:
            b = e.other_vert(a)
            if b.index not in visto:
                visto.add(b.index)
                pilha.append(b)
    nomes = {roda_de(x.co) for x in ilha}
    if len(nomes) == 1 and None not in nomes:
        por_roda.setdefault(nomes.pop(), []).extend(x.index for x in ilha)

# Marca cada vertice com o numero da roda (a marca sobrevive aos separates)
camada = bm.verts.layers.int.new("roda")
bm.verts.ensure_lookup_table()
nomes_roda = sorted(por_roda)
for i, nome in enumerate(nomes_roda, 1):
    for idx in por_roda[nome]:
        bm.verts[idx][camada] = i

rodas = {}
for i, nome in enumerate(nomes_roda, 1):
    camada = bm.verts.layers.int["roda"]
    for f in bm.faces:
        f.select = False
    for x in bm.verts:
        x.select = x[camada] == i
    bm.select_flush(True)
    verts = [x for x in bm.verts if x.select]
    bmesh.update_edit_mesh(corpo.data)
    antes = set(bpy.data.objects)
    bpy.ops.mesh.separate(type="SELECTED")
    nova = (set(bpy.data.objects) - antes).pop()
    nova.name = nova.data.name = nome
    rodas[nome] = nova
    bm = bmesh.from_edit_mesh(corpo.data)
    bm.verts.ensure_lookup_table()
    print(f"[carro] {nome}: {len(verts)} vertices separados")
bpy.ops.object.mode_set(mode="OBJECT")

# Frente em +X (padrao Unreal), apoiado no chao e na escala final
objs = [corpo] + list(rodas.values())
pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
tam_x = max(p.x for p in pts) - min(p.x for p in pts)
s = comprimento / tam_x
centro_x = (max(p.x for p in pts) + min(p.x for p in pts)) / 2
min_z = min(p.z for p in pts)
xf = Matrix.Scale(s, 4) @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Translation((-centro_x, 0, -min_z))
for o in objs:
    o.data.transform(xf)
    o.data.update()

def reduzir(o, alvo):
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    m = o.modifiers.new("Decimate", "DECIMATE")
    m.ratio = min(1.0, alvo / max(tris, 1))
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=m.name)
    print(f"[carro] {o.name}: {tris} -> {sum(len(p.vertices) - 2 for p in o.data.polygons)} triangulos")

reduzir(corpo, ALVO_CARROCERIA)
for r in rodas.values():
    reduzir(r, ALVO_RODA)

# Esqueleto: raiz no chao + um osso por roda no centro do pneu
arm_data = bpy.data.armatures.new("Armature")
arm = bpy.data.objects.new("Armature", arm_data)  # nome "Armature" evita osso extra na Unreal
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
raiz = arm_data.edit_bones.new("root")
raiz.head, raiz.tail = (0, 0, 0), (0, 0, 0.3)
centros = {}
for nome, r in rodas.items():
    c = sum((Vector(v.co) for v in r.data.vertices), Vector()) / len(r.data.vertices)
    vs = [v.co for v in r.data.vertices]
    c = Vector(((max(v.x for v in vs) + min(v.x for v in vs)) / 2,
                (max(v.y for v in vs) + min(v.y for v in vs)) / 2,
                (max(v.z for v in vs) + min(v.z for v in vs)) / 2))
    raio = (max(v.z for v in vs) - min(v.z for v in vs)) / 2
    centros[nome] = (c, raio)
    b = arm_data.edit_bones.new(nome)
    b.head, b.tail, b.parent = c, c + Vector((0, 0, 0.15)), raiz
bpy.ops.object.mode_set(mode="OBJECT")

# Pesa cada malha 100% no seu osso e junta tudo numa malha so
for o, osso in [(corpo, "root")] + [(r, n) for n, r in rodas.items()]:
    g = o.vertex_groups.new(name=osso)
    g.add(range(len(o.data.vertices)), 1.0, "REPLACE")
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = corpo
bpy.ops.object.join()
corpo.name = corpo.data.name = "SK_Buggy"
corpo.parent = arm
mod = corpo.modifiers.new("Armature", "ARMATURE")
mod.object = arm

for nome, (c, raio) in sorted(centros.items()):
    print(f"[carro] osso {nome}: centro=({c.x:+.3f},{c.y:+.3f},{c.z:+.3f}) m  raio={raio*100:.1f} cm")
pts = [Vector(c) for c in corpo.bound_box]
print(f"[carro] tamanho final: {max(p.x for p in pts)-min(p.x for p in pts):.2f} x "
      f"{max(p.y for p in pts)-min(p.y for p in pts):.2f} x {max(p.z for p in pts)-min(p.z for p in pts):.2f} m")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.fbx(filepath=os.path.join(dst, "SK_Buggy.fbx"), use_selection=True,
                         object_types={"ARMATURE", "MESH"}, add_leaf_bones=False,
                         bake_anim=False, path_mode="COPY", embed_textures=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(dst, "SK_Buggy.glb"), export_format="GLB")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(dst, "SK_Buggy.blend"))
