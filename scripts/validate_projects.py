"""Reopen and slice the published project files, without supplying any presets."""

from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import trimesh

from package_models import CORE, MACHINE, PROCESS, PROJECTS, ROOT, VARIANTS, VERSION, project_materials, slot_for, write_json


PRODUCTION = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
NS = {"m": CORE}
EXPECTED = PROJECTS


def check_settings(config, selected):
    palette, _ = project_materials(selected)
    count = len(palette)
    assert config["printer_settings_id"] == MACHINE
    assert config["printer_model"] == "Bambu Lab P1S"
    assert config["printer_variant"] == "0.2"
    assert config["nozzle_diameter"] == ["0.2"]
    assert config["print_settings_id"] == PROCESS
    assert config["filament_colour"] == [color for _, color in palette]
    assert config["filament_type"] == ["PLA"] * count
    assert len(config["filament_settings_id"]) == count
    assert all(float(value) == 1.75 for value in config["filament_diameter"])
    assert all(float(value) == 1.6 for value in config["filament_max_volumetric_speed"])
    assert float(config["layer_height"]) == 0.1
    assert float(config["initial_layer_print_height"]) == 0.1
    assert int(config["wall_loops"]) == 6
    assert config["sparse_infill_density"] == "100%"
    assert config["sparse_infill_pattern"] == "zig-zag"
    assert config["enable_prime_tower"] == "1"
    assert config["enable_support"] == "0"
    assert config["curr_bed_type"] == "Textured PEI Plate"
    assert len(config["flush_volumes_matrix"]) == count * count
    assert all(float(value) > 0 for i, value in enumerate(config["flush_volumes_matrix"]) if i % (count + 1))


def transform(value):
    result = np.eye(4)
    if value:
        result[:3, :] = np.array([float(number) for number in value.split()]).reshape(4, 3).T
    return result


def canonical_faces(faces):
    # Cyclic rotation preserves winding; sorting floating coordinates does not.
    starts = np.argmin(faces, axis=1)
    ordered = np.take_along_axis(faces, (starts[:, None] + np.arange(3)) % 3, axis=1)
    return ordered[np.lexsort((ordered[:, 2], ordered[:, 1], ordered[:, 0]))]


def inspect_project(path, selected):
    expected_names = set()
    for key in selected:
        variant = VARIANTS[key][0]
        expected_names.update(f"{variant}/{part}" for part in
                              ["black_back", "white_body", "inlay"] + (["light_inlay"] if variant == "hatsu" else []))
    results = []
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        assert not any(name.endswith((".gcode", ".gcode.3mf")) for name in archive.namelist())
        check_settings(json.loads(archive.read("Metadata/project_settings.config")), selected)
        main = ET.fromstring(archive.read("3D/3dmodel.model"))
        assert main.get("unit") == "millimeter"
        settings = ET.fromstring(archive.read("Metadata/model_settings.config"))
        build = main.findall("m:build/m:item", NS)
        assert len(build) == len(selected)
        assert len(settings.findall("plate")) == 1
        for item in build:
            placement = transform(item.get("transform"))
            assert np.allclose(placement[:3, :3], np.eye(3))
            assert placement[2, 3] == 0
            assembly = main.find(f"m:resources/m:object[@id='{item.get('objectid')}']", NS)
            obj_settings = settings.find(f"object[@id='{item.get('objectid')}']")
            assert assembly is not None and obj_settings is not None
            for component in assembly.findall("m:components/m:component", NS):
                part = obj_settings.find(f"part[@id='{component.get('objectid')}']")
                assert part is not None
                metadata = {node.get("key"): node.get("value") for node in part.findall("metadata")}
                name = metadata["name"]
                assert name in expected_names
                variant, kind = name.split("/")
                slot = int(metadata["extruder"])
                assert slot == slot_for(variant, kind), (name, slot)
                stats = part.find("mesh_stat")
                assert stats is not None
                assert all(int(value) == 0 for key, value in stats.attrib.items() if key != "face_count")
                model_path = component.get(f"{{{PRODUCTION}}}path", "3D/3dmodel.model").lstrip("/")
                definition = ET.fromstring(archive.read(model_path))
                mesh_xml = definition.find(f"m:resources/m:object[@id='{component.get('objectid')}']/m:mesh", NS)
                assert mesh_xml is not None
                vertices = [[float(node.get(axis)) for axis in ("x", "y", "z")]
                            for node in mesh_xml.findall("m:vertices/m:vertex", NS)]
                faces = [[int(node.get(axis)) for axis in ("v1", "v2", "v3")]
                         for node in mesh_xml.findall("m:triangles/m:triangle", NS)]
                mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
                mesh.apply_transform(transform(component.get("transform")))
                report = json.loads((ROOT / "validation" / f"validation-{variant}.json").read_text())
                original = trimesh.load_mesh(ROOT / report["parts"][kind]["file"], process=True)
                assert mesh.is_watertight and mesh.is_winding_consistent
                assert len(mesh.faces) == len(original.faces)
                assert len(mesh.vertices) == len(original.vertices)
                distances, vertex_map = original.kdtree.query(mesh.vertices)
                difference = float(np.max(distances))
                assert difference < 2e-5, (path.name, name, difference)
                assert len(np.unique(vertex_map)) == len(original.vertices), "Vertex correspondence is not bijective."
                assert np.array_equal(canonical_faces(vertex_map[mesh.faces]), canonical_faces(original.faces)), "Triangle connectivity or winding changed."
                assert np.allclose(mesh.bounds, original.bounds, atol=2e-5)
                assert np.all(mesh.bounds[0] + placement[:3, 3] >= [0, 0, 0])
                assert np.all(mesh.bounds[1] + placement[:3, 3] <= [256, 256, 250])
                results.append({"part": name, "slot": slot, "triangles": len(faces),
                                "max_vertex_distance_mm": difference, "triangle_connectivity_and_winding_unchanged": True})
    assert {item["part"] for item in results} == expected_names
    assert len(results) == len(expected_names)
    return results


