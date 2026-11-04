"""Read and atomically register a specification and formulation in one JSON file."""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import uuid

from .formulation import Formulation, StoredFormulation
from .spec import canonical, normalized


def check_formulation(value, spec, *, allow_legacy=False):
    model=StoredFormulation if allow_legacy else Formulation
    result = model.model_validate(value).model_dump(exclude_unset=allow_legacy)
    forms = result['weak_form']
    if not forms or {form['field'] for form in forms} != set(spec['problem']['unknowns']):
        raise ValueError('Weak-form fields must match the approved primary unknowns.')
    if result['constitutive'] is None:
        raise ValueError('Constitutive relations are required before saving.')
    return result


class Catalog:
    def __init__(self, root):
        self.root = Path(root)

    def entries(self):
        entries = []
        for path in sorted(self.root.rglob('*.json')):
            if any(part.startswith('.') for part in path.relative_to(self.root).parts):
                continue
            data = json.loads(path.read_text())
            if not isinstance(data, dict) or set(data) != {'problem', 'materials', 'formulation'}:
                continue
            spec = normalized({key:data[key] for key in ('problem','materials')})
            formula = check_formulation(data['formulation'],spec,allow_legacy=True)
            entries.append({'file':str(path.relative_to(self.root)), 'spec':spec, 'formulation':formula})
        return entries

    def choices(self):
        entries = self.entries()
        return {'types': sorted({entry['spec']['problem']['type'] for entry in entries}),
                'models': sorted({model['model'] for entry in entries for material in entry['spec']['materials']
                                  for model in material['constitutive_models']}),
                'selections': [{k: deepcopy(v) for k, v in entry.items() if k != 'formulation'} for entry in entries]}

    def lookup(self, spec, preferred_file=None):
        key = canonical(spec)
        ready = next((entry for entry in self.entries() if canonical(entry['spec']) == key
            and (preferred_file is None or entry['file'] == preferred_file)), None)
        if ready:
            return {'status': 'ready', **deepcopy(ready)}
        return {'status':'missing', 'file':None, 'formulation':None}

    def candidates(self, dimension, answers=None):
        from .questions import fixed_values
        answers=answers or {}
        for path,value in answers.items():
            if path not in fixed_values() or value not in fixed_values()[path]:
                raise ValueError('Check the user-confirmed physical choices.')
        def fits(spec):
            p=spec['problem']
            return p['dimension']==dimension and all(
                (p['coupling']['type'] if path=='problem.coupling.type' else p[path.removeprefix('problem.')])==value
                for path,value in answers.items())
        return [{'id':entry['file'],'spec':deepcopy(entry['spec'])} for entry in self.entries() if fits(entry['spec'])]

    def register(self, spec, formulation):
        spec = normalized(spec)
        formulation = check_formulation(formulation, spec)
        same=next((entry for entry in self.entries() if canonical(entry['spec'])==canonical(spec)
            and entry['formulation']==formulation),None)
        if same:
            return {'file':same['file']}
        symmetries = sorted({model['symmetry'] for material in spec['materials'] for model in material['constitutive_models']})
        name = re.sub(r'[^a-z0-9_]', '_', spec['problem']['type']+'_'+'_'.join(symmetries))[:150]
        self.root.mkdir(parents=True,exist_ok=True)
        staging = self.root / ('.pending_'+uuid.uuid4().hex+'.json')
        target = self.root / f'{name}_formulation.json'
        try:
            staging.write_text(json.dumps({**spec,'formulation':formulation},ensure_ascii=False,indent=2)+'\n')
            while True:
                try:
                    # Publish the complete file atomically without replacing an existing record.
                    os.link(staging,target)
                    break
                except FileExistsError:
                    target = self.root / f'{name}_{uuid.uuid4().hex[:12]}_formulation.json'
        finally:
            staging.unlink(missing_ok=True)
        return {'file':str(target.relative_to(self.root))}
