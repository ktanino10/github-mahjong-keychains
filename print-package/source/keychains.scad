// Dimensions are millimeters. The metal chain and rings are not printed.
variant = "git_branch"; // See scripts/designs.py for the additive design inventory.
part = "assembled";    // assembled, white_body, black_back, inlay, light_inlay, blank

body_width = 21;
body_height = 28;
body_thickness = 16.5;
corner_radius = 2.45;
edge_chamfer = 0.4;
back_thickness = 5.5;
inlay_depth = 0.8;
lug_height = 5;
lug_center_y = body_height / 2 + 3;
lug_radius = 5;
hole_diameter = 4.6;
hole_chamfer = 0.3;

$fn = 96;
epsilon = 0.01;
slice = 0.001;

module rounded_profile(width, height, radius) {
    offset(r = radius)
        square([width - 2 * radius, height - 2 * radius], center = true);
}

module body_solid() {
    hull() {
        linear_extrude(slice)
            rounded_profile(body_width - 2 * edge_chamfer,
                            body_height - 2 * edge_chamfer,
                            corner_radius - edge_chamfer);
        translate([0, 0, edge_chamfer])
            linear_extrude(body_thickness - 2 * edge_chamfer)
                rounded_profile(body_width, body_height, corner_radius);
        translate([0, 0, body_thickness - slice])
            linear_extrude(slice)
                rounded_profile(body_width - 2 * edge_chamfer,
                                body_height - 2 * edge_chamfer,
                                corner_radius - edge_chamfer);
    }
}

module lug_profile() {
    hull() {
        translate([0, lug_center_y]) circle(r = lug_radius);
        translate([-3.5, body_height / 2 - 2]) circle(r = 3);
        translate([3.5, body_height / 2 - 2]) circle(r = 3);
    }
}

module lug_solid() {
    hull() {
        linear_extrude(slice)
            offset(delta = -hole_chamfer) lug_profile();
        translate([0, 0, hole_chamfer])
            linear_extrude(lug_height - 2 * hole_chamfer)
                lug_profile();
        translate([0, 0, lug_height - slice])
            linear_extrude(slice)
                offset(delta = -hole_chamfer) lug_profile();
    }
}

module blank() {
    difference() {
        union() {
            body_solid();
            lug_solid();
        }
        translate([0, lug_center_y, -epsilon])
            cylinder(h = body_thickness + 2 * epsilon, d = hole_diameter);
        translate([0, lug_center_y, -epsilon])
            cylinder(h = hole_chamfer + epsilon,
                     d1 = hole_diameter + 2 * hole_chamfer + 2 * epsilon,
                     d2 = hole_diameter);
        translate([0, lug_center_y, lug_height - hole_chamfer])
            cylinder(h = hole_chamfer + epsilon, d1 = hole_diameter,
                     d2 = hole_diameter + 2 * hole_chamfer + 2 * epsilon);
    }
}

module hatsu_grid(shade = -1) {
    light_cells = [[1, 1, 0, 0], [1, 0, 0, 1], [1, 1, 0, 0]];
    for (row = [0:2], column = [0:3])
        if (shade == -1 || light_cells[row][column] == shade)
            translate([(column - 1.5) * 4.6, -0.6 - row * 4.6])
                offset(r = 0.18)
                    square([3.64, 3.64], center = true);
}

module artwork_original(layer = "all") {
    if (variant == "git_branch") {
        resize([0, 20], auto = true)
            import("assets/git-branch-24.svg", center = true);
    } else if (variant == "octocat") {
        resize([18.8, 0], auto = true)
            import("assets/github-invertocat.svg", center = true);
    } else if (variant == "hatsu") {
        if (layer != "light")
            translate([0, 8.1])
                offset(delta = 0.12, chamfer = true)
                    resize([0, 9.6], auto = true)
                        import("assets/hatsu.svg", center = true, $fn = 24);
        hatsu_grid(layer == "all" ? -1 : layer == "light" ? 1 : 0);
    } else if (variant == "chun") {
        // Retain the accepted glyph's source-frame transform when the lower logo changes.
        translate([-7.049664427392641, -11.84085168182418])
            scale(0.39926399049251327)
                import("assets/chun-custom.svg", center = false, dpi = 72);
    } else {
        assert(false, str("Unknown variant: ", variant));
    }
}

module duck_shape(details = false) {
    mirror([1, 0, 0])
        translate([-5.82625, -11.55])
            import(details ? "assets/iisou-ducky-details.svg" : "assets/iisou-ducky-silhouette.svg");
}

module ducky_artwork() {
    difference() {
        duck_shape();
        offset(delta = -0.48) duck_shape();
    }
    intersection() {
        duck_shape();
        duck_shape(true);
    }
}

module peacock_fan() {
    root = [0, -6.4];
    tips = [[-7.6, 2.8], [-6.2, 6.5], [-3.4, 9.1], [0, 9.7],
            [3.4, 9.1], [6.2, 6.5], [7.6, 2.8]];
    difference() {
        union() {
            for (tip = tips) {
                difference() {
                    hull() {
                        translate(root) circle(r = 0.32);
                        translate(tip) scale([1, 1.4]) circle(r = 1.15);
                    }
                    offset(delta = -0.48)
                        hull() {
                            translate(root) circle(r = 0.32);
                            translate(tip) scale([1, 1.4]) circle(r = 1.15);
                        }
                }
                translate(tip)
                    difference() {
                        scale([1, 1.4]) circle(r = 1.15);
                        scale([1, 1.3]) circle(r = 0.32);
                    }
                hull() {
                    translate(root) circle(r = 0.26);
                    translate([tip.x, tip.y - 1.5]) circle(r = 0.26);
                }
            }
        }
        offset(delta = 0.65) duck_shape();
    }
}

module artwork(layer = "all") {
    if (variant == "haku") {
        // The black graphic stays below center; all upper face area is blank.
        translate([0, -5.62])
            resize([13.2, 0], auto = true)
                import("assets/haku-supplied-icon.svg", center = true);
    } else if (variant == "iisou") {
        ducky_artwork();
        peacock_fan();
    } else {
        scale(body_width / 24) artwork_original(layer);
    }
}

module black_back() {
    intersection() {
        blank();
        translate([-50, -50, -epsilon])
            cube([100, 100, back_thickness + epsilon]);
    }
}

module white_body() {
    difference() {
        blank();
        black_back();
        translate([0, 0, body_thickness - inlay_depth])
            linear_extrude(inlay_depth + epsilon)
                artwork();
    }
}

module inlay(light = false, layer = "") {
    intersection() {
        blank();
        translate([0, 0, body_thickness - inlay_depth])
            linear_extrude(inlay_depth)
                artwork(layer != "" ? layer : light ? "light" : "dark");
    }
}

if (part == "black_back") {
    black_back();
} else if (part == "white_body") {
    white_body();
} else if (part == "inlay") {
    inlay();
} else if (part == "light_inlay") {
    assert(variant == "hatsu", "Light green is used only in the hatsu design");
    inlay(true);
} else if (part == "blank") {
    blank();
} else if (part == "assembled") {
    color("#191C1A") black_back();
    color("#F6F5EE") white_body();
    color(variant == "octocat" || variant == "haku" ? "#191C1A" : variant == "chun" ? "#B33220" : "#238636") inlay();
    if (variant == "hatsu") color("#9DD96C") inlay(true);
} else {
    assert(false, str("Unknown part: ", part));
}
