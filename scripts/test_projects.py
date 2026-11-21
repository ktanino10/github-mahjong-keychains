import unittest

import numpy as np
import trimesh

from package_models import ROOT, project_materials
from validate_projects import canonical_faces, check_toolpaths


class ProjectTests(unittest.TestCase):
    def test_chun_cannot_enter_a_combined_five_color_project(self):
        with self.assertRaisesRegex(ValueError, "separate"):
            project_materials(["git-branch", "invertocat", "hatsu", "chun"])

    def test_chun_lower_logo_is_the_same_uniformly_scaled_invertocat(self):
        glyph = trimesh.load_mesh(ROOT / "print-package/STL/04-chun/inlay-red.stl", process=True)
        logo = trimesh.load_mesh(ROOT / "print-package/STL/04-chun/logo_inlay-black.stl", process=True)
        self.assertEqual(len(glyph.split()), 1, "The red part must contain only the glyph.")
        self.assertEqual(len(logo.split()), 1, "The black face part must contain only the circular logo.")
        self.assertGreater(glyph.bounds[0, 1], logo.bounds[1, 1])
        original = trimesh.load_mesh(ROOT / "print-package/STL/02-octocat/inlay-black.stl", process=True)
        scale = logo.extents[0] / original.extents[0]
        original.vertices[:, :2] *= scale
        original.vertices[:, :2] += logo.bounds.mean(axis=0)[:2] - original.bounds.mean(axis=0)[:2]
        self.assertEqual(len(logo.vertices), len(original.vertices))
        self.assertEqual(len(logo.faces), len(original.faces))
        distances, indices = original.kdtree.query(logo.vertices)
        self.assertLess(float(distances.max()), 2e-5)
        self.assertEqual(len(np.unique(indices)), len(original.vertices))
        # Planar caps may retriangulate after scaling; every contour wall must match.
        side_faces = np.ptp(logo.triangles[:, :, 2], axis=1) > 2e-5
        original_sides = np.ptp(original.triangles[:, :, 2], axis=1) > 2e-5
        np.testing.assert_array_equal(
            canonical_faces(indices[logo.faces[side_faces]]), canonical_faces(original.faces[original_sides]),
        )
        self.assertTrue(logo.is_watertight and logo.is_winding_consistent)
        self.assertLess(abs(logo.volume - original.volume), 1e-4)
        np.testing.assert_allclose(logo.bounds, original.bounds, atol=2e-5)

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
