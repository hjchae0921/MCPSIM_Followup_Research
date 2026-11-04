"""3D two-layer piezoelectric cantilever with a bonded shared interface; mm."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mesh_tools as mt


def build(output, *, length=40.0, width=5.0, layer_thickness=0.5, mesh_size=0.4):
    parameters = dict(length=length, width=width, layer_thickness=layer_thickness, mesh_size=mesh_size)
    mt.positive(**parameters)
    t = layer_thickness
    with mt.model("piezoelectric_bimorph") as occ:
        bottom = occ.addBox(0, 0, 0, length, width, t)
        top = occ.addBox(0, 0, t, length, width, t)
        _, maps = occ.fragment([(3, bottom)], [(3, top)])
        occ.synchronize()
        volume_groups = {"Piezo_Bottom": [tag for dim, tag in maps[0] if dim == 3],
                         "Piezo_Top": [tag for dim, tag in maps[1] if dim == 3]}
        volumes = [v for entities in volume_groups.values() for v in entities]
        exterior, internal = mt.surfaces(volumes)
        if len(internal) != 1:
            raise ValueError("The layers must share exactly one bonded interface.")
        clamp = [s for s in exterior if mt.flat_at(s, 0, 0)]
        free = [s for s in exterior if mt.flat_at(s, 0, length)]
        electrode_top = [s for s in exterior if mt.flat_at(s, 2, 2 * t)]
        electrode_bottom = [s for s in exterior if mt.flat_at(s, 2, 0)]
        side = sorted(set(exterior) - set(clamp + free + electrode_top + electrode_bottom))
        groups = mt.label(volume_groups, {"Clamp_End": clamp, "Free_End": free,
                                          "Electrode_Top": electrode_top, "Electrode_Bottom": electrode_bottom,
                                          "Side_Surface": side})
        return mt.export(output, parameters, groups, mesh_size=mesh_size,
                         expected_volume=length * width * 2 * t,
                         axes={"x": "cantilever span", "y": "width", "z": "layer stack"},
                         details={"intended_family": "Piezoelectric cantilever actuator",
                                  "contact": "Shared CAD interface and mesh nodes; perfect bond.",
                                  "electrodes": "Surface groups only; no conductor volume or internal electrode.",
                                  "poling": "Directions and tensors are physics inputs to be selected later."})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    for name, default in (("length", 40.0), ("width", 5.0), ("layer-thickness", 0.5), ("mesh-size", 0.4)):
        parser.add_argument("--" + name, type=float, default=default)
    build(**vars(parser.parse_args()))
