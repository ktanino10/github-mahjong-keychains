"""Inspect the final sliced face, using actual extrusion paths and saved line widths."""

from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
import trimesh

from package_models import CORE, ROOT, project_materials, slot_for
from validate_projects import transform


SCALE = 40
SIZE = (880, 1160)
font = ImageFont.truetype(str(ROOT / "viewer/assets/fonts/DMMono-Regular.ttf"), 20)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--only", nargs="+", choices=("haku", "iisou"), default=["haku", "iisou"])
args = parser.parse_args()


def top_extrusions(gcode):
    xy = np.zeros(2)
    z = 0.0
    layer = tool = width = feature = object_id = None
    relative_e = False
    paths = []
    for line in gcode.splitlines():
        if line.startswith("; layer num/total_layer_count: "):
            layer = int(line.split(": ", 1)[1].split("/")[0])
        elif line.startswith("; LINE_WIDTH: "):
            width = float(line.split(": ", 1)[1])
        elif line.startswith("; FEATURE: "):
            feature = line.split(": ", 1)[1]
        elif line.startswith("; OBJECT_ID: "):
            object_id = int(line.split(": ", 1)[1])
        command = line.split(";", 1)[0].strip()
        if command == "M83":
            relative_e = True
        elif command == "M82":
            relative_e = False
        match = re.fullmatch(r"T(\d+)", command)
        if match and int(match[1]) not in {255, 1000}:
            tool = int(match[1]) + 1
        match = re.match(r"G([123])(?: |$)", command)
        if not match:
            continue
        values = {key: float(value) for key, value in re.findall(r"([XYZIJE])(-?(?:\d+(?:\.\d*)?|\.\d+))", command)}
        end = np.array([values.get("X", xy[0]), values.get("Y", xy[1])])
        z = values.get("Z", z)
        if (layer == 165 and object_id and feature not in {None, "Custom", "Prime tower"}
                and values.get("E", 0) > 0 and ("X" in values or "Y" in values) and abs(z - 16.5) < 0.001):
            assert relative_e and width is not None and tool is not None
            if match[1] == "1":
                points = np.array([xy, end])
            else:
                assert "I" in values and "J" in values, "Unexpected non-XY arc."
                center = xy + [values["I"], values["J"]]
                radius = np.linalg.norm(xy - center)
                start_angle = math.atan2(*(xy - center)[::-1])
                end_angle = math.atan2(*(end - center)[::-1])
                sweep = ((end_angle - start_angle) % (2 * math.pi) if match[1] == "3"
                         else -((start_angle - end_angle) % (2 * math.pi)))
                steps = max(2, math.ceil(abs(sweep) * radius / 0.02))
                angles = np.linspace(start_angle, start_angle + sweep, steps)
                points = center + radius * np.column_stack((np.cos(angles), np.sin(angles)))
                points[-1] = end
            paths.append((points, width, tool))
        xy = end
    assert paths, "No actual final-layer object extrusions were found."
    return paths


def pixel(point):
    return (point[0] + 11) * SCALE, (14.5 - point[1]) * SCALE


def section_mask(mesh):
    lines = trimesh.intersections.mesh_plane(mesh, [0, 0, 1], [0, 0, 16.1])
    result = np.zeros((SIZE[1], SIZE[0]), dtype=bool)
    for loop in trimesh.load_path(lines).discrete:
        layer = Image.new("1", SIZE)
        ImageDraw.Draw(layer).polygon([pixel(point) for point in loop], fill=1)
        result ^= np.asarray(layer)
    return result


