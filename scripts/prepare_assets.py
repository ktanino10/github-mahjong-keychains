"""Validate the supplied outlines without accessing or exporting system fonts."""

from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "print-package" / "source" / "assets"
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
            "source": "User-supplied image: a red Chun glyph above an open-bottom cat-head outline.",
            "modifications": "Manual flat outline, preserving the composition and a restrained red; not the circular Invertocat or a full character.",
            "official_logo_claim": False,
            "reference_photo_distributed": False,
            "font_files_distributed": False,
            "note": "Image-derived custom artwork; original rights remain with their holders. Not covered by the source-code license.",
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
