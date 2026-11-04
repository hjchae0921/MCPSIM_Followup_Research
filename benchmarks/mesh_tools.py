"""Gmsh-only helpers for benchmark CAD, physical groups, and review artifacts.

This module is independent of the application, prompts, and physics libraries.
The meshes are geometry drafts, not evidence of FE solution convergence.
"""

from contextlib import contextmanager
import json
import math
from pathlib import Path

import gmsh
import numpy as np


@contextmanager
def model(name):
    gmsh.initialize(interruptible=False)
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setNumber("General.NumThreads", 1)
    try:
        gmsh.model.add(name)
        yield gmsh.model.occ
    finally:
        gmsh.finalize()


def positive(**values):
    if any(not math.isfinite(v) or v <= 0 for v in values.values()):
        raise ValueError("Dimensions and mesh size must be finite and positive.")


def flat_at(tag, axis, value, tolerance=1e-5):
    box = gmsh.model.getBoundingBox(2, tag)
    return abs(box[axis] - value) < tolerance and abs(box[axis + 3] - value) < tolerance


def surfaces(volumes):
    selected = set(volumes)
    exterior, interior = [], []
    for _, tag in gmsh.model.getEntities(2):
        owners = selected.intersection(map(int, gmsh.model.getAdjacencies(2, tag)[0]))
        if len(owners) == 1:
            exterior.append(tag)
        elif len(owners) == 2:
            interior.append(tag)
        elif owners:
            raise ValueError("A face cannot join more than two solid volumes.")
    return exterior, interior


def label(volume_groups, boundary_groups):
    """Use exactly one material tag per volume and one tag per exterior face."""
    volumes = [v for entities in volume_groups.values() for v in entities]
    if len(volumes) != len(set(volumes)):
        raise ValueError("Material groups must not overlap.")
    if set(volumes) != {tag for _, tag in gmsh.model.getEntities(3)}:
        raise ValueError("Every solid needs a material group.")
    exterior, _ = surfaces(volumes)
    tagged = [s for entities in boundary_groups.values() for s in entities]
    if len(tagged) != len(set(tagged)) or set(tagged) != set(exterior):
        raise ValueError("Boundary groups must partition the whole exterior.")
    result = {}
    for dim, groups in ((3, volume_groups), (2, boundary_groups)):
        for name, entities in groups.items():
            if not entities:
                raise ValueError(f"Empty Physical Group: {name}")
            tag = len(result) + 1
            gmsh.model.addPhysicalGroup(dim, sorted(entities), tag, name)
            result[name] = {"dim": dim, "tags": [tag], "entities": sorted(entities)}
    return result


def refine_short_edges(mesh_size):
    for _, tag in gmsh.model.getEntities(1):
        if gmsh.model.getType(1, tag) != "Line":
            continue
        length = gmsh.model.occ.getMass(1, tag)
        if length < 2 * mesh_size:
            gmsh.model.mesh.setTransfiniteCurve(tag, max(3, math.ceil(length / mesh_size) + 1))


def preview():
    """Build compact actual-mesh surface data, including bonded internal faces."""
    node_tags, coordinates, _ = gmsh.model.mesh.getNodes()
    xyz = np.asarray(coordinates).reshape(-1, 3)
    index = {int(tag): i for i, tag in enumerate(node_tags)}
    volume_names, face_names = {}, {}
    for dim, tag in gmsh.model.getPhysicalGroups():
        name = gmsh.model.getPhysicalName(dim, tag)
        target = volume_names if dim == 3 else face_names
        for entity in gmsh.model.getEntitiesForPhysicalGroup(dim, tag):
            target[int(entity)] = name
    faces = []
    used = set()
    for _, entity in gmsh.model.getEntities(2):
        owners = [int(v) for v in gmsh.model.getAdjacencies(2, entity)[0] if int(v) in volume_names]
        if not owners:
            continue
        triangles = []
        kinds, _, arrays = gmsh.model.mesh.getElements(2, entity)
        for kind, array in zip(kinds, arrays):
            _, _, _, width, _, primary = gmsh.model.mesh.getElementProperties(int(kind))
            if primary != 3:
                raise ValueError("Preview currently expects triangular solid faces.")
            for row in np.asarray(array).reshape(-1, width):
                triangle = [index[int(n)] for n in row[:3]]
                used.update(triangle)
                triangles.append(triangle)
        faces.append({"entity": entity, "boundary_group": face_names.get(entity),
                      "material_group": volume_names[owners[0]], "internal": len(owners) == 2,
                      "triangles": triangles})
    # Exclude unused CAD construction points from both data and bounds.
    ordered = sorted(used)
    compact = {old: new for new, old in enumerate(ordered)}
    for face in faces:
        face["triangles"] = [[compact[n] for n in row] for row in face["triangles"]]
    coords = xyz[ordered]
    return {"nodes": coords.round(8).tolist(), "surfaces": faces,
            "bounds": coords.min(axis=0).tolist() + coords.max(axis=0).tolist()}


def export(output, parameters, groups, *, mesh_size, axes, details=None, expected_volume=None):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    volumes = [tag for _, tag in gmsh.model.getEntities(3)]
    total = sum(gmsh.model.occ.getMass(3, tag) for tag in volumes)
    if expected_volume is not None and not math.isclose(total, expected_volume, rel_tol=1e-8):
        raise ValueError(f"Unexpected CAD volume: {total}, expected {expected_volume}")
    gmsh.write(str(output / "geometry.brep"))
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    gmsh.option.setNumber("Mesh.ElementOrder", 1)
    gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
    refine_short_edges(mesh_size)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.optimize("Netgen")
    kinds, tag_arrays, _ = gmsh.model.mesh.getElements(3)
    if not len(kinds) or any(int(kind) != 4 for kind in kinds):
        raise ValueError("Draft meshes must contain linear tetrahedra only.")
    cell_tags = np.concatenate(tag_arrays)
    quality = gmsh.model.mesh.getElementQualities(cell_tags, "minSICN")
    if not np.isfinite(quality).all() or min(quality) <= 0:
        raise ValueError("Invalid or inverted tetrahedron detected.")
    for dim, tag in gmsh.model.getPhysicalGroups():
        elements = sum(len(a) for e in gmsh.model.getEntitiesForPhysicalGroup(dim, tag)
                       for a in gmsh.model.mesh.getElements(dim, int(e))[1])
        if not elements:
            raise ValueError(f"Physical Group {gmsh.model.getPhysicalName(dim, tag)} has no mesh elements")
    gmsh.write(str(output / "model.msh"))
    data = preview()
    (output / "preview.json").write_text(json.dumps(data, separators=(",", ":")) + "\n")
    node_tags, _, _ = gmsh.model.mesh.getNodes()
    _, internal = surfaces(volumes)
    metadata = {"status": "geometry_draft_for_review", "coordinate_unit": "mm",
                "parameters": parameters, "axes": axes, "groups": groups,
                "cad_volume_mm3": total,
                "internal_interfaces": internal,
                "mesh": {"nodes": len(node_tags), "tetrahedra": len(cell_tags),
                         "minimum_signed_quality": float(min(quality)), "bounds": data["bounds"]},
                "physics_status": "Deferred by user; no material or load values selected.",
                "mesh_note": "Geometry review mesh; solution convergence has not been assessed."}
    if details:
        metadata.update(details)
    (output / "geometry.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"mesh": str(output / "model.msh"), "tetrahedra": len(cell_tags),
                      "minimum_signed_quality": float(min(quality)), "groups": list(groups)}))
    return output / "model.msh"
