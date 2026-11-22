from pathlib import Path
import json
import math
import struct
import sys

import bpy
import bmesh
from mathutils import Vector


OUT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(OUT / "scripts"))
from designs import VARIANTS, parts_for
MM = 0.001
DRAFT = "--draft" in sys.argv


def linear(channel):
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def material(name, hex_color, roughness, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    rgb = [(hex_color >> shift & 255) / 255 for shift in (16, 8, 0)]
    rgba = tuple(linear(value) for value in rgb) + (1,)
    mat.diffuse_color = rgba
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["IOR"].default_value = 1.46
    if not metallic:
        bsdf.inputs["Coat Weight"].default_value = 0.08
        bsdf.inputs["Coat Roughness"].default_value = 0.27
    return mat


def mesh_from_stl(path, name, mat, parent):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + 50 * count
    vertices, faces = [], []
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        start = len(vertices)
        for offset in (3, 6, 9):
            vertices.append(tuple(value * MM for value in values[offset:offset + 3]))
        faces.append((start, start + 1, start + 2))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    editable = bmesh.new()
    editable.from_mesh(mesh)
    bmesh.ops.remove_doubles(editable, verts=list(editable.verts), dist=1e-9)
    editable.to_mesh(mesh)
    editable.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    obj["viewer_role"] = "body"
    return obj


def tube(name, points, radius, mat, parent, cyclic=False):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = radius * MM
    curve.bevel_resolution = 4
    curve.resolution_u = 16
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for vertex, point in zip(spline.points, points):
        vertex.co = tuple(value * MM for value in point) + (1,)
    spline.use_cyclic_u = cyclic
    curve.use_fill_caps = True
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj.parent = parent
    obj["viewer_role"] = "hardware"
    return obj


def smooth_loop(points):
    nodes = [Vector(point) for point in points]
    result = []
    for index in range(len(nodes)):
        a, b, c, d = [nodes[(index + offset) % len(nodes)] for offset in (-1, 0, 1, 2)]
        for step in range(32):
            t = step / 32
            result.append(0.5 * ((2 * b) + (-a + c) * t
                                + (2 * a - 5 * b + 4 * c - d) * t * t
                                + (-a + 3 * b - 3 * c + d) * t * t * t))
    return result


def ball_path():
    nodes = [(0, 17, -3), (0, 17, 0), (0, 17, 2.5), (0, 17, 5), (0, 17, 8),
             (3, 24, 9), (13, 43, 9), (11, 64, 5), (0, 69, 2.5),
             (-11, 64, 0), (-13, 43, -4), (-3, 24, -4)]
    low, high = 0.4, 1.4
    for _ in range(40):
        scale = (low + high) / 2
        path = smooth_loop([(x, 17 + (y - 17) * scale, z) for x, y, z in nodes])
        length = sum((path[(i + 1) % len(path)] - point).length for i, point in enumerate(path))
        if length < 120:
            low = scale
        else:
            high = scale
    distances = [0.0]
    closed = path + [path[0]]
    for a, b in zip(closed, closed[1:]):
        distances.append(distances[-1] + (b - a).length)
    evenly_spaced = []
    segment = 0
    for index in range(40):
        distance = index * distances[-1] / 40
        while distances[segment + 1] < distance:
            segment += 1
        fraction = (distance - distances[segment]) / (distances[segment + 1] - distances[segment])
        evenly_spaced.append(closed[segment].lerp(closed[segment + 1], fraction))
    return path, evenly_spaced


def sphere(name, point, radius, mat, parent):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=16, ring_count=8, radius=radius * MM,
        location=tuple(value * MM for value in point),
    )
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.data.materials.append(mat)
    obj["viewer_role"] = "hardware"
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def ball_chain(parent, mat):
    path, beads = ball_path()
    tube("Ball chain / connecting wire (approximate)", path, 0.24, mat, parent, cyclic=True)
    connector_index = max(range(len(beads)), key=lambda index: beads[index].y)
    for index, point in enumerate(beads):
        if index in {connector_index, (connector_index + 1) % len(beads)}:
            continue
        sphere(f"Ball chain / 2.4 mm ball {index + 1:02}", point, 1.2, mat, parent)
    a, b = beads[connector_index], beads[(connector_index + 1) % len(beads)]
    tube("Ball chain / connector (approximate)", [a, b], 1.35, mat, parent)
    sphere("Ball chain / connector end A", a, 1.35, mat, parent)
    sphere("Ball chain / connector end B", b, 1.35, mat, parent)


def ellipse(name, center, radii, mat, parent, wire=0.45, yz=False):
    points = []
    for index in range(96):
        theta = index * 2 * math.pi / 96
        a, b = radii[0] * math.cos(theta), radii[1] * math.sin(theta)
        offset = (0, a, b) if yz else (a, b, 0)
        points.append(tuple(center[i] + offset[i] for i in range(3)))
    return tube(name, points, wire, mat, parent, cyclic=True)


