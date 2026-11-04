"""Generate review prose exclusively from a validated selection specification."""
from common.coupling import COUPLING

from .spec import normalized


def label(identifier):
    return identifier.replace('_', ' ')


def joined(items):
    items = list(items)
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return ' and '.join(items)
    return ', '.join(items[:-1]) + ', and ' + items[-1]


def describe_selection(value):
    """Validate first; never infer assumptions or use a model-written overview."""
    spec = normalized(value)
    p = spec['problem']
    fields = joined(label(name) for name in p['unknowns'])
    subject = 'primary unknown is' if len(p['unknowns']) == 1 else 'primary unknowns are'
    parts = [f"The proposed model is {p['dimension']}D {label(p['type'])}, formulated as a {p['linearity']} problem.",
        f'The {subject} {fields}.',
        ('It depends on physical time' if p['time_dependence'] == 'dependent' else 'It is independent of physical time') +
        (' and retains material history.' if p['history_dependence'] else ' and has no material history dependence.')]
    coupling = p['coupling']
    if coupling['type'] == COUPLING[0]:
        parts.append('This is a single-physics model.')
    else:
        kind = {COUPLING[1]: 'one-way', COUPLING[2]: 'fully coupled'}[coupling['type']]
        directions = joined(f"{label(dep['from'])} affects {label(dep['to'])}" for dep in coupling['dependencies'])
        parts.append(f'The model uses {kind} multiphysics coupling: {directions}.')
    for index, material in enumerate(spec['materials'], 1):
        models = joined(f"{label(model['symmetry'])} {label(model['model'])} for " +
            joined(label(name) for name in model['fields']) for model in material['constitutive_models'])
        parts.append(f'Material {index} uses {models}.')
    return ' '.join(parts)
