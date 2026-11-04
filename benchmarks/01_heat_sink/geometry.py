"""Parametric 3D plate-fin heat sink. All geometry lengths are in mm.

Run with the project's Gmsh environment. This creates the prepared mesh used by
the authoring UI; it makes no model calls and does not approve any physics inputs.
"""

import argparse
import json
import math
from pathlib import Path

import gmsh


def build(output, *, length=80.0, width=60.0, base_thickness=5.0,
          fin_count=12, fin_thickness=2.0, fin_height=25.0, mesh_size=2.0):
    dimensions = [length, width, base_thickness, fin_thickness, fin_height, mesh_size]
    if any(not math.isfinite(value) or value <= 0 for value in dimensions) or fin_count < 1:
        raise ValueError("All dimensions and the fin count must be positive.")
    gap = (length - fin_count * fin_thickness) / (fin_count + 1)
    if gap <= 0:
        raise ValueError("Fins need positive clearance and end margins.")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    gmsh.initialize(interruptible=False)
    gmsh.option.setNumber("General.Terminal", 0)
    try:
        gmsh.model.add("plate_fin_heat_sink")
        current = [(3, gmsh.model.occ.addBox(0, 0, 0, length, width, base_thickness))]
        for i in range(fin_count):
            x = gap + i * (fin_thickness + gap)
            fin = gmsh.model.occ.addBox(x, 0, base_thickness, fin_thickness, width, fin_height)
            current, _ = gmsh.model.occ.fuse(current, [(3, fin)])
        gmsh.model.occ.synchronize()
        volumes = [tag for dim, tag in gmsh.model.getEntities(3)]
        if len(volumes) != 1:
            raise ValueError("The base and fins must form a single connected solid.")
        exterior = sorted({tag for dim, tag in gmsh.model.getBoundary(current, combined=True, oriented=False) if dim == 2})
        bottom, exposed = [], []
        for tag in exterior:
            box = gmsh.model.getBoundingBox(2, tag)
            (bottom if abs(box[2]) < 1e-5 and abs(box[5]) < 1e-5 else exposed).append(tag)
        if not bottom or not exposed:
            raise ValueError("Bottom and exposed boundary groups must be nonempty.")
        for dim, entities, tag, name in (
            (3, volumes, 1, "Solid"),
            (2, bottom, 2, "Base_Bottom"),
            (2, exposed, 3, "Exposed_Surface"),
        ):
            gmsh.model.addPhysicalGroup(dim, entities, tag, name)
        gmsh.write(str(output / "geometry.brep"))
        gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
        gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
        gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
        gmsh.model.mesh.generate(3)
        mesh = output / "model.msh"
        gmsh.write(str(mesh))
        expected_volume = length * width * base_thickness + fin_count * fin_thickness * width * fin_height
        actual_volume = sum(gmsh.model.occ.getMass(3, tag) for tag in volumes)
        if abs(actual_volume - expected_volume) > expected_volume * 1e-9:
            raise ValueError("CAD volume does not match the declared dimensions.")
        metadata = {
            "status": "draft_for_review", "coordinate_unit": "mm",
            "parameters": dict(length=length, width=width, base_thickness=base_thickness,
                               fin_count=fin_count, fin_thickness=fin_thickness,
                               fin_height=fin_height, mesh_size=mesh_size),
            "fin_gap_mm": gap, "cad_volume_mm3": actual_volume,
            "groups": {"Solid": {"dim": 3, "tags": [1]},
                       "Base_Bottom": {"dim": 2, "tags": [2]},
                       "Exposed_Surface": {"dim": 2, "tags": [3]}},
            "axes": {"x": "fin array direction", "y": "fin length", "z": "height"},
        }
        (output / "geometry.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(json.dumps({"mesh": str(mesh), "volume_mm3": actual_volume,
                          "groups": list(metadata["groups"])}, indent=2))
    finally:
        gmsh.finalize()
    return mesh


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    for name, default in (("length", 80.0), ("width", 60.0), ("base-thickness", 5.0),
                          ("fin-thickness", 2.0), ("fin-height", 25.0), ("mesh-size", 2.0)):
        parser.add_argument("--" + name, type=float, default=default)
    parser.add_argument("--fin-count", type=int, default=12)
    args = parser.parse_args()
    build(**vars(args))
