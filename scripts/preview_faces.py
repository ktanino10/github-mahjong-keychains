"""Draw a front contact sheet from the actual printable mesh cross sections."""

from pathlib import Path
import argparse
import json
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh

from designs import ADDITIONS, VARIANTS, parts_for


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--only", nargs="+", choices=VARIANTS)
parser.add_argument("--output", type=Path, default=ROOT / "docs/images/new-designs-front.png")
args = parser.parse_args()
SCALE = 16
TILE = (420, 660)
COLORS = {"black_back": "#161616", "white_body": "#F6F5EE", "inlay": "#238636"}
font = ImageFont.truetype(str(ROOT / "viewer/assets/fonts/DMMono-Regular.ttf"), 23)


def face(variant, title):
    image = Image.new("RGB", TILE, "#E5EEE6")
    draw = ImageDraw.Draw(image)
    center = (TILE[0] // 2, 400)

    def pixel(point):
        return center[0] + point[0] * SCALE, center[1] - point[1] * SCALE

    report = json.loads((ROOT / "validation" / f"validation-{variant}.json").read_text())
    draw.ellipse([pixel((-5, 22)), pixel((5, 12))], fill=COLORS["black_back"])
    draw.ellipse([pixel((-2.3, 19.3)), pixel((2.3, 14.7))], fill="#E5EEE6")
    draw.rounded_rectangle([pixel((-10.5, 14)), pixel((10.5, -14))],
                           radius=2.45 * SCALE, fill=COLORS["white_body"])
    for part in parts_for(variant):
        if "inlay" not in part:
            continue
        mesh = trimesh.load_mesh(ROOT / report["parts"][part]["file"], process=True)
        lines = trimesh.intersections.mesh_plane(mesh, [0, 0, 1], [0, 0, 16.1])
        mask = np.zeros((TILE[1], TILE[0]), dtype=bool)
        for loop in trimesh.load_path(lines).discrete:
            layer = Image.new("1", TILE)
            ImageDraw.Draw(layer).polygon([pixel(point) for point in loop], fill=1)
            mask ^= np.asarray(layer)
        color = "#161616" if variant == "haku" and part == "inlay" else COLORS[part]
        image.paste(color, mask=Image.fromarray(mask))
    draw.text((TILE[0] // 2, 640), title, font=font, fill="#132D27", anchor="ms")
    return image


selected = args.only or ADDITIONS
columns = min(3, len(selected))
sheet = Image.new("RGB", (TILE[0] * columns, TILE[1] * math.ceil(len(selected) / columns)), "#E5EEE6")
for index, variant in enumerate(selected):
    sheet.paste(face(variant, variant.capitalize()), (index % columns * TILE[0], index // columns * TILE[1]))
sheet.save(args.output)
face("haku", "Haku / supplied icon").save(ROOT / "docs/images/haku-front.png")
face("iisou", "Iisou / green Ducky").save(ROOT / "docs/images/iisou-front.png")
print("Rendered Haku and front-facing peacock Ducky from STL cross sections.")