def classify_cli_diagnostics(log):
    diagnostics = []
    patterns = [
        ("cli mode, Current BambuStudio Version", "CLI version banner logged at warning level"),
        ("can not find system preset file:", "Desktop bundle lacks optional machine_full/process_full lookup copies; embedded project settings were used"),
        ("no filament colors found in projects", "Known CLI branch message when an existing flush matrix needs no recalculation; project colors and actual toolpaths verified separately"),
        ("building nozzle list from filament map and volume types", "Single-nozzle compatibility mapping initialized from the embedded filament map"),
        ("tree support default to organic support", "Support-constructor default; support generation is disabled in this project"),
    ]
    for line in log.splitlines():
        if "[error]" in line:
            raise AssertionError(f"Slicer error: {line}")
        if "[warning]" not in line:
            continue
        for token, explanation in patterns:
            if token in line:
                if explanation not in diagnostics:
                    diagnostics.append(explanation)
                break
        else:
            raise AssertionError(f"Unclassified slicer warning: {line}")
    return diagnostics


def check_toolpaths(gcode, expected_layers):
    tool = layer = object_id = feature = None
    observed = {}
    ams_slots = set()
    for line in gcode.decode("utf-8").splitlines():
        command = line.split(";", 1)[0].strip()
        match = re.fullmatch(r"T(\d+)", command)
        if match:
            number = int(match[1])
            # T1000 is the stock nozzle-load-line sentinel, not another AMS spool.
            if number not in {255, 1000}:
                tool = number + 1
        match = re.match(r"M620 S(\d+)A\b", command)
        if match:
            ams_slots.add(int(match[1]) + 1)
        match = re.fullmatch(r"; layer num/total_layer_count: (\d+)/\d+", line)
        if match:
            layer = int(match[1]) - 1
        match = re.fullmatch(r"; OBJECT_ID: (\d+)", line)
        if match:
            object_id = int(match[1])
        if line.startswith("; FEATURE: "):
            feature = line.removeprefix("; FEATURE: ")
        extrusion = re.search(r"\bE(-?[\d.]+)", command)
        if (layer is not None and object_id and feature not in {None, "Custom", "Prime tower"}
                and re.match(r"G[123] ", command) and re.search(r"\b[XY]-?[\d.]", command)
                and extrusion and float(extrusion[1]) > 0):
            assert tool is not None, "Object extrusion has no selected filament."
            observed.setdefault(layer, set()).add(tool)
    assert observed == expected_layers, "Actual object extrusion tools do not match the required layer colors."
    expected_slots = set().union(*expected_layers.values())
    assert ams_slots == expected_slots, "AMS selectors do not match the actual model filaments."
    return {
        "object_layers_verified": len(observed),
        "actual_object_extrusion_matches_layer_colors": True,
        "actual_ams_project_slots": sorted(ams_slots),
        "prime_tower_and_custom_purge_excluded": True,
    }


