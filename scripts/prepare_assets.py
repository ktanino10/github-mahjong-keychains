"""Extract the Invertocat's white cat silhouette and compose it with the retained Chun glyph."""

from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "print-package" / "source" / "assets"
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
chun_path = ASSETS / "chun-custom.svg"
chun = ET.parse(chun_path)
for group_id in ("chun-invertocat", "chun-cat"):
    old_logo = chun.getroot().find(f"{{{SVG}}}g[@id='{group_id}']")
    if old_logo is not None:
        chun.getroot().remove(old_logo)
glyph = chun.getroot().find(f".//{{{SVG}}}path[@id='chun-glyph']")
assert glyph is not None, "The accepted top Chun glyph must be retained."
assert len(chun.getroot().findall(f".//{{{SVG}}}path")) == 1, "Unexpected lower artwork remains."
work = ROOT / ".work" / "assets"
work.mkdir(parents=True, exist_ok=True)
recipe = work / "extract-cat.scad"
recipe.write_text(
    '$fn = 96;\nmodule logo() { import('
    + json.dumps(str(ASSETS / "github-invertocat.svg"))
    + ', center = false, dpi = 72); }\ndifference() { hull() logo(); logo(); }\n',
    encoding="utf-8",
)
extracted_path = work / "cat.svg"
result = subprocess.run(
    [os.environ.get("OPENSCAD", "openscad"), "--backend=Manifold", "--hardwarnings",
     "-o", str(extracted_path), str(recipe)], capture_output=True, text=True,
)
(work / "extract-cat.log").write_text(result.stdout + result.stderr, encoding="utf-8")
if result.returncode:
    raise RuntimeError(f"Cat silhouette extraction failed:\n{result.stdout}\n{result.stderr}")
extracted = ET.parse(extracted_path).getroot()
contours = [contour for node in extracted.iter(f"{{{SVG}}}path")
            for contour in re.findall(r"M[^M]+", node.get("d", ""))]
head_x, head_y = 49 * 25.4 / 72, -(96 - 47) * 25.4 / 72
cat_contours = []
for contour in contours:
    coordinates = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", contour)]
    assert len(coordinates) % 2 == 0, "Invalid extracted SVG contour."
    points = list(zip(coordinates[::2], coordinates[1::2]))
    inside = False
    for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
        if (ay > head_y) != (by > head_y) and head_x < ax + (head_y - ay) * (bx - ax) / (by - ay):
            inside = not inside
    if inside:
        cat_contours.append(contour)
assert len(cat_contours) == 1, "Expected one connected white cat containing the head, not the circle."
cat = ET.SubElement(chun.getroot(), f"{{{SVG}}}g", {
    "id": "chun-cat",
    "transform": "translate(5.423799822247 83.876810071173) scale(0.910745833695684)",
})
# Convert OpenSCAD's exported millimeter coordinates back into the source SVG frame.
ET.SubElement(cat, f"{{{SVG}}}path", {
    "d": cat_contours[0], "fill": "#B33220",
    "transform": f"translate(0 96) scale({72 / 25.4:.15g})",
})
ET.indent(chun, space="  ")
chun.write(chun_path, encoding="unicode")

expected = {"git-branch-24.svg", "github-invertocat.svg", "hatsu.svg", "chun-custom.svg"}
assert {path.name for path in ASSETS.glob("*.svg")} == expected
for path in ASSETS.glob("*.svg"):
    root = ET.parse(path).getroot()
    assert root.tag.endswith("svg"), path
    assert not any(node.tag.endswith(("script", "image", "text")) for node in root.iter()), path

provenance = {
    "artwork": [
        {
            "file": "git-branch-24.svg",
            "source": "https://github.com/primer/octicons/blob/main/icons/git-branch-24.svg",
            "license": "MIT; see the adjacent octicons-LICENSE.txt.",
        },
        {
            "file": "github-invertocat.svg",
            "source": "https://brand.github.com/GitHub_Logos.zip",
            "guidelines": "https://brand.github.com/foundations/logo",
            "modifications": "Uniform scaling only. GitHub trademark rights are not granted.",
        },
        {
            "file": "hatsu.svg",
            "source": "Pre-existing single-glyph outline supplied with the accepted design.",
            "font_files_distributed": False,
            "note": "Not covered by the source-code license. No system font is needed by this build.",
        },
        {
            "file": "chun-custom.svg",
            "source": "Retained hand-outlined Chun glyph plus the white cat silhouette extracted from github-invertocat.svg.",
            "modifications": "Keep the head/body/tail region from convex hull minus the original black logo. Select only the connected region containing the head, excluding the circle and a disconnected hull-edge sliver. Fill the cat red, without moving the upper Chun glyph.",
            "logo_source_file": "github-invertocat.svg",
            "cat_color": "#B33220",
            "black_circle_retained": False,
            "extracted_contours": len(contours),
            "selected_cat_contours": len(cat_contours),
            "product_official_or_endorsed": False,
            "reference_photo_distributed": False,
            "font_files_distributed": False,
            "note": "This is modified source artwork, not a new official logo. Removing the circle or recoloring does not grant permission for merchandise, combined artwork or redistribution. Not covered by the source-code license.",
        },
    ],
    "size_reference": {
        "product": "AMOS SMART",
        "url": "https://www.alban.co.jp/products/detail/682",
        "scope": "External tile body dimensions only; not equivalent material, weight or strength.",
    },
    "hardware_references": [
        {
            "url": "https://www.amazon.co.jp/dp/B0DN6JW6LK",
            "shape": "Ball chain with connector",
            "listed_length_mm": 120,
            "listed_ball_diameter_mm": 2.4,
            "approximate": ["pitch", "ball count", "connector dimensions", "drape", "silver finish"],
        },
        {
            "url": "https://www.amazon.co.jp/dp/B0FX47WYC4",
            "shape": "Round wire-gate clasp, jump ring, axial swivel and lower ring",
            "listing_length_mm": [42, 44],
            "listing_width_mm": 18,
            "approximate": ["internal proportions", "lower ring bore", "wire thickness"],
            "fit": "Unverified reference only; ball-chain mounting is the supported design intent.",
        },
    ],
    "source_asset_sha256": {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(ASSETS.iterdir()) if path.is_file()
    },
}
(ROOT / "validation" / "provenance.json").write_text(
    json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
)
print("Validated four SVG outlines; existing artwork is retained and no photo or system font is distributed.")
