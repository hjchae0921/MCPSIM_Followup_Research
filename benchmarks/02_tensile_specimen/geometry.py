"""3D metal sheet-type dog-bone proposal, lengths in mm.

Nominal dimensions reference ASTM E8/E8M-13a Fig. 1 (sheet-type). The smooth
double-arc shoulder is an explicit modeling choice. This draft does not certify
the complete specimen or testing procedure against the current standard.
"""

import argparse
import json
import math
from pathlib import Path

import gmsh


def build(output, *, length=200.0, gauge_length=50.0, reduced_length=60.0,
          reduced_width=12.5, grip_width=20.0, thickness=3.0,
          shoulder_radius=15.0, mesh_size=2.0):
    parameters = dict(length=length, gauge_length=gauge_length, reduced_length=reduced_length,
                      reduced_width=reduced_width, grip_width=grip_width, thickness=thickness,
                      shoulder_radius=shoulder_radius, mesh_size=mesh_size)
    if any(not math.isfinite(v) or v <= 0 for v in parameters.values()):
        raise ValueError("All dimensions must be finite and positive.")
    if gauge_length > reduced_length or grip_width <= reduced_width:
        raise ValueError("Gauge length must fit in the reduced section; grips must be wider.")
    if length < 200 or reduced_length < 57 or shoulder_radius < 12.5:
        raise ValueError("The selected sheet-type baseline needs L>=200, A>=57 and R>=12.5 mm.")
    delta = (grip_width - reduced_width) / 2
    if delta >= 2 * shoulder_radius:
        raise ValueError("Shoulder rise is too large for the selected radius.")
    half_transition = math.sqrt(shoulder_radius * delta - delta ** 2 / 4)
    a = reduced_length / 2
    xm, xe = a + half_transition, a + 2 * half_transition
    grip_length = length / 2 - xe
    if grip_length < 50:
        raise ValueError("At least 50 mm of parallel grip section is required at each end.")
    yw, yg, ym = reduced_width / 2, grip_width / 2, (reduced_width + grip_width) / 4
    end = length / 2
    outline = [(-end, -yg), (-xe, -yg), (-xm, -ym), (-a, -yw),
               (a, -yw), (xm, -ym), (xe, -yg), (end, -yg),
               (end, yg), (xe, yg), (xm, ym), (a, yw),
               (-a, yw), (-xm, ym), (-xe, yg), (-end, yg)]
    centers = {1: (-xe, shoulder_radius - yg), 2: (-a, -yw - shoulder_radius),
               4: (a, -yw - shoulder_radius), 5: (xe, shoulder_radius - yg),
               9: (xe, yg - shoulder_radius), 10: (a, yw + shoulder_radius),
               12: (-a, yw + shoulder_radius), 13: (-xe, yg - shoulder_radius)}
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    gmsh.initialize(interruptible=False)
    gmsh.option.setNumber("General.Terminal", 0)
    try:
        gmsh.model.add("metal_flat_dogbone")
        occ = gmsh.model.occ
        points = [occ.addPoint(x, y, 0) for x, y in outline]
        curves = []
        for i, point in enumerate(points):
            following = points[(i + 1) % len(points)]
            if i in centers:
                x, y = centers[i]
                center = occ.addPoint(x, y, 0)
                curves.append(occ.addCircleArc(point, center, following))
            else:
                curves.append(occ.addLine(point, following))
        surface = occ.addPlaneSurface([occ.addCurveLoop(curves)])
        extruded = occ.extrude([(2, surface)], 0, 0, thickness)
        occ.synchronize()
        volumes = [tag for dim, tag in extruded if dim == 3]
        if len(volumes) != 1:
            raise ValueError("The specimen must be one connected solid.")
        boundaries = [tag for dim, tag in gmsh.model.getBoundary([(3, volumes[0])], oriented=False) if dim == 2]
        left, right, free = [], [], []
        for tag in boundaries:
            box = gmsh.model.getBoundingBox(2, tag)
            if abs(box[0] + end) < 1e-5 and abs(box[3] + end) < 1e-5:
                left.append(tag)
            elif abs(box[0] - end) < 1e-5 and abs(box[3] - end) < 1e-5:
                right.append(tag)
            else:
                free.append(tag)
        if not left or not right or not free:
            raise ValueError("Grip and free-surface groups must be nonempty.")
        for dim, entities, tag, name in ((3, volumes, 1, "Specimen"),
                                       (2, left, 2, "Grip_Left"), (2, right, 3, "Grip_Right"),
                                       (2, free, 4, "Free_Surface")):
            gmsh.model.addPhysicalGroup(dim, entities, tag, name)
        gmsh.write(str(output / "geometry.brep"))
        gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
        gmsh.option.setNumber("Mesh.MeshSizeMin", min(mesh_size, thickness / 2))
        gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
        # Refine thickness edges to resolve the 3D solid across its thickness.
        for _, tag in gmsh.model.getEntities(1):
            box = gmsh.model.getBoundingBox(1, tag)
            if box[3] - box[0] < 1e-5 and box[4] - box[1] < 1e-5:
                gmsh.model.mesh.setTransfiniteCurve(tag, max(3, math.ceil(thickness / mesh_size) + 1))
        gmsh.model.mesh.generate(3)
        mesh = output / "model.msh"
        gmsh.write(str(mesh))
        metadata = {
            "status": "draft_for_review", "coordinate_unit": "mm", "parameters": parameters,
            "shoulder_profile": "Two tangent circular arcs per shoulder; equal radii and horizontal endpoint tangents",
            "parallel_grip_length_mm": grip_length,
            "gauge_window_x_mm": [-gauge_length / 2, gauge_length / 2],
            "gauge_cross_section_mm2": reduced_width * thickness,
            "cad_volume_mm3": occ.getMass(3, volumes[0]),
            "axes": {"x": "tension axis", "y": "width", "z": "thickness"},
            "groups": {"Specimen": {"dim": 3, "tags": [1]}, "Grip_Left": {"dim": 2, "tags": [2]},
                       "Grip_Right": {"dim": 2, "tags": [3]}, "Free_Surface": {"dim": 2, "tags": [4]}},
            "dimension_reference": {"standard": "ASTM E8/E8M-13a", "figure": "Fig. 1, sheet-type",
                                    "url": "https://www.galvanizeit.com/uploads/ASTM-E-8-yr-13.pdf"},
            "note": "Nominal benchmark geometry with a proposed shoulder profile; dimensions and physics are not yet approved.",
        }
        (output / "geometry.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(json.dumps({"mesh": str(mesh), "parallel_grip_length_mm": grip_length,
                          "groups": list(metadata["groups"])}, indent=2))
    finally:
        gmsh.finalize()
    return mesh


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    for name, default in (("length", 200.0), ("gauge-length", 50.0), ("reduced-length", 60.0),
                          ("reduced-width", 12.5), ("grip-width", 20.0), ("thickness", 3.0),
                          ("shoulder-radius", 15.0), ("mesh-size", 2.0)):
        parser.add_argument("--" + name, type=float, default=default)
    build(**vars(parser.parse_args()))
