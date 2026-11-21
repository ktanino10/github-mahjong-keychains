from pathlib import Path
import json
import os
import subprocess
import sys

import numpy as np
import trimesh


OUT = Path(__file__).resolve().parents[1]
SOURCE = OUT / "print-package" / "source"
VARIANTS = {"git_branch": "01-git-branch", "octocat": "02-octocat", "hatsu": "03-hatsu"}
variant = sys.argv[1]
if variant not in VARIANTS:
    raise SystemExit(f"Unknown variant: {variant}")
target = OUT / "print-package" / "STL" / VARIANTS[variant]
target.mkdir(parents=True, exist_ok=True)
logs = OUT / ".work" / "build-logs"
logs.mkdir(parents=True, exist_ok=True)
report = {"variant": variant, "parts": {}}

parts = ["black_back", "white_body", "inlay"]
if variant == "hatsu":
    parts.append("light_inlay")
if variant == "git_branch":
    parts.append("blank")

for part in parts:
    color = "black" if part == "black_back" or (part == "inlay" and variant == "octocat") else "green"
    if part == "white_body":
        color = "white"
    if part == "light_inlay":
        color = "light-green"
    filename = f"{part}-{color}.stl" if part != "blank" else "reference-blank.stl"
    destination = target / filename if part != "blank" else OUT / "validation" / filename
    command = [
        os.environ.get("OPENSCAD", "openscad"),
        "--backend=Manifold",
        "--hardwarnings",
        "--export-format=binstl",
        "-D", f'variant="{variant}"',
        "-D", f'part="{part}"',
        "-o", str(destination),
        str(SOURCE / "keychains.scad"),
    ]
    result = subprocess.run(command, cwd=SOURCE, capture_output=True, text=True)
    log = logs / f"{variant}-{part}.log"
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"OpenSCAD failed for {variant}/{part}:\n{result.stdout}\n{result.stderr}")
    mesh = trimesh.load_mesh(destination, process=True)
    if not isinstance(mesh, trimesh.Trimesh):
        raise TypeError(f"Unexpected mesh type: {destination}")
    components = mesh.split(only_watertight=False)
    assert np.isfinite(mesh.vertices).all(), destination
    assert mesh.is_watertight and mesh.is_winding_consistent, destination
    assert mesh.volume > 0, destination
    assert all(c.is_watertight and c.volume > 0 for c in components), destination
    assert np.all(mesh.area_faces > 1e-10), destination
    if part in {"white_body", "black_back", "blank"}:
        assert len(components) == 1, (destination, len(components))
    expected_z = {
        "black_back": [0.0, 5.5],
        "white_body": [5.5, 16.5],
        "inlay": [15.7, 16.5],
        "light_inlay": [15.7, 16.5],
        "blank": [0.0, 16.5],
    }[part]
    assert np.allclose(mesh.bounds[:, 2], expected_z, atol=2e-5), (destination, mesh.bounds)
    if part in {"inlay", "light_inlay"}:
        assert np.all(mesh.bounds[0, :2] >= [-8.925, -11.55]), mesh.bounds
        assert np.all(mesh.bounds[1, :2] <= [8.925, 11.55]), mesh.bounds
    report["parts"][part] = {
        "file": str(destination.relative_to(OUT)),
        "bounds_mm": mesh.bounds.tolist(),
        "volume_mm3": float(mesh.volume),
        "faces": len(mesh.faces),
        "watertight": bool(mesh.is_watertight),
        "components": len(components),
    }
    print(variant, part, f"{mesh.volume:.3f} mm3", len(mesh.faces), "triangles", len(components), "component(s)")

(OUT / "validation" / f"validation-{variant}.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
