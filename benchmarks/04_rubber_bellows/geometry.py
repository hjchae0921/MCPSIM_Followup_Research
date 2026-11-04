"""Full 3D corrugated rubber tube with end collars; dimensions in mm."""

import argparse
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mesh_tools as mt
import gmsh


def build(output, *, mean_radius=15.0, wall=2.0, amplitude=3.0,
          wave_count=4, wave_length=10.0, collar_length=5.0, mesh_size=1.25):
    parameters = dict(mean_radius=mean_radius, wall=wall, amplitude=amplitude,
                      wave_count=wave_count, wave_length=wave_length,
                      collar_length=collar_length, mesh_size=mesh_size)
    mt.positive(**parameters)
    if wave_count != int(wave_count) or mean_radius - amplitude - wall / 2 <= 0:
        raise ValueError("Use a whole number of waves and a strictly positive bore radius.")
    length = wave_count * wave_length
    total_length = length + 2 * collar_length
    base_radius = mean_radius - amplitude
    with mt.model("rubber_bellows") as occ:
        def point(radius, z):
            return occ.addPoint(radius, 0, z)

        count = int(wave_count) * 24
        z_values = [collar_length + length * i / count for i in range(count + 1)]
        radii = [mean_radius - amplitude * math.cos(2 * math.pi * (z - collar_length) / wave_length)
                 for z in z_values]
        outer = [point(radius + wall / 2, z) for radius, z in zip(radii, z_values)]
        inner = [point(radius - wall / 2, z) for radius, z in zip(radii, z_values)]
        outer_start = point(base_radius + wall / 2, 0)
        outer_end = point(base_radius + wall / 2, total_length)
        inner_start = point(base_radius - wall / 2, 0)
        inner_end = point(base_radius - wall / 2, total_length)
        # Half-wave patches keep each spline surface monotone in radius.
        # This avoids one long oscillating CAD parametrization for all waves.
        outer_waves = [occ.addSpline(outer[i:i + 13], tangents=[0, 0, 1, 0, 0, 1])
                       for i in range(0, count, 12)]
        inner_waves = [occ.addSpline(inner[i:i + 13], tangents=[0, 0, 1, 0, 0, 1])
                       for i in range(0, count, 12)]
        curves = [occ.addLine(outer_start, outer[0]), *outer_waves,
                  occ.addLine(outer[-1], outer_end), occ.addLine(outer_end, inner_end),
                  occ.addLine(inner_end, inner[-1]), *[-c for c in reversed(inner_waves)],
                  occ.addLine(inner[0], inner_start), occ.addLine(inner_start, outer_start)]
        profile = occ.addPlaneSurface([occ.addCurveLoop(curves)])
        # Retain quarter seams: a single periodic spline surface can fail Gmsh's
        # periodic surface mesher. These are conformal partitions of one solid.
        revolved = occ.revolve([(2, profile)], 0, 0, 0, 0, 0, 1, math.pi / 2)
        quarter = [(3, tag) for dim, tag in revolved if dim == 3]
        if len(quarter) != 1:
            raise ValueError("The meridional profile must form one quarter solid.")
        pieces = quarter.copy()
        for i in range(1, 4):
            copied = occ.copy(quarter)
            occ.rotate(copied, 0, 0, 0, 0, 0, 1, i * math.pi / 2)
            pieces.extend(copied)
        partitioned, _ = occ.fragment(pieces[:1], pieces[1:])
        volumes = [tag for dim, tag in partitioned if dim == 3]
        occ.synchronize()
        if len(volumes) != 4:
            raise ValueError("The full-angle tube must retain four conformal quarter partitions.")
        exterior, _ = mt.surfaces(volumes)
        left = [s for s in exterior if mt.flat_at(s, 2, 0)]
        right = [s for s in exterior if mt.flat_at(s, 2, total_length)]
        walls = sorted(set(exterior) - set(left) - set(right))
        outer_faces, inner_faces = [], []
        for tag in walls:
            box = gmsh.model.getBoundingBox(2, tag)
            radius = max(abs(box[0]), abs(box[1]), abs(box[3]), abs(box[4]))
            # OCC spline bounding boxes include control-point overshoot, so classify
            # curved surfaces by their parametric midpoint, not just box extrema.
            low, high = gmsh.model.getParametrizationBounds(2, tag)
            sample = gmsh.model.getValue(2, tag, [(low[0] + high[0]) / 2,
                                                 (low[1] + high[1]) / 2])
            z = float(sample[2])
            r = math.hypot(float(sample[0]), float(sample[1]))
            expected_mid = base_radius if z <= collar_length or z >= collar_length + length else (
                mean_radius - amplitude * math.cos(2 * math.pi * (z - collar_length) / wave_length))
            if not math.isfinite(radius):
                raise ValueError("Invalid wall bounding box.")
            (outer_faces if r > expected_mid else inner_faces).append(tag)
        groups = mt.label({"Rubber": volumes}, {"Collar_Left": left, "Collar_Right": right,
                                                "Inner_Wall": inner_faces, "Outer_Wall": outer_faces})
        return mt.export(output, parameters, groups, mesh_size=mesh_size,
                         axes={"z": "axial extension", "x/y": "radial plane"},
                         details={"total_length_mm": total_length,
                                  "radial_extent_mm": [base_radius - wall / 2, mean_radius + amplitude + wall / 2],
                                  "profile": "r_mid(z) = mean_radius - amplitude*cos(2*pi*(z-collar_length)/wave_length), spline through 24 points per wave",
                                  "wall_definition": "Constant radial wall thickness; normal thickness varies along the corrugation.",
                                  "collar_groups": "End annular faces; inner/outer wall groups include the smooth collar walls.",
                                  "partition": "Four conformal quarter solids, all assigned to one Rubber Physical Group; no physical seams or gaps.",
                                  "intended_family": "Hyperelastic rubber bellows"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    for name, default in (("mean-radius", 15.0), ("wall", 2.0), ("amplitude", 3.0),
                          ("wave-length", 10.0), ("collar-length", 5.0), ("mesh-size", 1.25)):
        parser.add_argument("--" + name, type=float, default=default)
    parser.add_argument("--wave-count", type=int, default=4)
    build(**vars(parser.parse_args()))
