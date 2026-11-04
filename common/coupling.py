"""Canonical coupling identifiers and compatibility with saved specifications."""
from typing import Literal

COUPLING = ('single_physics', 'multi_physics_one_way', 'multi_physics_fully_coupled')
CouplingType = Literal['single_physics', 'multi_physics_one_way', 'multi_physics_fully_coupled']
ALIASES = {
    'multi_physics_\ub2e8\ubc29\ud5a5': COUPLING[1],
    'multi_physics_\uc591\ubc29\ud5a5': COUPLING[2],
    'multiphysics_one_way': COUPLING[1],
    'multiphysics_fully_coupled': COUPLING[2],
}


def normalized_coupling(value):
    """Translate legacy spellings; leave invalid values for schema validation."""
    return ALIASES.get(value, value) if isinstance(value, str) else value
