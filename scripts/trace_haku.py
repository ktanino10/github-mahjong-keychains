"""Trace only the supplied raster's dark silhouette, without copying the upload or metadata."""

from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from PIL import Image
from outline_trace import path_data, rasterize, trace


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("image", type=Path, help="Explicitly supplied reference image; never published.")
args = parser.parse_args()
with Image.open(args.image) as image:
    gray = np.asarray(image.convert("L"), dtype=float)
height, width = gray.shape
assert (width, height) == (135, 110), "Use the designated 135 by 110 source, not a replacement logo."
threshold = 127.5
contours = trace(gray, threshold=threshold)
assert len(contours) == 6, "Expected the outer face, two goggle gaps, lower white face and two black mouth details."
mask = rasterize(contours, gray.shape)
reference = gray < threshold
iou = np.count_nonzero(mask & reference) / np.count_nonzero(mask | reference)
assert iou > 0.985, f"Trace no longer faithfully follows the supplied silhouette: {iou}"
target = ROOT / "print-package/source/assets/haku-supplied-icon.svg"
target.write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
    '  <path fill="#161616" fill-rule="evenodd" d="' + path_data(contours) + '"/>\n</svg>\n',
    encoding="utf-8",
)
report = {
    "source": "User-supplied 135 x 110 raster showing a legacy Copilot-style face.",
    "source_image_distributed": False, "source_metadata_distributed": False,
    "method": "127.5-level marching-squares contour, mild corner smoothing and 0.13-pixel simplification; all six boundaries retained.",
    "reference_pixel_mask_iou": float(iou), "closed_contours": len(contours),
    "no_background_rectangle_or_text": True,
    "current_approved_logo_or_merchandise_permission_claimed": False,
    "outline": target.relative_to(ROOT).as_posix(),
    "outline_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
}
(ROOT / "validation/haku-trace.json").write_text(json.dumps(report, indent=2) + "\n")
print(f"Traced all six source boundaries; threshold-mask IoU {iou:.5f}. Original upload not copied.")
