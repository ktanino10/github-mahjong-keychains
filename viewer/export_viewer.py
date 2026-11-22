from pathlib import Path
import hashlib
import json
import sys

import bpy
from mathutils import Matrix


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from designs import PRINTED_PART_COUNT, VARIANTS
OUT = ROOT / "viewer" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT / ".work" / "keychain-studio.blend"))
variants = [value[0] for value in VARIANTS.values()]
roots = []
printed = []
hardware = []

for index, variant in enumerate(variants):
    parent = bpy.data.objects.get(f"Keychain {index + 1} - {variant}")
    if parent is None:
        raise RuntimeError(f"Missing finished model: {variant}")
    children = list(parent.children)
    parent.name = f"design_{variant}"
    parent.location = (0, 0, 0)
    parent.rotation_euler = (0, 0, 0)
    parent["role"] = "design"
    parent["design"] = variant
    roots.append(parent)
    groups = {}
    for role in ["body", "hardware"]:
        group = bpy.data.objects.new(f"{variant}_{role}", None)
        bpy.context.collection.objects.link(group)
        group.parent = parent
        group["role"] = role
        group["design"] = variant
        groups[role] = group
    options = {}
    for kind in ["ball", "clasp"]:
        group = bpy.data.objects.new(f"{variant}_{kind}", None)
        bpy.context.collection.objects.link(group)
        group.parent = groups["hardware"]
        group["role"] = "hardware_option"
        group["kind"] = kind
        options[kind] = group
    for obj in children:
        is_printed = obj.get("viewer_role") == "body"
        role = "body" if is_printed else "hardware"
        obj.parent = groups[role] if is_printed else options[obj["hardware_kind"]]
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj["role"] = role
        obj["design"] = variant
        if is_printed:
            printed.append(obj)
        elif obj.get("viewer_role") == "hardware" and obj.type in {"CURVE", "MESH"}:
            if obj.type == "CURVE":
                obj.data.bevel_resolution = 2
            hardware.append(obj)
        else:
            raise RuntimeError(f"Unexpected model object: {obj.name}/{obj.type}")

assert len(printed) == PRINTED_PART_COUNT
assert len(hardware) > 18
bpy.ops.object.select_all(action="DESELECT")
curves = [obj for obj in hardware if obj.type == "CURVE"]
for obj in curves:
    obj.select_set(True)
bpy.context.view_layer.objects.active = curves[0]
bpy.ops.object.convert(target="MESH")
for obj in bpy.context.selected_objects:
    for face in obj.data.polygons:
        face.use_smooth = True

bpy.ops.object.select_all(action="DESELECT")
for parent in roots:
    parent.select_set(True)
    for obj in parent.children_recursive:
        obj.select_set(True)
bpy.context.view_layer.objects.active = roots[0]
target = OUT / "keychains.glb"
bpy.ops.export_scene.gltf(
    filepath=str(target),
    export_format="GLB",
    use_selection=True,
    export_yup=False,
    export_animations=False,
    export_cameras=False,
    export_lights=False,
    export_extras=True,
    export_apply=False,
)
assert target.is_file() and target.stat().st_size > 0
metadata = {
    "source": "28 x 21 x 16.5 mm tile bodies and 5 mm ears unchanged. All black/white boundaries share z=5.5 mm; the entire ear is black. Nineteen exact STL-derived parts: thirteen originals, three no-text Haku and three mirrored three-quarter green official-Ducky Iisou with a peacock-inspired tail.",
    "coordinate_system": "X right, Y along keychain, Z toward front; stored in meters.",
    "printed_geometry_modified": False,
    "metal_hardware": "Default: 2.4 mm balls on an approximately 120 mm loop through the unchanged ear. Alternate: purchased round wire-gate swivel-clasp shape. Pitch, connector and clasp internal dimensions are approximate; physical fit and strength untested. No metal in print files.",
    "designs": variants,
    "printed_parts": [obj.name for obj in printed],
    "glb_bytes": target.stat().st_size,
    "glb_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
}
(ROOT / "validation" / "model-manifest.json").write_text(
    json.dumps(metadata, indent=2), encoding="utf-8"
)
print(f"Exported {len(roots)} designs, {len(printed)} exact printed parts and {len(hardware)} reference metal objects.")
print(target)