def swivel_clasp(parent, mat):
    ellipse("Clasp / lower ring (fit unverified)", (0, 21, 2.5), (4.3, 4.3), mat, parent, yz=True)
    ellipse("Clasp / lower swivel eye", (0, 27, 2.5), (1.65, 3), mat, parent)
    tube("Clasp / swivel barrel", [(0, 29.3, 2.5), (0, 32.3, 2.5)], 1.65, mat, parent)
    ellipse("Clasp / upper swivel eye", (0, 33.1, 2.5), (1.7, 2.3), mat, parent)
    ellipse("Clasp / upper jump ring", (0, 36.7, 2.5), (2.3, 2.3), mat, parent, yz=True)
    points = []
    for index in range(160):
        theta = math.radians(220 + 280 * index / 159)
        points.append((7.8 * math.cos(theta), 47.8 + 9.5 * math.sin(theta), 2.5))
    body = tube("Clasp / rounded open frame", points, 1.15, mat, parent)
    # Flatten only the metal reference frame, never the printable model.
    for point in body.data.splines[0].points:
        point.co.z = 0
    body.scale.z = 0.65
    body.location.z = 2.5 * MM
    gate = [points[0], (-6.5, 44.4, 2.7), (-6.4, 53.4, 2.7), points[-1]]
    tube("Clasp / one-touch wire gate", gate, 0.3, mat, parent)
    ellipse("Clasp / bottom attachment eye", (0, 39, 2.5), (1.9, 2.1), mat, parent, wire=0.65)


def hardware(parent, mat):
    before = set(parent.children)
    ball_chain(parent, mat)
    for obj in set(parent.children) - before:
        obj["hardware_kind"] = "ball"
    before = set(parent.children)
    swivel_clasp(parent, mat)
    for obj in set(parent.children) - before:
        obj["hardware_kind"] = "clasp"
        obj.hide_render = True


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area(name, location, energy, size, target):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
white = material("Printed white", 0xF5F4ED, 0.32)
black = material("Printed black", 0x181818, 0.32)
green = material("Printed green", 0x238636, 0.32)
light_green = material("Printed light green", 0x9DD96C, 0.32)
red = material("Printed red", 0xB33220, 0.32)
metal = material("Purchased metal / illustrative finish", 0xBAC0C1, 0.23, metallic=1)
ground = material("Warm studio ground", 0xEEEFE8, 0.8)

for index, (variant, _, _) in enumerate(VARIANTS.values()):
    report = json.loads((OUT / "validation" / f"validation-{variant}.json").read_text())
    parent = bpy.data.objects.new(f"Keychain {index + 1} - {variant}", None)
    bpy.context.collection.objects.link(parent)
    parent.location = ((index - (len(VARIANTS) - 1) / 2) * 36 * MM, 0, 0)
    parent.rotation_euler.z = math.radians([4, 0, -4, -5, 2, -2][index])
    parts = parts_for(variant)
    for part in parts:
        mat = white if part == "white_body" else light_green if part == "light_inlay" else (green if part == "inlay" and variant not in {"octocat", "haku"} else black)
        if variant == "chun" and part == "inlay":
            mat = red
        mesh_from_stl(OUT / report["parts"][part]["file"], f"{variant}/{part}", mat, parent)
    hardware(parent, metal)

bpy.ops.mesh.primitive_plane_add(size=2000 * MM, location=(0, 0, -7 * MM))
bpy.context.object.name = "Studio ground"
bpy.context.object.data.materials.append(ground)

camera_data = bpy.data.cameras.new("Camera")
camera = bpy.data.objects.new("Camera", camera_data)
bpy.context.collection.objects.link(camera)
camera.location = (0, -48 * MM, 210 * MM)
aim(camera, (0, 22 * MM, 5 * MM))
camera.data.type = "ORTHO"
camera.data.ortho_scale = 240 * MM
camera.data.lens = 60
camera.data.clip_start = 0.001
camera.data.clip_end = 10

area("Large softbox", (-65 * MM, -35 * MM, 180 * MM), 0.078, 150 * MM, (0, 20 * MM, 0))
area("Fill softbox", (100 * MM, 20 * MM, 110 * MM), 0.039, 130 * MM, (0, 20 * MM, 0))
area("Rim softbox", (5 * MM, 135 * MM, 140 * MM), 0.062, 110 * MM, (0, 30 * MM, 0))

scene = bpy.context.scene
scene.camera = camera
scene.unit_settings.system = "METRIC"
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 16 if DRAFT else 48
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.render.threads_mode = "FIXED"
scene.render.threads = 4
scene.render.resolution_x = 3000
scene.render.resolution_y = 2300
scene.render.resolution_percentage = 50 if DRAFT else 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.film_transparent = False
scene.render.filepath = str(OUT / "docs" / "images" / "keychains-studio.png")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.65
scene.render.image_settings.color_depth = "8"
scene.render.use_stamp_filename = False
scene.render.use_stamp_hostname = False
(OUT / ".work").mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / ".work" / "keychain-studio.blend"))
bpy.ops.render.render(write_still=True)
print("Rendered all six exact STL assemblies with the unchanged 120 mm ball-chain reference.")
