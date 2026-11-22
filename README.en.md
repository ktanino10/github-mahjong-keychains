# Mahjong keychains

**[日本語](README.md) | English**

Six designs: the original Git branch, GitHub Invertocat, Hatsu (發) with a 4-column × 3-row contribution grid, and **red Chun (中) with a red cat and no circle**, plus **no-text Haku** and **green peacock-inspired Ducky Iisou**. The original single Git branch design, all 13 existing STLs and all five existing projects are unchanged. Includes **configured Bambu Lab P1S · 0.2 mm nozzle · AMS · PLA project 3MFs**; no part repainting is needed. Not an official or endorsed GitHub product.

[Open the 360° viewer in English](https://ktanino10.github.io/github-mahjong-keychains/#en) · [日本語で表示](https://ktanino10.github.io/github-mahjong-keychains/#ja) · [Download standalone offline HTML](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/docs/index.html)

![Reference CG of all six designs with ball chains](docs/images/keychains-studio.png)

## Downloads

| Project | Printable parts | Colors used |
| --- | ---: | --- |
| [Original three-design set, unchanged](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/print-package/projects/all-three-P1S-0.2-AMS-PLA.3mf) | 10 | White, black, green, light green |
| [Chun, separate project](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/print-package/projects/chun-P1S-0.2-AMS-PLA.3mf) | 3 | White, black, red |
| [Haku: no text, low supplied icon](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/print-package/projects/haku-P1S-0.2-AMS-PLA.3mf) | 3 | White, black |
| [Iisou: front-facing Ducky with peacock tail](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/print-package/projects/iisou-P1S-0.2-AMS-PLA.3mf) | 3 | White, black, green |
| [Git branch](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/print-package/projects/git-branch-P1S-0.2-AMS-PLA.3mf) | 3 | White, black, green |
| [Invertocat](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/print-package/projects/invertocat-P1S-0.2-AMS-PLA.3mf) | 3 | White, black |
| [Hatsu](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/print-package/projects/hatsu-P1S-0.2-AMS-PLA.3mf) | 4 | White, black, green, light green |

[Print bundle ZIP: seven projects, nineteen STLs, bilingual instructions and offline HTML](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/docs/downloads/github-mahjong-keychains-P1S-0.2-AMS-PLA.zip)

**The original three-design set, Chun, Haku and Iisou are separate print projects.** All six designs require five colors: white, black, green, light green and red. One four-slot AMS cannot hold all five at once; no all-six five-color print project is supplied. Change to a red spool when needed for Chun and map each project's colors to the actual AMS spools. The five original files, assignments and URLs are retained.

These are **not** generic geometry-only 3MFs with display colors. They retain printer, process, PLA settings, per-part filament numbers, placement and flushing volumes. Metal hardware is excluded from every STL and 3MF. Ready-to-send machine-specific G-code is not distributed.

### The two additions

**Haku / white dragon has no text on its physical face.** Its dark outline is traced from the supplied 135 × 110 image, retaining both white goggle openings, the white lower face and both black mouth details. The icon is 13.2 mm wide with approximately 2.87 mm bottom clearance; even its top stays below the tile center. The upper half is blank, with no rectangular background patch. No “Haku,” “Copilot,” character or number is modeled. This legacy Copilot-style artwork is not represented as a current approved logo.

**Iisou / one bamboo uses front-facing Ducky with a green peacock-inspired tail.** It uses the left-hand, front-facing Ducky view from the [official Brand Toolkit](https://brand.github.com/graphic-elements/mascots), without mirroring or repositioning the eyes. Its rounded head/body, both eyes and broad bill are retained, with the original symmetrical seven-feather fan behind it. This is flat printable line art, without gradients, yellow/orange filament or numerals. It is adapted custom artwork, not a new official mascot or colorway.

![Front cross sections of the actual Haku and Iisou meshes](docs/images/new-designs-front.png)

## Printing

1. Open a 3MF **as a project** in **Bambu Studio 02.09.01.70**, not as geometry only. Do not independently arrange its component parts.
2. Confirm **Bambu Lab P1S 0.2 nozzle** and the numbered PLA colors below. The four original projects retain their shared palette; Chun uses white/black/red, Haku white/black, and Iisou white/black/green.
3. Match the project's filament numbers to the **actual PLA spools in your AMS** in the print dialog. Part assignments are saved; physical tray mapping remains a hardware-specific step. Confirm that the installed nozzle really is 0.2 mm.
4. The saved bed is **Textured PEI Plate**, with stock Generic PLA temperatures of 220 °C nozzle and 55 °C bed. If your actual plate or filament needs different temperatures, select the appropriate settings and re-slice.
5. Start with a single-design project. Inspect the ear, inlays, filament assignments and prime tower in Preview, then inspect the first physical print for hole clearance, layer bonding, damage and color contamination before fitting hardware.

The repository's build and verification scripts do not connect to a printer, transmit jobs or start printing.

### Filament map

**Four original projects: unchanged shared palette**

| Project slot | Color | Display RGB | Assignment |
| ---: | --- | --- | --- |
| 1 | White | `#F6F5EE` | White body of every design |
| 2 | Black | `#161616` | Rear, entire ear and Invertocat inlay |
| 3 | Green | `#238636` | Git branch, Hatsu and dark grid cells |
| 4 | Light green | `#9DD96C` | Light Hatsu grid cells |

**Separate Chun project: its own three-color palette**

| Project slot | Color | Display RGB | Assignment |
| ---: | --- | --- | --- |
| 1 | White | `#F6F5EE` | White body |
| 2 | Black | `#161616` | Shared rear and entire ear |
| 3 | Red | `#B33220` | Upper Chun glyph and standalone cat: head, body and tail |

Chun has **three parts and three colors**: white body, shared black rear and red inlay. The red STL contains two disconnected closed solids, the glyph and cat, aligned with the white body's recesses. Do not arrange them separately. The obsolete black-circle face part is removed. No gradient printing is required.

**Separate Haku and Iisou projects**

| Project slot | Color / RGB | Haku: two colors | Iisou: three colors |
| ---: | --- | --- | --- |
| 1 | White `#F6F5EE` | White body | White body |
| 2 | Black `#161616` | Shared rear/ear and low face icon | Shared rear/ear |
| 3 | Green `#238636` | Unused | Ducky and peacock-inspired fan |

Each addition has three STL parts: body, rear and inlay. An inlay STL contains multiple aligned disconnected solids; do not split or auto-arrange them independently. Haku saves only two materials and Iisou only three, without an unused fourth material.

**Removing the circle and coloring the cat red does not automatically permit modification, combining it with text, making keychains, publishing or distributing them.** Check GitHub's written permission covering this modification and use separately under the [official guidelines](https://brand.github.com/foundations/logo).

RGB values are visual references, not a guarantee of any manufacturer's PLA shade. See the [per-part color table](print-package/parts-and-colors.csv).

### Saved process

0.10 mm normal and first layers; six walls; eight top and bottom layers; 100% Rectilinear infill; no supports; black rear down; prime tower enabled. Outer walls run at 40 mm/s, inner walls at 60 mm/s and top surfaces at 30 mm/s, retaining the stock 0.2 mm Generic PLA volumetric limit of 1.6 mm³/s. Flushing into the object or its infill is disabled to reduce color contamination.

The machine is the official **P1S 0.2 mm** preset. Its process inherits `0.10mm Standard @BBL X1C 0.2 nozzle`: this is the **shared process explicitly designated as the default by the official P1S 0.2 mm profile**, not a switch to an X1 printer. Every material inherits `Generic PLA @0.2 nozzle`. [Settings and provenance](validation/profile-provenance.json)

Flushing volumes are conservative starting values, with more flushing from dark to light. Actual pigment transitions still need a physical test. Slicer estimates are approximately **11 h 12 min / 54 g** for the original combined project, **4 h 12 min / 20.4 g** for Chun, **4 h 17 min / 20.9 g** for Haku and **4 h 15 min / 20.1 g** for Iisou. All include flushing and the tower; these are not measured print results.

## Dimensions and hardware

| Feature | Dimension |
| --- | --- |
| Tile body, height × width × thickness | **28 × 21 × 16.5 mm** |
| Height including ear | 36 mm |
| Ear thickness / hole diameter | 5 mm / Ø4.6 mm |
| Black rear / white side of body | 5.5 mm / 11 mm |
| Shared black/white boundary | z = 5.5 mm |
| Surface inlays | z = 15.7–16.5 mm |

All 13 original printable STLs and five original project 3MFs are byte-identical to accepted commit `d6cb1dc`. Haku and Iisou use the same common blank and byte-identical black rear/ear STL. The ear outline, body size, front/back proportions, original logos, glyphs, grid and red Chun/cat without the circle are unchanged. No transverse body hole was added. [SHA-256 hashes of the 18 preserved files](validation/preserved-originals.json). The AMOS SMART reference matches only its [listed external dimensions](https://www.alban.co.jp/products/detail/682), not its material, weight or strength.

**Default: purchased-style ball chain.** The [product listing](https://www.amazon.co.jp/dp/B0DN6JW6LK) specifies 2.4 mm balls and 120 mm chain length. The viewer shows a loop through the existing ear. Pitch, bead count, connector dimensions and drape are approximate. Silver is an illustrative finish, not an inference about the purchased color. Detach the connector, pass the free beaded end through the hole and reconnect; do not force the connector itself through the ear.

**Alternate: wire-gate swivel clasp.** The [referenced product](https://www.amazon.co.jp/dp/B0FX47WYC4) has a rounded clasp, thin wire gate, short axial swivel and lower jump ring. Its title lists 42 mm, while the bullets give 44 × 18 mm. Internal proportions are approximate. The lower-ring bore and wire thickness are unknown, so **this option is a fit-unverified visual reference only**. Ball-chain mounting remains the supported design intent. No marketing images or order information are redistributed.

**Physical printing, actual hardware fit and strength are untested.** PLA can soften in heat. Avoid strong pulls and stop using a part if it chips or delaminates. Do not use this model for load-bearing or safety-critical purposes.

## Using the HTML

The **日本語 / English** buttons switch the full interface, including settings, notices, dynamic status, errors and accessible labels. Download `index.html` and open it in a browser: the models, Three.js, fonts and poster are embedded, so viewing needs **no external requests**. “Save HTML” preserves the chosen language in another standalone copy. The 3MF download links require an internet connection.

Drag, use one finger or arrow keys to rotate. Scroll, pinch or press `+` / `-` to zoom; `Home` fits the view. Choose designs, front/back/side/angle views, hardware visibility and type, and auto rotation. Auto rotation is off initially.

**Viewing** six designs together does not mean **printing** all six with one AMS. Haku displays two colors, Iisou white/black/green, and the all-six view five colors with the separate-project warning. The original single Git branch motif is retained.

[Haku / Japanese](docs/images/viewer-ja-haku.png) · [Haku / English](docs/images/viewer-en-haku.png) · [Iisou / Japanese](docs/images/viewer-ja-iisou.png) · [Iisou / English](docs/images/viewer-en-iisou.png) · [Existing Chun](docs/images/viewer-en-chun.png)

## Verification and rebuilding

The finished Haku and Iisou projects were **reopened and sliced with the official Bambu Studio 02.09.01.70 CLI without external presets or setting overrides**. Both have 165 layers and empty plate-warning fields: black at layers 1–55, white at 56–157, then white/black for Haku and white/green for Iisou at 158–165. Configuration was isolated from personal settings, printers and accounts. The five original files retain their same-version reopen/slice evidence after SHA-256 verification.

All three parts of each addition are closed positive-volume meshes whose sum matches the accepted blank. Boolean checks reject volumetric overlap/missing material, and 3MF vertices, triangle connectivity, winding and coordinates are checked against the STLs. [Haku geometry](validation/validation-haku.json) · [Iisou geometry](validation/validation-iisou.json) · [Supplied-icon trace comparison](validation/haku-trace.json) · [Official Ducky source and adaptation](validation/ducky-source.json)

Actual final-layer G-code extrusions are checked for the icons, eyes, bill and feathers, accounting for the saved stock nozzle XY offset. Iisou's inlay comparison allows 0.025 mm (one pixel) of rasterization error and retains the raw measurements. White gaps are checked against the unexpanded footprint. These are line-width-based raster estimates, not a physical bead or strength simulation. [Measured checks](validation/top-layer-checks.json) · [Haku layer 165](docs/images/haku-sliced-top.png) · [Iisou layer 165](docs/images/iisou-sliced-top.png)

All three Chun parts and both red connected components are closed, positive-volume meshes. Their summed volume matches the accepted common blank; Boolean checks find no volumetric overlap or missing material at a 0.00002 mm STL precision tolerance. Vertex correspondence, triangle connectivity/winding, dimensions and alignment are also checked against the 3MF and GLB. [Chun geometry checks](validation/validation-chun.json)

The upper Chun retains its shape, placement and triangle connectivity. Cross-section checks confirm the cat's head, body and tail, and reject red material where the old circle stood. `prepare_assets.py` uses OpenSCAD to subtract the black logo from its convex hull, then keeps only the white connected region containing the head. A disconnected tiny hull-edge fragment is excluded.

[Slicer results](validation/slicer-checks.json) · [Accepted STL SHA-256 hashes](validation/accepted-meshes.json) · [Browser results](validation/browser-checks.json) · [Download SHA-256 hashes](https://github.com/ktanino10/github-mahjong-keychains/blob/main/validation/deliverables.json)

The [official slicer download SHA-256](validation/slicer-distribution.json) was verified as well. The application, personal profiles and local verification G-code are not distributed.

The desktop CLI emits some misleading diagnostics about optional expanded-profile lookups and an already-present flushing matrix. These are classified, not hidden, in the verification JSON. Saved colors, actual used filaments, every layer and the empty plate-warning field are independently checked. This does not claim that every diagnostic log line is warning-free.

Development uses Python 3.13, Node.js, OpenSCAD with the Manifold backend, Blender and the Bambu Studio release above. Run the commands below from a clone of this repository; the ZIP is a print bundle. **Rebuilding is unnecessary for printing.**

```sh
python3.13 -m pip install -r requirements.txt
python3.13 scripts/prepare_assets.py
python3.13 scripts/build_variant.py haku
python3.13 scripts/build_variant.py iisou
python3.13 scripts/preview_faces.py
python3.13 -m unittest discover -s scripts -p test_projects.py
python3.13 scripts/package_models.py --only haku iisou --bambu "$BAMBU" --profiles "$BBL_PROFILES"
python3.13 scripts/validate_projects.py --only haku iisou --bambu "$BAMBU"
python3.13 scripts/inspect_top_layers.py
"$BLENDER" --background --factory-startup --python-exit-code 1 --python scripts/render_scene.py
"$BLENDER" --background --factory-startup --python-exit-code 1 --python viewer/export_viewer.py
python3.13 viewer/check_geometry.py
python3.13 scripts/make_deliverables.py --poster-only
cd viewer
npm ci
npm run build
npm test
cd ..
python3.13 scripts/make_deliverables.py
python3.13 scripts/audit_public.py
```

`BAMBU`, `BLENDER` and `OPENSCAD` are executable paths. `BBL_PROFILES` is the **application-supplied** `Resources/profiles/BBL` directory, never a personal printer-profile directory. Intermediate files stay under `.work/`. The example regenerates only Haku and Iisou, preserving the original 13 STLs and five projects. Omit `--only haku iisou` from verification only when re-slicing everything. Printing or repackaging does not require STL regeneration. Clean outline SVGs are included; the original upload and system fonts are not needed. `trace_haku.py` and `trace_ducky.py` accept an explicitly designated reference image only when retracing is wanted.

For an Iisou-only update, use `inspect_top_layers.py --only iisou` as well. It retains Haku's prior evidence only when the unchanged project's SHA-256 matches.

Not an official GitHub product. **The code's MIT license does not freely license the logos, glyph or derived model geometry as a whole.** See [asset-specific rights and licenses](ASSET-LICENSES.md).
