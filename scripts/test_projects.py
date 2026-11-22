import unittest

import trimesh

from package_models import ROOT, project_materials
from validate_projects import check_toolpaths


class ProjectTests(unittest.TestCase):
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
