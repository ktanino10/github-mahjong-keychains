"""Trace the official Brand Toolkit's front-facing Ducky into a green inlay."""

from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from outline_trace import path_data, rasterize, trace


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("image", type=Path, help="Official mascots-03.png from the GitHub Brand Toolkit.")
args = parser.parse_args()
with Image.open(args.image) as image:
    assert image.size == (1510, 728), "Expected the official three-view Ducky reference."
    rgb = np.asarray(image.convert("RGB"), dtype=int)
crop = rgb[130:600, 90:480]
saturation = crop.max(axis=2) - crop.min(axis=2)
mask = ndimage.binary_fill_holes(saturation > 22)
labels, count = ndimage.label(mask)
assert count == 1, "Only the front-facing official duck should be selected."
contours = trace((~mask).astype(float) * 255, tolerance=0.28)
assert len(contours) == 1
traced = rasterize(contours, mask.shape)
iou = np.count_nonzero(mask & traced) / np.count_nonzero(mask | traced)
assert iou > 0.995
target = ROOT / "print-package/source/assets/iisou-ducky-silhouette.svg"
target.write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" width="11.505mm" height="13.865mm" viewBox="0 0 390 470">\n'
    '  <path fill="#238636" d="' + path_data(contours) + '"/>\n</svg>\n',
    encoding="utf-8",
)
yy, xx = np.mgrid[:470, :390]
eye_mask = ((crop[:, :, 2] > crop[:, :, 1] + 18) & (crop[:, :, 0] < 230)
            & (yy > 105) & (yy < 185) & (xx > 55) & (xx < 335))
eye_labels, eye_count = ndimage.label(eye_mask)
assert eye_count >= 2
sizes = np.bincount(eye_labels.ravel())
chosen = np.argsort(sizes[1:])[-2:] + 1
assert all(sizes[label] > 300 for label in chosen)
bill = ((crop[:, :, 0] > 240) & (crop[:, :, 1] < 190) & (crop[:, :, 2] < 160)
        & (xx > 110) & (xx < 280) & (yy > 110) & (yy < 230))
bill_labels, bill_count = ndimage.label(bill)
assert bill_count > 0
bill_sizes = np.bincount(bill_labels.ravel())
bill_mask = ndimage.binary_fill_holes(bill_labels == np.argmax(bill_sizes[1:]) + 1)
bill_contours = trace((~bill_mask).astype(float) * 255, tolerance=0.35)
assert len(bill_contours) == 1
bill_ink = bill_mask & (ndimage.distance_transform_edt(bill_mask) <= 14.5)
crease = Image.new("1", (390, 470))
t = np.linspace(0, 1, 80)[:, None]
curve = ((1 - t) ** 3 * [138, 206] + 3 * (1 - t) ** 2 * t * [151, 161]
         + 3 * (1 - t) * t ** 2 * [230, 151] + t ** 3 * [251, 206])
ImageDraw.Draw(crease).line([tuple(point) for point in curve], fill=1, width=14, joint="curve")
bill_ink |= np.asarray(crease) & bill_mask
bill_lines = trace((~bill_ink).astype(float) * 255, tolerance=0.25)
eye_mask = ndimage.binary_fill_holes(np.isin(eye_labels, chosen))
eyes = trace((~eye_mask).astype(float) * 255, tolerance=0.25)
assert len(eyes) == 2, "Retain both front-facing eyes in their original positions."
details = ROOT / "print-package/source/assets/iisou-ducky-details.svg"
details.write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" width="11.505mm" height="13.865mm" viewBox="0 0 390 470">\n'
    '  <path fill="#238636" fill-rule="evenodd" d="' + path_data(eyes + bill_lines) + '"/>\n'
    '</svg>\n', encoding="utf-8",
)
report = {
    "official_source": "https://brand.github.com/graphic-elements/mascots",
    "source_image": "https://brand.github.com/_next/static/media/mascots-03.202752d0.png",
    "source_image_sha256": hashlib.sha256(args.image.read_bytes()).hexdigest(),
    "selected_view": "Left-hand front-facing view; source crop x=90..480, y=130..600. Not mirrored.",
    "silhouette_pixel_iou": float(iou),
    "transform": "Uniform scale of the official front-facing silhouette, both traced eyes and traced broad bill, retaining their original positions. Green line art with a simplified bill crease and the unchanged symmetrical seven-feather peacock fan behind the duck. No mirroring, gradients or extra text.",
    "green": "#238636",
    "not_a_new_official_colorway_or_blanket_license": True,
    "usage_notice": "The upstream guide requires approval for public mascot use. This adaptation does not grant downstream permissions or establish a new official colorway.",
    "original_raster_distributed": False,
    "outline_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    "details_sha256": hashlib.sha256(details.read_bytes()).hexdigest(),
}
(ROOT / "validation/ducky-source.json").write_text(json.dumps(report, indent=2) + "\n")
print(f"Traced official front-facing Ducky, both eyes and bill: silhouette IoU {iou:.5f}; source raster not copied.")
