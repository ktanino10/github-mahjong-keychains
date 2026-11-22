from pathlib import Path
import json
import sys

import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from designs import PRINTED_PART_COUNT, VARIANTS
from validate_projects import canonical_faces
scene = trimesh.load_scene(ROOT / "viewer/assets/keychains.glb")
results = []
for variant, _, _ in VARIANTS.values():
    report = json.loads((ROOT / "validation" / f"validation-{variant}.json").read_text())
    part_bounds = [np.array(part["bounds_mm"]) for name, part in report["parts"].items() if name != "blank"]
    overall = np.array([np.min([bounds[0] for bounds in part_bounds], axis=0),
                        np.max([bounds[1] for bounds in part_bounds], axis=0)])
    assert np.allclose(overall, [[-10.5, -14, 0], [10.5, 22, 16.5]], atol=0.0001), variant
    for part, original in report["parts"].items():
        if part == "blank":
            continue
        mesh = scene.geometry[f"{variant}/{part}"]
        bounds = mesh.bounds * 1000
        volume = mesh.volume * 1e9
        assert len(mesh.faces) == original["faces"], (variant, part)
        assert np.allclose(bounds, original["bounds_mm"], atol=0.0001), (variant, part)
        assert abs(volume - original["volume_mm3"]) < 0.03, (variant, part)
        source = trimesh.load_mesh(ROOT / original["file"], process=True)
        distances, vertex_map = source.kdtree.query(mesh.vertices * 1000)
        assert float(distances.max()) < 2e-5, (variant, part)
        assert np.array_equal(canonical_faces(vertex_map[mesh.faces]), canonical_faces(source.faces)), (variant, part)
        if part == "black_back":
            assert mesh.visual.material.name == "Printed black", variant
            ear = mesh.vertices[mesh.vertices[:, 1] > 0.01401] * 1000
            assert np.allclose([ear[:, 2].min(), ear[:, 2].max()], [0, 5], atol=0.0001), variant
            assert bounds[1, 2] <= 5.5001, variant
        elif part == "white_body":
            assert mesh.visual.material.name == "Printed white", variant
            assert np.isclose(bounds[0, 2], 5.5, atol=0.0001), variant
            assert bounds[1, 1] <= 14.0001, variant
        elif variant == "chun" and part == "inlay":
            assert mesh.visual.material.name == "Printed red", variant
        elif variant == "haku" and part == "inlay":
            assert mesh.visual.material.name == "Printed black", variant
        elif part == "inlay" and variant not in {"octocat", "chun"}:
            assert mesh.visual.material.name == "Printed green", variant
        results.append({
            "part": f"{variant}/{part}",
            "triangles": len(mesh.faces),
            "max_bound_difference_mm": float(np.max(np.abs(bounds - original["bounds_mm"]))),
            "volume_difference_mm3": volume - original["volume_mm3"],
            "max_vertex_distance_mm": float(distances.max()),
            "triangle_connectivity_and_winding_unchanged": True,
        })
assert len(results) == PRINTED_PART_COUNT
(ROOT / "validation" / "viewer-geometry.json").write_text(json.dumps(results, indent=2) + "\n")
print(f"All {PRINTED_PART_COUNT} browser meshes preserve printable triangle counts, dimensions and volumes.")
print("All six ears are black; white starts at z=5.5 mm. Artwork colors match the printable parts.")
