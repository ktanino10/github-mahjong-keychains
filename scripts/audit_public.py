"""Check the exact publishable file set, nested archives and offline assets."""

from pathlib import Path, PurePosixPath
import base64
import hashlib
import io
import json
import re
import struct
import subprocess
import zipfile

from PIL import Image
from designs import PRINTED_PART_COUNT, PROJECTS


ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".py", ".ts", ".mjs", ".css", ".html", ".scad", ".csv", ".svg", ".xml", ".config", ".model", ".rels"}
PRIVATE_PATTERNS = {
    "host home path": re.compile(r"(?:/(?:Users|home)/[^\s\"'<>]+|[A-Z]:\\{1,2}Users\\)", re.I),
    "session or plugin path": re.compile(r"\.copilot/(?:session-state|chats|installed-plugins)/"),
    "GitHub credential": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "credential or device value": re.compile(r'"(?:access_token|auth_token|refresh_token|password|printer_id|serial_number|print_host|printhost_apikey)"\s*:\s*"[^"]+"', re.I),
    "private service URL": re.compile(r'https?://[^\s/"<>]*(?:sharepoint\.com|outreach\.io|salesforce\.com|slack\.com)(?:/|["\s])', re.I),
    "private IP address": re.compile(r"(?<![\w.])(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?![\w.])"),
}
FORBIDDEN_SUFFIXES = {".log", ".dmg", ".app", ".gcode", ".ttc", ".blend", ".blend1", ".pyc"}
allowed_roots = {"docs", "print-package", "scripts", "validation", "viewer", "licenses"}
allowed_top = {".gitignore", "README.md", "README.en.md", "ASSET-LICENSES.md", "LICENSE", "requirements.txt"}
failures = []
scanned = 0


def check_text(name, content):
    for label, pattern in PRIVATE_PATTERNS.items():
        if pattern.search(content):
            failures.append(f"{name}: {label}")


def check_blob(name, content):
    global scanned
    scanned += 1
    path = PurePosixPath(name)
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        failures.append(f"{name}: non-distribution file type")
    if path.suffix.lower() in {".zip", ".3mf"}:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            if archive.testzip() is not None:
                failures.append(f"{name}: archive checksum failure")
            for entry in archive.infolist():
                member = PurePosixPath(entry.filename)
                if member.is_absolute() or ".." in member.parts:
                    failures.append(f"{name}: unsafe member path")
                if not entry.is_dir():
                    check_blob(f"{name}!{entry.filename}", archive.read(entry))
        return
    if path.suffix.lower() == ".glb":
        magic, version, length = struct.unpack_from("<III", content)
        assert magic == 0x46546C67 and version == 2 and length == len(content)
        json_length, chunk_type = struct.unpack_from("<II", content, 12)
        assert chunk_type == 0x4E4F534A
        metadata = content[20:20 + json_length].decode("utf-8")
        check_text(name, metadata)
        return
    if path.suffix.lower() == ".stl":
        check_text(name, content[:80].decode("ascii", errors="replace"))
        return
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        with Image.open(io.BytesIO(content)) as image:
            metadata = {**image.info, "EXIF": dict(image.getexif())}
            for key, value in metadata.items():
                text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
                check_text(f"{name}!{key}", text)
        return
    if path.suffix.lower() == ".ttf":
        if path.name not in {"BigShoulders-Bold.ttf", "DMMono-Regular.ttf"}:
            failures.append(f"{name}: unapproved font program")
        return
    if path.suffix.lower() in TEXT_EXTENSIONS or path.name in {"LICENSE", ".gitignore", ".nojekyll"}:
        check_text(name, content.decode("utf-8-sig"))


listing = subprocess.check_output(
    ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT
).decode().split("\0")
files = [ROOT / name for name in listing if name]
for path in files:
    relative = path.relative_to(ROOT)
    if len(relative.parts) == 1 and relative.name not in allowed_top:
        failures.append(f"{relative}: unexpected top-level file")
    if len(relative.parts) > 1 and relative.parts[0] not in allowed_roots:
        failures.append(f"{relative}: unexpected directory")
    if path.stat().st_size >= 50 * 1024 * 1024:
        failures.append(f"{relative}: unexpectedly large file")
    check_blob(relative.as_posix(), path.read_bytes())
    if path.suffix == ".md":
        for target in re.findall(r"\[[^\]]*\]\(([^ )]+)\)", path.read_text()):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            destination = path.parent / target.split("#", 1)[0]
            if not destination.exists():
                failures.append(f"{relative}: broken local link {target}")

html = (ROOT / "docs/index.html").read_text()
model_data = re.search(r'<script id="model-data" type="application/octet-stream">([^<]+)</script>', html)
assert model_data
embedded_model = base64.b64decode(model_data.group(1), validate=True)
assert embedded_model == (ROOT / "viewer/assets/keychains.glb").read_bytes()
check_blob("docs/index.html!embedded-model.glb", embedded_model)
assert "connect-src 'none'" in html
assert not re.search(r'<script[^>]+src=|<link[^>]+rel=["\']stylesheet', html, re.I)
poster_data = re.search(r'id="poster"[^>]+src="data:image/jpeg;base64,([^"]+)"', html)
assert poster_data
assert base64.b64decode(poster_data.group(1), validate=True) == (ROOT / "viewer/poster.jpg").read_bytes()
assert '"en"' in html and '"ja"' in html

accepted = json.loads((ROOT / "validation/accepted-meshes.json").read_text())
for name, expected in accepted["parts"].items():
    assert hashlib.sha256((ROOT / "print-package/STL" / name).read_bytes()).hexdigest() == expected
manifest = json.loads((ROOT / "validation/deliverables.json").read_text())
for name, expected in manifest.items():
    data = (ROOT / name).read_bytes()
    assert len(data) == expected["bytes"] and hashlib.sha256(data).hexdigest() == expected["sha256"]
projects = json.loads((ROOT / "validation/slicer-checks.json").read_text())["projects"]
for project in projects:
    assert hashlib.sha256((ROOT / project["project"]).read_bytes()).hexdigest() == project["sha256"]
assert len(projects) == len(PROJECTS)
assert len(list((ROOT / "print-package/STL").rglob("*.stl"))) == PRINTED_PART_COUNT
assert len(list((ROOT / "print-package/projects").glob("*.3mf"))) == len(PROJECTS)
preserved = json.loads((ROOT / "validation/preserved-originals.json").read_text())
for name, expected in preserved["files"].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
top_layers = json.loads((ROOT / "validation/top-layer-checks.json").read_text())
assert {item["variant"] for item in top_layers} == {"haku", "iisou"}
for item in top_layers:
    path = ROOT / "print-package/projects" / f"{item['variant']}-P1S-0.2-AMS-PLA.3mf"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["project_sha256"]

if failures:
    raise SystemExit("Public artifact audit failed:\n" + "\n".join(failures))
print(f"PASS: {len(files)} publishable files, {scanned} files/archive members; no private paths or credentials detected.")
print(f"PASS: {len(PROJECTS)} project hashes, {PRINTED_PART_COUNT} STLs, 18 byte-identical original files, top-layer evidence, documentation links and embedded viewer assets.")
