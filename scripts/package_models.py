"""Build native project 3MFs using the official Bambu Studio application.

Only stock resources supplied with the application are read. Printer accounts,
connected devices and the user's Bambu Studio data directory are never used.
"""

from pathlib import Path
import argparse
import copy
import csv
import hashlib
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import trimesh

from designs import ADDITIONS, PROJECTS, VARIANTS, parts_for

ROOT = Path(__file__).resolve().parents[1]
CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
ET.register_namespace("", CORE)
VERSION = "02.09.01.70"
MACHINE = "Bambu Lab P1S 0.2 nozzle"
STOCK_PROCESS = "0.10mm Standard @BBL X1C 0.2 nozzle"
STOCK_FILAMENT = "Generic PLA @0.2 nozzle"
PROCESS = "Keychains 0.10mm Solid @P1S 0.2"
PALETTE = [
    ("White", "#F6F5EE"),
    ("Black", "#161616"),
    ("Green", "#238636"),
    ("Light green", "#9DD96C"),
]
CHUN_PALETTE = PALETTE[:2] + [("Red", "#B33220")]
IISOU_PALETTE = PALETTE[:3]
FLUSH_MATRIX = [
    0, 250, 300, 250,
    800, 0, 600, 750,
    600, 250, 0, 500,
    400, 250, 300, 0,
]
CHUN_FLUSH_MATRIX = [
    0, 250, 300,
    800, 0, 600,
    650, 250, 0,
]


def project_materials(selected):
    if not selected or any(key not in VARIANTS for key in selected):
        raise ValueError("Select known designs.")
    if "chun" in selected:
        if selected != ["chun"]:
            raise ValueError("Chun must remain a separate three-color project.")
        return CHUN_PALETTE, CHUN_FLUSH_MATRIX
    if "haku" in selected:
        if selected != ["haku"]:
            raise ValueError("Haku is supplied as a separate two-color project.")
        return PALETTE[:2], [0, 250, 800, 0]
    if "iisou" in selected:
        if selected != ["iisou"]:
            raise ValueError("Iisou is supplied as a separate three-color project.")
        return IISOU_PALETTE, [FLUSH_MATRIX[row * 4 + column] for row in range(3) for column in range(3)]
    return PALETTE, FLUSH_MATRIX


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def resolve_profile(directory, name, sources, visiting=()):
    if name in visiting:
        raise ValueError(f"Cyclic stock profile inheritance: {visiting + (name,)}")
    path = directory / f"{name}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    sources[f"{directory.name}/{path.name}"] = hashlib.sha256(path.read_bytes()).hexdigest()
    profile = {}
    if data.get("inherits"):
        profile.update(resolve_profile(directory, data["inherits"], sources, visiting + (name,)))
    for included in data.get("include", []):
        profile.update(resolve_profile(directory, included, sources, visiting + (name,)))
    profile.update({key: value for key, value in data.items() if key not in {"inherits", "include"}})
    return profile


def configured_profiles(resources, work, palette):
    sources = {}
    machine = resolve_profile(resources / "machine", MACHINE, sources)
    process = resolve_profile(resources / "process", STOCK_PROCESS, sources)
    filament = resolve_profile(resources / "filament", STOCK_FILAMENT, sources)
    assert machine["nozzle_diameter"] == ["0.2"]
    assert machine["printer_model"] == "Bambu Lab P1S"
    assert MACHINE in process["compatible_printers"]
    assert MACHINE in filament["compatible_printers"]
    assert filament["filament_type"] == ["PLA"]
    assert machine["default_print_profile"] == STOCK_PROCESS
    machine["printer_settings_id"] = MACHINE
    machine["inherits"] = ""
    process.update({
        "name": PROCESS, "from": "user", "inherits": STOCK_PROCESS,
        "print_settings_id": PROCESS, "compatible_printers": [MACHINE],
        "layer_height": "0.1", "initial_layer_print_height": "0.1",
        "wall_loops": "6", "top_shell_layers": "8", "bottom_shell_layers": "8",
        "sparse_infill_density": "100%", "sparse_infill_pattern": "zig-zag",
        "enable_support": "0", "enable_prime_tower": "1",
        "prime_tower_width": "35", "prime_tower_brim_width": "3",
        "flush_into_infill": "0", "flush_into_objects": "0",
        "brim_type": "no_brim", "print_sequence": "by layer",
        "description": "Solid PLA keychains: six walls, 0.10 mm layers, stock P1S 0.2 mm lineage. Physical strength and hardware fit untested.",
    })
    for key, value in {
        "initial_layer_speed": "20", "initial_layer_infill_speed": "30",
        "outer_wall_speed": "40", "inner_wall_speed": "60",
        "top_surface_speed": "30", "sparse_infill_speed": "60",
        "internal_solid_infill_speed": "60",
        "default_acceleration": "3000", "outer_wall_acceleration": "1500",
    }.items():
        if key not in process or not isinstance(process[key], list):
            raise ValueError(f"Unexpected stock process value shape: {key}")
        process[key] = [value] * len(process[key])
    profiles = work / "profiles"
    machine_path, process_path = profiles / "machine.json", profiles / "process.json"
    write_json(machine_path, machine)
    write_json(process_path, process)
    filament_paths = []
    filaments = []
    for slot, (name, color) in enumerate(palette, 1):
        current = copy.deepcopy(filament)
        current.update({
            "name": f"Generic PLA {name} @P1S 0.2", "from": "user",
            "inherits": STOCK_FILAMENT, "compatible_printers": [MACHINE],
            "filament_colour": [color],
            "filament_settings_id": [f"Generic PLA {name} @P1S 0.2"],
        })
        path = profiles / f"filament-{slot}.json"
        write_json(path, current)
        filament_paths.append(path)
        filaments.append(current)
    return machine, process, filaments, machine_path, process_path, filament_paths, sources


