import unittest

from package_models import project_materials
from validate_projects import check_toolpaths


class ProjectTests(unittest.TestCase):
    def test_chun_cannot_enter_a_combined_five_color_project(self):
        with self.assertRaisesRegex(ValueError, "separate"):
            project_materials(["git-branch", "invertocat", "hatsu", "chun"])

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
M620 S2A
T2
; FEATURE: Custom
G1 X10 Y20 E2
; FEATURE: Prime tower
G1 X180 Y170 E.02
; FEATURE: Top surface
G1 X125 Y102 E.02
"""
        layers = {0: {2}, 1: {1}, 2: {1, 3}}
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
