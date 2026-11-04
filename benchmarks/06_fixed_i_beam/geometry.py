"""3D I-section beam with separate end and thermal-surface groups; mm."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mesh_tools as mt


def build(output, *, length=300.0, height=40.0, width=30.0,
          flange_thickness=4.0, web_thickness=3.0, mesh_size=3.0):
    parameters = dict(length=length, height=height, width=width,
                      flange_thickness=flange_thickness, web_thickness=web_thickness,
                      mesh_size=mesh_size)
    mt.positive(**parameters)
    if 2 * flange_thickness >= height or web_thickness >= width:
        raise ValueError("The web and flanges need positive clear dimensions.")
    b, h, w = width / 2, height / 2, web_thickness / 2
    zi = h - flange_thickness
    with mt.model("fixed_i_beam") as occ:
        outline = [(-b, -h), (b, -h), (b, -zi), (w, -zi), (w, zi), (b, zi),
                   (b, h), (-b, h), (-b, zi), (-w, zi), (-w, -zi), (-b, -zi)]
        points = [occ.addPoint(0, y, z) for y, z in outline]
        curves = [occ.addLine(p, points[(i + 1) % len(points)]) for i, p in enumerate(points)]
        face = occ.addPlaneSurface([occ.addCurveLoop(curves)])
        volumes = [tag for dim, tag in occ.extrude([(2, face)], length, 0, 0) if dim == 3]
        occ.synchronize()
        exterior, _ = mt.surfaces(volumes)
        left = [s for s in exterior if mt.flat_at(s, 0, 0)]
        right = [s for s in exterior if mt.flat_at(s, 0, length)]
        top = [s for s in exterior if mt.flat_at(s, 2, h)]
        bottom = [s for s in exterior if mt.flat_at(s, 2, -h)]
        side = sorted(set(exterior) - set(left + right + top + bottom))
        groups = mt.label({"Beam": volumes}, {"End_Left": left, "End_Right": right,
                                              "Top_Surface": top, "Bottom_Surface": bottom,
                                              "Side_Surface": side})
        area = 2 * width * flange_thickness + (height - 2 * flange_thickness) * web_thickness
        return mt.export(output, parameters, groups, mesh_size=mesh_size, expected_volume=area * length,
                         axes={"x": "beam span", "y": "flange width", "z": "section height"},
                         details={"section_area_mm2": area,
                                  "intended_family": "Thermoelastic I beam fixed at both ends"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    for name, default in (("length", 300.0), ("height", 40.0), ("width", 30.0),
                          ("flange-thickness", 4.0), ("web-thickness", 3.0), ("mesh-size", 3.0)):
        parser.add_argument("--" + name, type=float, default=default)
    build(**vars(parser.parse_args()))