def slot_for(variant, part):
    if part == "white_body":
        return 1
    if part == "light_inlay":
        return 4
    if part == "inlay" and variant not in {"octocat", "haku"}:
        return 3
    return 2


def child(parent, name, attributes=None, text=None):
    node = ET.SubElement(parent, f"{{{CORE}}}{name}", attributes or {})
    node.text = text
    return node


def meta(parent, key, value):
    return ET.SubElement(parent, "metadata", {"key": key, "value": str(value)})


def make_seed(path, selected, machine, process, filaments):
    palette, flush_matrix = project_materials(selected)
    count = len(palette)
    model = ET.Element(f"{{{CORE}}}model", {"unit": "millimeter"})
    child(model, "metadata", {"name": "Application"}, f"BambuStudio-{VERSION}")
    child(model, "metadata", {"name": "BambuStudio:3mfVersion"}, "1")
    child(model, "metadata", {"name": "Title"}, path.stem.removesuffix("-seed") + " - P1S 0.2 AMS PLA")
    child(model, "metadata", {"name": "Description"}, "Unchanged color-separated keychains; metal hardware is excluded.")
    resources, build = child(model, "resources"), child(model, "build")
    settings = ET.Element("config")
    plate = ET.Element("plate")
    meta(plate, "plater_id", 1)
    meta(plate, "plater_name", "P1S 0.2 AMS PLA")
    meta(plate, "locked", "false")
    meta(plate, "bed_type", "Textured PEI Plate")
    assignments = []
    for index, key in enumerate(selected):
        variant, slug, title = VARIANTS[key]
        report = json.loads((ROOT / "validation" / f"validation-{variant}.json").read_text())
        parts = parts_for(variant)
        object_id = 100 + index
        object_settings = ET.SubElement(settings, "object", {"id": str(object_id)})
        meta(object_settings, "name", title)
        meta(object_settings, "extruder", 1)
        ids = []
        for part_index, part in enumerate(parts):
            part_id = 10 + index * 4 + part_index
            ids.append(part_id)
            info = report["parts"][part]
            source = ROOT / info["file"]
            mesh = trimesh.load_mesh(source, process=True)
            assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
            assert np.allclose(mesh.bounds, info["bounds_mm"], atol=2e-5)
            slot = slot_for(variant, part)
            obj = child(resources, "object", {"id": str(part_id), "type": "model"})
            geometry = child(obj, "mesh")
            vertices, triangles = child(geometry, "vertices"), child(geometry, "triangles")
            for x, y, z in mesh.vertices:
                child(vertices, "vertex", {"x": f"{x:.9g}", "y": f"{y:.9g}", "z": f"{z:.9g}"})
            for a, b, c in mesh.faces:
                child(triangles, "triangle", {"v1": str(a), "v2": str(b), "v3": str(c)})
            name = f"{variant}/{part}"
            part_settings = ET.SubElement(object_settings, "part", {"id": str(part_id), "subtype": "normal_part"})
            meta(part_settings, "name", name)
            meta(part_settings, "matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1")
            meta(part_settings, "extruder", slot)
            meta(part_settings, "source_file", source.name)
            assignments.append({"name": name, "slot": slot, "source": str(source.relative_to(ROOT))})
        assembly = child(resources, "object", {"id": str(object_id), "type": "model"})
        components = child(assembly, "components")
        for part_id in ids:
            child(components, "component", {"objectid": str(part_id)})
        x = 128 + (index - (len(selected) - 1) / 2) * 32
        child(build, "item", {
            "objectid": str(object_id), "printable": "1",
            "transform": f"1 0 0 0 1 0 0 0 1 {x} 100 0",
        })
        instance = ET.SubElement(plate, "model_instance")
        meta(instance, "object_id", object_id)
        meta(instance, "instance_id", 0)
        meta(instance, "identify_id", index + 1)
    settings.append(plate)
    preset_metadata = {"type", "name", "from", "inherits", "instantiation", "setting_id", "description", "compatible_printers"}
    seed_config = {
        key: value for profile in (machine, process) for key, value in profile.items()
        if key not in preset_metadata
    }
    seed_config.update({
        "printer_settings_id": MACHINE, "printer_model": "Bambu Lab P1S",
        "printer_variant": "0.2", "nozzle_diameter": ["0.2"],
        "print_settings_id": PROCESS,
        "filament_colour": [color for _, color in palette],
        "filament_settings_id": [item["name"] for item in filaments],
        "filament_type": ["PLA"] * count, "filament_diameter": ["1.75"] * count,
        "filament_map": ["1"] * count,
        "inherits_group": [STOCK_PROCESS, *([STOCK_FILAMENT] * count), ""],
        "different_settings_to_system": [""] * (count + 2),
        "print_compatible_printers": [MACHINE],
        "curr_bed_type": "Textured PEI Plate",
        "flush_volumes_matrix": [str(value) for value in flush_matrix],
        "flush_volumes_vector": ["140"] * (count * 2),
        "flush_multiplier": "1",
        "wipe_tower_x": ["175"], "wipe_tower_y": ["160"],
    })
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
            '<Default Extension="config" ContentType="application/octet-stream"/></Types>'
        ))
        archive.writestr("_rels/.rels", (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-model" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
        ))
        archive.writestr("3D/3dmodel.model", ET.tostring(model, encoding="utf-8", xml_declaration=True))
        archive.writestr("Metadata/model_settings.config", ET.tostring(settings, encoding="utf-8", xml_declaration=True))
        archive.writestr("Metadata/project_settings.config", json.dumps(seed_config))
    return assignments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bambu", required=True, type=Path, help="Official Bambu Studio executable.")
    parser.add_argument("--profiles", required=True, type=Path, help="The application's Resources/profiles/BBL directory, never user profiles.")
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".work" / "slicer")
    parser.add_argument("--only", choices=PROJECTS, nargs="+", help="Build selected projects, preserving every other file.")
    args = parser.parse_args()
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = str(work / "home")
    (work / "home").mkdir(exist_ok=True)
    (work / "data").mkdir(exist_ok=True)
    base = [str(args.bambu.resolve()), "--datadir", str(work / "data"), "--debug", "3"]
    result = subprocess.run(base + ["--help"], cwd=work, env=env, capture_output=True, text=True, check=True)
    if f"BambuStudio-{VERSION}:" not in result.stdout:
        raise RuntimeError(f"Use the validated Bambu Studio {VERSION} release.")
    accepted = json.loads((ROOT / "validation/accepted-meshes.json").read_text())
    for name, expected in accepted["parts"].items():
        path = ROOT / "print-package/STL" / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, f"Accepted mesh changed: {name}"
    destination = ROOT / "print-package" / "projects"
    destination.mkdir(parents=True, exist_ok=True)
    for name, selected in PROJECTS.items():
        if args.only and name not in args.only:
            continue
        palette, _ = project_materials(selected)
        machine, process, filaments, machine_path, process_path, filament_paths, sources = configured_profiles(
            args.profiles.resolve(), work / name, palette,
        )
        seed = work / f"{name}-seed.3mf"
        assignments = make_seed(seed, selected, machine, process, filaments)
        target = destination / f"{name}-P1S-0.2-AMS-PLA.3mf"
        log = work / f"{name}-export.log"
        (work / f"{name}-export").mkdir(exist_ok=True)
        candidate = work / f"{name}-export" / target.name
        command = base + [
            "--load-settings", f"{machine_path};{process_path}",
            "--load-filaments", ";".join(str(path) for path in filament_paths),
            "--arrange", "0", "--orient", "0",
            "--export-3mf", target.name, "--outputdir", str(work / f"{name}-export"),
            str(seed),
        ]
        with log.open("w") as output:
            result = subprocess.run(command, cwd=work, env=env, stdout=output, stderr=subprocess.STDOUT)
        if result.returncode or not candidate.is_file():
            raise RuntimeError(f"Bambu Studio export failed ({result.returncode}); inspect {log}")
        with zipfile.ZipFile(candidate) as archive:
            config = json.loads(archive.read("Metadata/project_settings.config"))
            assert config["printer_settings_id"] == MACHINE, config.get("printer_settings_id")
            assert config["nozzle_diameter"] == ["0.2"], config.get("nozzle_diameter")
            assert config["filament_colour"] == [color for _, color in palette], config.get("filament_colour")
        shutil.copyfile(candidate, target)
        print(f"Exported with Bambu Studio: {target.name} ({len(assignments)} aligned parts)")
    with (ROOT / "print-package/parts-and-colors.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["Part", "Project filament slot", "Color", "Display RGB", "Source STL", "Print project"])
        for key, (variant, _, _) in VARIANTS.items():
            palette, _ = project_materials([key])
            report = json.loads((ROOT / "validation" / f"validation-{variant}.json").read_text())
            for part, info in report["parts"].items():
                if part == "blank":
                    continue
                slot = slot_for(variant, part)
                color, rgb = palette[slot - 1]
                project = key if key in ("chun", *ADDITIONS) else "all-three"
                writer.writerow([f"{variant}/{part}", slot, color, rgb, info["file"].removeprefix("print-package/"),
                                 f"projects/{project}-P1S-0.2-AMS-PLA.3mf"])
    write_json(ROOT / "validation/profile-provenance.json", {
        "bambu_studio_version": VERSION,
        "release": f"https://github.com/bambulab/BambuStudio/releases/tag/v{VERSION}",
        "machine": MACHINE, "official_machine_default_process": STOCK_PROCESS,
        "process": PROCESS, "filament_parent": STOCK_FILAMENT,
        "physical_printer_used": False, "account_or_device_profile_used": False,
        "stock_resource_sha256": sources,
        "process_overrides": {key: process[key] for key in [
            "layer_height", "initial_layer_print_height", "wall_loops", "top_shell_layers",
            "bottom_shell_layers", "sparse_infill_density", "sparse_infill_pattern",
            "outer_wall_speed", "inner_wall_speed", "top_surface_speed",
            "enable_support", "enable_prime_tower", "flush_into_infill", "flush_into_objects",
        ]},
        "palette": [{"slot": slot, "color": name, "rgb": color} for slot, (name, color) in enumerate(PALETTE, 1)],
        "bed": "Textured PEI Plate; select your actual bed surface before printing.",
        "flush_volumes_mm3_from_row_to_column": FLUSH_MATRIX,
        "separate_chun_project": {
            "project": "print-package/projects/chun-P1S-0.2-AMS-PLA.3mf",
            "palette": [{"slot": slot, "color": name, "rgb": color} for slot, (name, color) in enumerate(CHUN_PALETTE, 1)],
            "flush_volumes_mm3_from_row_to_column": CHUN_FLUSH_MATRIX,
            "note": "Separate white/black/red project. The original three-design set retains white/black/green/light green. Map or change the physical red spool; five simultaneous colors do not fit one four-slot AMS.",
        },
        "separate_haku_project": {
            "project": "print-package/projects/haku-P1S-0.2-AMS-PLA.3mf",
            "palette": [{"slot": slot, "color": name, "rgb": color} for slot, (name, color) in enumerate(PALETTE[:2], 1)],
        },
        "separate_iisou_project": {
            "project": "print-package/projects/iisou-P1S-0.2-AMS-PLA.3mf",
            "palette": [{"slot": slot, "color": name, "rgb": color} for slot, (name, color) in enumerate(IISOU_PALETTE, 1)],
            "note": "Iisou uses white/black/green in slots 1/2/3. Mirrored three-quarter Ducky and its peacock tail are green line art; no yellow or orange filament is needed.",
        },
        "flush_note": "Conservative starting volumes; actual pigment transitions still need a physical first print.",
    })


if __name__ == "__main__":
    main()
