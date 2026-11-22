from pathlib import Path
import json
import os
import hashlib
import shutil
import subprocess
import sys

import numpy as np
import trimesh

from designs import ADDITIONS, VARIANTS as INVENTORY, parts_for

OUT = Path(__file__).resolve().parents[1]
SOURCE = OUT / "print-package" / "source"
VARIANTS = {variant: slug for variant, slug, _ in INVENTORY.values()}
variant = sys.argv[1]
if variant not in VARIANTS:
    raise SystemExit(f"Unknown variant: {variant}")
target = OUT / "print-package" / "STL" / VARIANTS[variant]
target.mkdir(parents=True, exist_ok=True)
logs = OUT / ".work" / "build-logs"
logs.mkdir(parents=True, exist_ok=True)
report = {"variant": variant, "parts": {}}

parts = parts_for(variant)
if variant == "git_branch":
    parts.append("blank")

for part in parts:
    color = "black" if part == "black_back" or (part == "inlay" and variant in {"octocat", "haku"}) else "green"
    if part == "white_body":
        color = "white"
    if part == "light_inlay":
        color = "light-green"
    if part == "inlay" and variant == "chun":
        color = "red"
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
    if variant in ("chun", *ADDITIONS) and part == "black_back":
        common = OUT / "print-package/STL/01-git-branch/black_back-black.stl"
        accepted = json.loads((OUT / "validation/accepted-meshes.json").read_text())
        assert hashlib.sha256(common.read_bytes()).hexdigest() == accepted["parts"]["01-git-branch/black_back-black.stl"]
        shutil.copyfile(common, destination)
    else:
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
    if "inlay" in part:
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

if variant in ("chun", *ADDITIONS):
    reference = OUT / "validation/reference-blank.stl"
    blank = trimesh.load_mesh(reference, process=True)
    volume_error = sum(info["volume_mm3"] for info in report["parts"].values()) - blank.volume
    assert abs(volume_error) < 0.001, volume_error
    if variant == "chun":
        assert report["parts"]["inlay"]["components"] == 2, "The red part must contain only the Chun glyph and cat silhouette."
    check = logs / f"{variant}-partition.scad"
    imports = [f'import("{(OUT / info["file"]).as_posix()}");' for info in report["parts"].values()]
    assembled = "union() {" + "".join(imports) + "}"
    original = f'import("{reference.as_posix()}");'
    # A remote unit cube lets an empty residual export successfully.
    check.write_text(
        "union() { translate([100,100,100]) cube(1);"
        f"difference() {{{assembled}{original}}}"
        f"difference() {{{original}{assembled}}}"
        + "".join(f"intersection() {{{a}{b}}}" for i, a in enumerate(imports) for b in imports[i + 1:])
        + "}", encoding="utf-8",
    )
    residual_path = logs / f"{variant}-partition.stl"
    result = subprocess.run(
        [os.environ.get("OPENSCAD", "openscad"), "--backend=Manifold", "--hardwarnings",
         "--export-format=binstl", "-o", str(residual_path), str(check)],
        capture_output=True, text=True,
    )
    (logs / f"{variant}-partition.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"Partition validation failed:\n{result.stdout}\n{result.stderr}")
    residual = trimesh.load_mesh(residual_path, process=True)
    sentinel_faces = np.all(residual.triangles >= 100, axis=(1, 2))
    sentinel = residual.submesh([np.flatnonzero(sentinel_faces)], append=True)
    assert sentinel.is_watertight and abs(sentinel.volume - 1) < 1e-6
    boundary_facets = residual.triangles[~sentinel_faces]
    boundary_error = 0.0
    if len(boundary_facets):
        # Float32 roundtrips leave coincident facets on the inlay's top and walls.
        inlay_mesh = trimesh.util.concatenate([
            trimesh.load_mesh(OUT / info["file"], process=True)
            for name, info in report["parts"].items() if "inlay" in name
        ])
        points = np.unique(boundary_facets.reshape(-1, 3), axis=0)
        for start in range(0, len(points), 32):
            _, distances, _ = trimesh.proximity.closest_point_naive(inlay_mesh, points[start:start + 32])
            boundary_error = max(boundary_error, float(distances.max()))
        assert boundary_error < 2e-5, "Residual geometry is not confined to the shared inlay interface."
    assert abs(residual.volume - 1) < 1e-6, "Parts overlap or change the accepted blank."
    report.update({
        "volume_sum_error_mm3": float(volume_error),
        "accepted_blank_partition_matches_within_stl_precision": True,
        "pairwise_part_intersections_have_no_volume": True,
        "boolean_residual_boundary_facets": len(boundary_facets),
        "max_boolean_residual_inlay_surface_distance_mm": boundary_error,
        "boolean_residual_volume_mm3": float(residual.volume - 1),
        "geometry_tolerance_mm": 2e-5,
        "common_black_back_byte_identical": True,
        "reference_blank_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
        "source": "print-package/source/keychains.scad",
        "physical_print_and_fit_tested": False,
    })
    if variant == "chun":
        report["source_asset"] = "print-package/source/assets/chun-custom.svg"
    if variant == "haku":
        bounds = np.array(report["parts"]["inlay"]["bounds_mm"])
        assert bounds[1, 1] < 0, "Haku must have no graphic or text above the face center."
        assert bounds[0, 1] > -11.5, "The supplied icon needs a clear bottom margin."
        report["layout"] = {
            "no_text_or_upper_graphic": True,
            "icon_width_mm": float(bounds[1, 0] - bounds[0, 0]),
            "bottom_margin_mm": float(bounds[0, 1] + 14),
            "top_of_black_graphic_y_mm": float(bounds[1, 1]),
            "source_asset": "print-package/source/assets/haku-supplied-icon.svg",
        }
    elif variant == "iisou":
        components = trimesh.load_mesh(OUT / report["parts"]["inlay"]["file"], process=True).split()
        assert any(mesh.bounds[1, 1] > 11 for mesh in components), "The peacock fan must reach the upper face."
        report["layout"] = {"single_bird": True, "peacock_fan_feathers": 7, "duck": "Official central three-quarter GitHub Ducky, mirrored so its bill faces left, with both eyes and a symmetrical peacock fan behind it. All green.", "numerals_or_text": False}

(OUT / "validation" / f"validation-{variant}.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
if variant in ("chun", *ADDITIONS):
    summary_path = OUT / "validation/validation-summary.json"
    summary = json.loads(summary_path.read_text())
    summary["variant_checks"][variant] = report
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
