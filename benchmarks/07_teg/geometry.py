"""One 3D p/n thermocouple with conformal copper joints; dimensions in mm."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mesh_tools as mt


def build(output, *, leg_width=2.0, depth=2.0, leg_height=5.0,
          gap=2.0, copper_thickness=0.5, mesh_size=0.4):
    parameters = dict(leg_width=leg_width, depth=depth, leg_height=leg_height,
                      gap=gap, copper_thickness=copper_thickness, mesh_size=mesh_size)
    mt.positive(**parameters)
    w, t = leg_width, copper_thickness
    span, top_z = 2 * w + gap, leg_height + 2 * t
    with mt.model("one_pair_teg") as occ:
        p_leg = occ.addBox(0, 0, t, w, depth, leg_height)
        n_leg = occ.addBox(w + gap, 0, t, w, depth, leg_height)
        bridge = occ.addBox(0, 0, t + leg_height, span, depth, t)
        pad_a = occ.addBox(0, 0, 0, w, depth, t)
        pad_b = occ.addBox(w + gap, 0, 0, w, depth, t)
        _, maps = occ.fragment([(3, p_leg)], [(3, n_leg), (3, bridge), (3, pad_a), (3, pad_b)])
        occ.synchronize()
        regions = [[tag for dim, tag in items if dim == 3] for items in maps]
        volume_groups = {"P_Leg": regions[0], "N_Leg": regions[1],
                         "Copper": sorted(set(regions[2] + regions[3] + regions[4]))}
        volumes = [v for entities in volume_groups.values() for v in entities]
        exterior, internal = mt.surfaces(volumes)
        if len(internal) != 4:
            raise ValueError("Both legs must share conformal faces with their hot and cold copper contacts.")
        hot = [s for s in exterior if mt.flat_at(s, 2, top_z)]
        cold = [s for s in exterior if mt.flat_at(s, 2, 0)]
        import gmsh
        terminal_a = [s for s in cold if gmsh.model.occ.getCenterOfMass(2, s)[0] < span / 2]
        terminal_b = sorted(set(cold) - set(terminal_a))
        sides = sorted(set(exterior) - set(hot + terminal_a + terminal_b))
        groups = mt.label(volume_groups, {"Hot_Surface": hot, "Terminal_A": terminal_a,
                                          "Terminal_B": terminal_b, "Side_Surface": sides})
        expected = 2 * w * depth * leg_height + (span + 2 * w) * depth * t
        return mt.export(output, parameters, groups, mesh_size=mesh_size, expected_volume=expected,
                         axes={"x": "p/n leg separation", "y": "depth", "z": "cold-to-hot direction"},
                         details={"intended_family": "Thermoelectric generator",
                                  "thermal_cold_groups": ["Terminal_A", "Terminal_B"],
                                  "topology": "P leg and N leg connected by one hot copper bridge; separate cold copper pads.",
                                  "contact": "Shared CAD faces and shared mesh nodes; no contact resistance or ceramic domains.",
                                  "boundary_note": "Cold thermal faces are Terminal_A and Terminal_B; no overlapping Cold_Surface tag."})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    for name, default in (("leg-width", 2.0), ("depth", 2.0), ("leg-height", 5.0),
                          ("gap", 2.0), ("copper-thickness", 0.5), ("mesh-size", 0.4)):
        parser.add_argument("--" + name, type=float, default=default)
    build(**vars(parser.parse_args()))
