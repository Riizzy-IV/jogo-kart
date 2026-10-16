# Salva as texturas de cada .glb como PNG (para reaplicar na Unreal se o Mixamo perder as cores).
# Uso: blender -b -P extrair_texturas.py -- <pasta_saida> <arquivo1.glb> [arquivo2.glb ...]
import bpy, sys, os

args = sys.argv[sys.argv.index("--") + 1:]
dst, arquivos = args[0], args[1:]
os.makedirs(dst, exist_ok=True)

for caminho in arquivos:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=caminho)
    base = os.path.splitext(os.path.basename(caminho))[0]
    for i, img in enumerate(i for i in bpy.data.images if i.has_data or i.packed_file):
        sufixo = "" if i == 0 else f"_{i}"
        img.filepath_raw = os.path.join(dst, f"{base}{sufixo}.png")
        img.file_format = "PNG"
        img.save()
        print(f"[texturas] {base}{sufixo}.png {img.size[0]}x{img.size[1]}")
