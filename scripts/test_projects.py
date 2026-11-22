import unittest
import hashlib
import json

import trimesh

from designs import ADDITIONS, VARIANTS
from package_models import ROOT, project_materials, slot_for
from validate_projects import check_toolpaths


class ProjectTests(unittest.TestCase):
    def test_original_print_files_are_byte_identical(self):
        baseline = json.loads((ROOT / "validation/preserved-originals.json").read_text())
        for name, expected in baseline["files"].items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)
        black = (ROOT / "print-package/STL/01-git-branch/black_back-black.stl").read_bytes()
        for variant in ADDITIONS:
            self.assertEqual((ROOT / "print-package/STL" / VARIANTS[variant][1] / "black_back-black.stl").read_bytes(), black)

    def test_haku_retains_goggles_face_gap_and_both_mouth_details_below_center(self):
        trace = json.loads((ROOT / "validation/haku-trace.json").read_text())
        self.assertGreater(trace["reference_pixel_mask_iou"], 0.985)
        icon = trimesh.load_mesh(ROOT / "print-package/STL/05-haku/inlay-black.stl", process=True)
        self.assertLess(icon.bounds[1, 1], 0)
        self.assertGreater(icon.bounds[0, 1] + 14, 2.5)
        self.assertAlmostEqual(icon.extents[0], 13.2, places=4)
        parts = sorted(icon.split(), key=lambda mesh: mesh.volume, reverse=True)
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0].euler_number, -4, "Two goggle gaps and the white lower face must remain.")
        for mouth in parts[1:]:
            self.assertGreater(mouth.extents[0], 0.6)
            self.assertGreater(mouth.extents[1], 1.5)
            self.assertEqual(mouth.euler_number, 2)

    def test_new_palettes_keep_white_black_green_stable_without_yellow(self):
        palette, matrix = project_materials(["iisou"])
        self.assertEqual([color for _, color in palette], ["#F6F5EE", "#161616", "#238636"])
        self.assertEqual(len(matrix), 9)
        self.assertEqual(slot_for("iisou", "inlay"), 3)
        self.assertEqual(len(project_materials(["haku"])[0]), 2)
        for mixed in [["iisou", "hatsu"], ["haku", "iisou"], ["iisou", "chun"]]:
            with self.subTest(mixed=mixed), self.assertRaisesRegex(ValueError, "separate"):
                project_materials(mixed)

    def test_iisou_retains_official_ducky_with_a_peacock_fan(self):
        source = json.loads((ROOT / "validation/ducky-source.json").read_text())
        self.assertGreater(source["silhouette_pixel_iou"], 0.995)
        mesh = trimesh.load_mesh(ROOT / "print-package/STL/06-iisou/inlay-green.stl", process=True)
        components = mesh.split()
        self.assertTrue(any(part.bounds[1, 1] > 11 for part in components), "The feather fan must be above, not over, Ducky.")
        self.assertTrue(any(part.extents[0] > 10 and part.extents[1] > 10 and part.bounds[1, 1] < 2 for part in components),
                        "Ducky must remain a separate intact outline.")
        eyes = [part for part in components if 0.5 < part.extents[0] < 2.2 and 0.8 < part.extents[1] < 2.2]
        self.assertEqual(len(eyes), 2, "Both visible three-quarter eyes must survive as separate printable components.")

    def test_chun_cannot_enter_a_combined_five_color_project(self):
        with self.assertRaisesRegex(ValueError, "separate"):
            project_materials(["git-branch", "invertocat", "hatsu", "chun"])

    def test_chun_white_cat_has_head_body_and_tail_but_no_circle(self):
        inlay = trimesh.load_mesh(ROOT / "print-package/STL/04-chun/inlay-red.stl", process=True)
        components = sorted(inlay.split(), key=lambda mesh: mesh.bounds[0, 1])
        self.assertEqual(len(components), 2, "Only the upper glyph and standalone cat may remain.")
        cat, glyph = components
        self.assertGreater(glyph.bounds[0, 1], cat.bounds[1, 1])
        self.assertTrue(cat.is_watertight and cat.is_winding_consistent)
        segments = trimesh.intersections.mesh_plane(cat, [0, 0, 1], [0, 0, 16.1])[:, :, :2]

        def contains_source_point(px, py):
            x, y = (px - 49) * 11 / 98, 0.5 - py * 11 / 98
            crossings = 0
            for (ax, ay), (bx, by) in segments:
                if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
                    crossings += 1
            return crossings % 2 == 1

        for point in [(49, 47), (49, 88), (17, 69)]:
            self.assertTrue(contains_source_point(*point), f"Missing head, body or tail at {point}")
        for point in [(4, 49), (94, 49), (49, 5)]:
            self.assertFalse(contains_source_point(*point), f"The former circle remains at {point}")
        self.assertFalse((ROOT / "print-package/STL/04-chun/logo_inlay-black.stl").exists())

    def test_model_extrusion_and_ams_must_both_use_red(self):
        gcode = b"""M620 S1A
    T1
T1000
; layer num/total_layer_count: 1/3
; OBJECT_ID: 1
; FEATURE: Outer wall
G1 X120 Y100 E.02
; layer num/total_layer_count: 2/3
M620 S0A
T0
; FEATURE: Outer wall
G1 X120 Y100 E.02
; layer num/total_layer_count: 3/3
G1 X120 Y100 E.02
M620 S1A
T1
; FEATURE: Top surface
G1 X121 Y98 E.02
M620 S2A
T2
; FEATURE: Custom
G1 X10 Y20 E2
; FEATURE: Prime tower
G1 X180 Y170 E.02
; FEATURE: Top surface
G1 X125 Y102 E.02
"""
        layers = {0: {2}, 1: {1}, 2: {1, 2, 3}}
        result = check_toolpaths(gcode, layers)
        self.assertTrue(result["actual_object_extrusion_matches_layer_colors"])
        with self.assertRaisesRegex(AssertionError, "object extrusion tools"):
            check_toolpaths(gcode.replace(b"T2\n", b"T0\n"), layers)
        with self.assertRaisesRegex(AssertionError, "AMS selectors"):
            check_toolpaths(gcode.replace(b"M620 S2A", b"M620 S0A"), layers)
        with self.assertRaisesRegex(AssertionError, "object extrusion tools"):
            check_toolpaths(gcode.replace(b"; FEATURE: Top surface", b"; FEATURE: Prime tower"), layers)


if __name__ == "__main__":
    unittest.main()