def validate_slice(path, selected, parts, executable, work):
    palette, _ = project_materials(selected)
    work.mkdir(parents=True, exist_ok=True)
    for name in ("home", "data", "output"):
        (work / name).mkdir(exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = str(work / "home")
    log_path = work / "slice.log"
    command = [
        str(executable), "--datadir", str(work / "data"), "--debug", "3",
        "--slice", "1", "--export-3mf", "sliced.3mf",
        "--export-settings", str(work / "reopened-settings.json"),
        "--outputdir", str(work / "output"), str(path),
    ]
    with log_path.open("w") as log:
        result = subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"Slicing failed ({result.returncode}); inspect {log_path}")
    raw = json.loads((work / "output/result.json").read_text())
    assert raw["return_code"] == 0 and raw["error_string"] == "Success."
    assert len(raw["sliced_plates"]) == 1
    plate = raw["sliced_plates"][0]
    assert plate["warning_message"] == "", plate["warning_message"]
    assert len(plate["objects"]) == len(selected)
    assert plate["triangle_count"] == sum(part["triangles"] for part in parts)
    expected_slots = {part["slot"] for part in parts}
    assert {item["id"] for item in plate["filaments"]} == expected_slots
    assert all(item["main_used_g"] > 0 for item in plate["filaments"])
    with zipfile.ZipFile(work / "output/sliced.3mf") as sliced:
        check_settings(json.loads(sliced.read("Metadata/project_settings.config")), selected)
        info = ET.fromstring(sliced.read("Metadata/slice_info.config"))
        state = {node.get("key"): node.get("value") for node in info.findall("plate/metadata")}
        assert state["outside"] == "false"
        assert state["support_used"] == "false"
        assert state["nozzle_diameters"] == "0.2"
        used = info.findall("plate/filament")
        assert {int(node.get("id")) for node in used} == expected_slots
        for node in used:
            assert node.get("type") == "PLA"
            assert node.get("color") == palette[int(node.get("id")) - 1][1]
            assert float(node.get("nozzle_diameter")) == 0.2
        layers = {}
        for node in info.findall("plate/layer_filament_lists/layer_filament_list"):
            slots = {int(value) + 1 for value in node.get("filament_list").split()}
            ranges = [int(value) for value in node.get("layer_ranges").split()]
            assert len(ranges) % 2 == 0
            for start, end in zip(ranges[::2], ranges[1::2]):
                for layer in range(start, end + 1):
                    assert layer not in layers
                    layers[layer] = slots
        assert set(layers) == set(range(165)), "Missing or extra layers."
        assert all(layers[layer] == {2} for layer in range(55)), "Black rear/ear assignment changed."
        assert all(layers[layer] == {1} for layer in range(55, 157)), "White side assignment changed."
        top_slots = {1} | {part["slot"] for part in parts if part["part"].endswith(("inlay", "light_inlay"))}
        assert all(layers[layer] == top_slots for layer in range(157, 165)), "Inlay filament assignment changed."
        gcode = sliced.read("Metadata/plate_1.gcode")
        assert len(gcode) > 100000
        assert b"M620" in gcode and b"M621" in gcode
        toolpaths = check_toolpaths(gcode, layers)
        gcode_hash = hashlib.sha256(gcode).hexdigest()
    diagnostics = classify_cli_diagnostics(log_path.read_text())
    return {
        "project": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "reopened_without_external_presets_or_setting_overrides": True,
        "slicer_return_code": 0, "plate_warning_message": "",
        "objects": len(selected), "parts": parts, "layers": 165,
        "black_layers_1_based": [1, 55], "white_layers_1_based": [56, 157],
        "surface_inlay_layers_1_based": [158, 165],
        "used_project_slots": sorted(expected_slots),
        "filament_changes": plate["filament_change_times"],
        "estimated_print_seconds": plate["total_predication"],
        "estimated_filament_grams_including_flush_and_tower": sum(item["total_used_g"] for item in plate["filaments"]),
        "local_toolpath_sha256": gcode_hash,
        "toolpath_checks": toolpaths,
        "gcode_published": False, "printer_transmission_performed": False,
        "cli_diagnostics": diagnostics,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bambu", required=True, type=Path)
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".work" / "verification")
    parser.add_argument("--only", choices=EXPECTED, help="Re-slice one project and retain hash-matching evidence for the others.")
    args = parser.parse_args()
    previous = {}
    if args.only:
        saved = json.loads((ROOT / "validation/slicer-checks.json").read_text())
        assert saved["slicer"] == f"BambuStudio-{VERSION}"
        previous = {item["project"]: item for item in saved["projects"]}
    results = []
    for name, selected in EXPECTED.items():
        path = ROOT / "print-package/projects" / f"{name}-P1S-0.2-AMS-PLA.3mf"
        parts = inspect_project(path, selected)
        if args.only and name != args.only:
            item = previous.get(str(path.relative_to(ROOT)))
            if item is None or item["sha256"] != hashlib.sha256(path.read_bytes()).hexdigest():
                raise RuntimeError(f"No matching prior slice evidence for {path.name}; run without --only.")
            results.append(item)
            print(f"PASS {path.name}: unchanged project; retained verified slice evidence")
            continue
        result = validate_slice(path, selected, parts, args.bambu.resolve(), args.work_dir.resolve() / name)
        results.append(result)
        print(f"PASS {path.name}: {len(parts)} unchanged parts, 165 layers, slots {result['used_project_slots']}, no plate warnings")
    write_json(ROOT / "validation/slicer-checks.json", {
        "slicer": f"BambuStudio-{VERSION}", "method": "Native CLI reopen and slice, no printer connection",
        "geometry_tolerance_mm": 2e-5, "physical_print_and_strength_tested": False,
        "projects": results,
    })


if __name__ == "__main__":
    main()