reports = []
for variant in args.only:
    project = ROOT / "print-package/projects" / f"{variant}-P1S-0.2-AMS-PLA.3mf"
    sliced = ROOT / ".work/verification" / variant / "output/sliced.3mf"
    with zipfile.ZipFile(project) as archive:
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        items = model.findall(f"{{{CORE}}}build/{{{CORE}}}item")
        assert len(items) == 1
        config = json.loads(archive.read("Metadata/project_settings.config"))
        assert len(config["extruder_offset"]) == 1
        nozzle_offset = np.array([float(value) for value in config["extruder_offset"][0].split("x")])
        origin = transform(items[0].get("transform"))[:2, 3] - nozzle_offset
    with zipfile.ZipFile(sliced) as archive:
        gcode = archive.read("Metadata/plate_1.gcode")
    paths = top_extrusions(gcode.decode("utf-8"))
    palette, _ = project_materials([variant])
    actual = {slot: Image.new("1", SIZE) for slot in range(1, len(palette) + 1)}
    drawing = Image.new("RGB", SIZE, "#DDE8E2")
    visible_paths = 0
    for points, width, slot in paths:
        points = points - origin
        if np.max(points[:, 0]) < -10.6 or np.min(points[:, 0]) > 10.6 or np.max(points[:, 1]) < -14.1 or np.min(points[:, 1]) > 14.1:
            continue
        assert slot in actual
        pixels = [pixel(point) for point in points]
        thickness = max(1, round(width * SCALE))
        for image, color in [(actual[slot], 1), (drawing, palette[slot - 1][1])]:
            draw = ImageDraw.Draw(image)
            draw.line(pixels, fill=color, width=thickness, joint="curve")
            radius = thickness / 2
            for x, y in (pixels[0], pixels[-1]):
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
        visible_paths += 1
    report = json.loads((ROOT / "validation" / f"validation-{variant}.json").read_text())
    inlay = trimesh.load_mesh(ROOT / report["parts"]["inlay"]["file"], process=True)
    ink_slot = slot_for(variant, "inlay")
    actual_ink = np.asarray(actual[ink_slot])
    coverage = []
    missed_core_area = []
    for component in inlay.split():
        core = ndimage.binary_erosion(section_mask(component), iterations=4)
        assert core.any(), "An inlay component has no printable 0.2 mm-wide core."
        ratio = np.count_nonzero(core & actual_ink) / np.count_nonzero(core)
        coverage.append(float(ratio))
        missed_core_area.append(float(np.count_nonzero(core & ~actual_ink) / SCALE ** 2))
    white = trimesh.load_mesh(ROOT / report["parts"]["white_body"]["file"], process=True)
    white_core = ndimage.binary_erosion(section_mask(white), iterations=6)
    ink_in_white = np.count_nonzero(white_core & actual_ink) / SCALE ** 2
    annotated = Image.new("RGB", (SIZE[0], SIZE[1] + 55), "#DDE8E2")
    annotated.paste(drawing)
    ImageDraw.Draw(annotated).text((SIZE[0] // 2, SIZE[1] + 14), f"{variant} / actual layer 165", fill="#132D27", font=font, anchor="mt")
    annotated.save(ROOT / "docs/images" / f"{variant}-sliced-top.png")
    item = {
        "variant": variant, "layer": 165,
        "project_sha256": hashlib.sha256(project.read_bytes()).hexdigest(),
        "local_gcode_sha256": hashlib.sha256(gcode).hexdigest(),
        "actual_extrusion_paths": visible_paths,
        "saved_stock_nozzle_xy_offset_mm": nozzle_offset.tolist(),
        "inlay_components_checked": len(coverage),
        "component_interior_coverage_ratios": coverage,
        "component_uncovered_core_area_mm2": missed_core_area,
        "colored_footprint_in_eroded_white_area_mm2": float(ink_in_white),
        "method": "Rasterized actual G1/G2/G3 object extrusions with saved LINE_WIDTH; purge/tower/custom excluded. Compare 0.10 mm-eroded inlay cores and 0.15 mm-eroded white spaces at 40 pixels/mm.",
        "scope": "Slicer footprint estimate, not physical bead width or strength validation.",
    }
    reports.append(item)
    print(variant, "core coverage", coverage, "uncovered area", missed_core_area, "ink in white", ink_in_white, "mm2")
    # Width-comment rasterization is an estimate, not a physical bead simulation.
    assert min(coverage) > 0.95 and max(missed_core_area) < 0.1, "A required face detail is missing from the actual toolpaths."
    assert ink_in_white < 0.2, "Colored extrusion closes a required white gap."
    if variant == "haku":
        assert not actual_ink[:int(14.5 * SCALE)].any(), "Haku has black top-layer extrusion above center."
(ROOT / "validation/top-layer-checks.json").write_text(json.dumps(reports, indent=2) + "\n")
print("Verified every inlay component against actual top-layer extrusion; no G-code is published.")
