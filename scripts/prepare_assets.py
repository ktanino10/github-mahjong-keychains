"""Compose Chun with the official Invertocat and validate the supplied outlines."""

from pathlib import Path
import copy
import hashlib
import json
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "print-package" / "source" / "assets"
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
chun_path = ASSETS / "chun-custom.svg"
chun = ET.parse(chun_path)
old_logo = chun.getroot().find(f"{{{SVG}}}g[@id='chun-invertocat']")
if old_logo is not None:
    chun.getroot().remove(old_logo)
glyph = chun.getroot().find(f".//{{{SVG}}}path[@id='chun-glyph']")
assert glyph is not None, "The accepted top Chun glyph must be retained."
assert len(chun.getroot().findall(f".//{{{SVG}}}path")) == 1, "Unexpected lower artwork remains."
official = ET.parse(ASSETS / "github-invertocat.svg").getroot()
logo = ET.SubElement(chun.getroot(), f"{{{SVG}}}g", {
    "id": "chun-invertocat",
    "transform": "translate(5.423799822247 83.876810071173) scale(0.910745833695684)",
})
for node in official:
    copied = copy.deepcopy(node)
    for descendant in copied.iter():
        if descendant.get("id"):
            descendant.set("id", descendant.get("id") + "-chun")
        if descendant.get("clip-path"):
            descendant.set("clip-path", descendant.get("clip-path").replace(")", "-chun)"))
        if descendant.tag == f"{{{SVG}}}path":
            descendant.set("fill", "#B33220")
    logo.append(copied)
assert [node.get("d") for node in logo.iter(f"{{{SVG}}}path")] == [
    node.get("d") for node in official.iter(f"{{{SVG}}}path")
], "The Invertocat path must not be redrawn or distorted."
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
            "source": "Retained hand-outlined Chun glyph plus the existing official github-invertocat.svg.",
            "modifications": "Top glyph retained. Lower logo uses the original official path, uniform scaling and red recoloring only; the former custom head is removed.",
            "logo_source_file": "github-invertocat.svg",
            "logo_color": "#B33220",
            "product_official_or_endorsed": False,
            "reference_photo_distributed": False,
            "font_files_distributed": False,
            "note": "Glyph and official logo artwork rights remain with their holders. Red is a project-specific recoloring, not a blanket permission or new official logo color. Not covered by the source-code license.",
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
