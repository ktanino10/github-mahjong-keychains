"""Package the inspected print projects, bilingual instructions and offline HTML."""

from pathlib import Path
import argparse
import hashlib
import json
import zipfile

from PIL import Image
from designs import PRINTED_PART_COUNT, PROJECTS


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--poster-only", action="store_true", help="Refresh the embedded-viewer poster before building HTML.")
args = parser.parse_args()
poster_source = ROOT / "docs/images/keychains-studio.png"
with Image.open(poster_source) as rendered:
    # Blender's PNG metadata can retain the local .blend path even without a visible stamp.
    poster = Image.frombytes("RGB", rendered.size, rendered.convert("RGB").tobytes())
poster.save(poster_source)
poster.thumbnail((1500, 1150))
poster.save(ROOT / "viewer/poster.jpg", quality=88)
if args.poster_only:
    print("Refreshed the offline viewer poster.")
    raise SystemExit(0)

checks = json.loads((ROOT / "validation/slicer-checks.json").read_text())
assert len(checks["projects"]) == len(PROJECTS)
for item in checks["projects"]:
    path = ROOT / item["project"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], path
    assert item["slicer_return_code"] == 0 and not item["plate_warning_message"]

paths = [path for path in (ROOT / "print-package").rglob("*") if path.is_file()]
paths += [ROOT / name for name in [
    "README.md", "README.en.md", "ASSET-LICENSES.md", "LICENSE",
    "docs/index.html", "docs/images/keychains-studio.png",
    "viewer/assets/fonts/BigShoulders-OFL.txt", "viewer/assets/fonts/DMMono-OFL.txt",
]]
paths += [path for path in (ROOT / "licenses").rglob("*") if path.is_file()]
paths += list((ROOT / "docs/images").glob("*.png"))
paths += [path for path in (ROOT / "validation").glob("*.json") if path.name != "deliverables.json"]
target = ROOT / "docs/downloads/github-mahjong-keychains-P1S-0.2-AMS-PLA.zip"
target.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(set(paths)):
        assert path.is_file(), path
        archive.write(path, "github-mahjong-keychains/" + path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    names = archive.namelist()
    assert sum(name.endswith(".stl") for name in names) == PRINTED_PART_COUNT
    assert sum(name.endswith(".3mf") for name in names) == len(PROJECTS)
    assert not any(name.endswith((".gcode", ".log", ".ttc", ".blend")) for name in names)
    assert not any(name.startswith("/") or ".." in Path(name).parts for name in names)

deliverables = [target, ROOT / "docs/index.html", *(ROOT / "print-package/projects").glob("*.3mf")]
manifest = {
    path.relative_to(ROOT).as_posix(): {
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    for path in sorted(deliverables)
}
(ROOT / "validation/deliverables.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Packaged {len(names)} files: {len(PROJECTS)} projects and {PRINTED_PART_COUNT} STLs, bilingual instructions and offline viewer.")
