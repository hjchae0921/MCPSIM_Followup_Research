"""Deterministic card projection. No model calls or changes to approved physics."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from boundary_condition_agent import values
from functionspace_agent import agent as spaces
from material_agent import agent as materials
from solver_agent import agent as solvers
from codegen.boundary_card import card as componentwise_boundary_card
from problem_selection_agent.spec import normalized

ROOT=Path(__file__).resolve().parent.parent
STAGES=(('mesh','1_Mesh_Prompt.txt'),('function_space','2_Functionspace_Prompt.txt'),
    ('weak_form','3_WeakForm_Prompt.txt'),('boundary_conditions','4_BC_Prompt.txt'),('solve','5_Solve_Prompt.txt'))
APPROVED_KEYS=('confirmed_selection','functionspace_card','material_card','boundary_parameter_assessment',
    'boundary_value_card','formulation','solver_card','solver_input_signature')


def source_signature(state):
    value={key:state.get(key) for key in APPROVED_KEYS}
    value['mesh']=state['mesh']
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def split(state,mesh_path):
    """Use approved values verbatim; preserve actual region dimensions and tags."""
    if state.get('stage')!='complete' or state.get('can_continue'):
        raise ValueError("Please finalize up to the solver first, then run the coding.")
    if any(state.get(key) is None for key in APPROVED_KEYS) or not state.get('solver_input_signature'):
        raise ValueError("Final approval is required for the physical, function space, material, boundary value, and solver settings.")
    spec=normalized(state['confirmed_selection']);problem=spec['problem']
    summary=state['mesh']['summary'];path=Path(mesh_path).resolve()
    if not path.is_file():raise ValueError("Could not find the mesh file for the finalized conversation.")
    if not summary.get('coordinate_unit'):raise ValueError("Please finalize the length unit of the mesh coordinates first.")
    if problem['dimension']!=summary['dimension']:raise ValueError("The mesh and physical specification have different dimensions.")
    if problem['time_dependence']!='independent':
        raise ValueError("For a time-dependent problem, the time interval, time integration, and initial conditions have not yet been finalized on the web. Complete those specifications and then connect them.")
    if problem['history_dependence'] or state['functionspace_card']['state_variables']:
        raise ValueError("The initial conditions and update equations for the internal state variables have not yet been finalized on the web. Complete those specifications and then connect them.")
    fs=spaces.check_card(state['functionspace_card'],spec)
    materials.check_card(state['material_card'],state['formulation'],summary)
    assessment=values.check_assessment(state['boundary_parameter_assessment'],state['formulation'],summary,fs['unknowns'])
    rows=values.requirements(assessment,state['formulation'],summary,fs['unknowns'])
    expected=values.card(state.get('boundary_value_draft',[]),rows) if 'boundary_value_draft' in state else None
    # Older approved checkpoints may have no draft; their approved card must still cover every requirement.
    actual=state['boundary_value_card']
    expected_rows={k:[] for k in ('boundary_parameters','source_parameters','dirichlet_conditions')}
    for row in rows:
        identity={k:row[k] for k in (('field','components','region') if row['scope']=='dirichlet_conditions' else ('name','region'))}
        matches=[item for item in actual[row['scope']] if all(item.get(k)==v for k,v in identity.items())]
        if len(matches)!=1 or matches[0].get('value') is None or matches[0].get('unit') is None:
            raise ValueError("The final boundary value card does not match the approved conditions and regions.")
        expected_rows[row['scope']].append(matches[0])
    if any(len(expected_rows[k])!=len(actual[k]) for k in expected_rows) or expected is not None and expected!=actual:
        raise ValueError("The boundary value card contains values different from the approved requirements. Please review it again.")
    formulation=deepcopy(state['formulation'])
    fields=[{k:u[k] for k in ('name','quantity','shape')} for u in fs['unknowns']]
    if {f['field'] for f in formulation.get('weak_form') or []}!={u['name'] for u in fields}:
        raise ValueError("An approved weak form is required for every unknown field.")
    regions={}
    for group in summary.get('volume_groups',[])+summary.get('boundary_groups',[]):
        value={k:deepcopy(group[k]) for k in ('dim','tags')}
        if group['name'] in regions and regions[group['name']]!=value:raise ValueError("Names of mesh regions with different dimensions are duplicated.")
        regions[group['name']]=value
    mesh={'mesh':{'path':str(path),'coordinate_unit':summary['coordinate_unit'],
        'target_coordinate_unit':summary['coordinate_unit'],'dim':summary['dimension'],'regions':regions}}
    # Parameter names are the exact join keys from the approved formulation, not guessed aliases.
    def bind(scope,items):
        symbols={p['name']:p['symbol'] for p in formulation[scope]}
        return [dict(deepcopy(item),symbol=symbols[item['name']]) for item in items]
    shared={'linearity':problem['linearity'],'time_type':'steady','dimension':problem['dimension'],
        'type':problem['type'],'coupling':deepcopy(problem['coupling'])}
    weak={'problem':shared,'unknowns':fields,
        'constitutive_parameters':bind('constitutive_parameters',state['material_card']['constitutive_parameters']),
        'boundary_parameters':bind('boundary_parameters',actual['boundary_parameters']),
        'source_parameters':bind('source_parameters',actual['source_parameters']),
        'parameter_usage':{scope:[{key:deepcopy(p[key]) for key in ('name','requirement','regions')}
            for p in assessment[scope]]
            for scope in ('boundary_parameters','source_parameters')},
        'formulation':formulation}
    boundary=componentwise_boundary_card(fields,actual['dirichlet_conditions'])
    solve={'problem':shared,'unknowns':fields,'state_variables':deepcopy(fs['state_variables']),
        'solver':deepcopy(state['solver_card']['solver'])}
    return dict(zip((name for name,_ in STAGES),(mesh,fs,weak,boundary,solve)))


def templates(variant="no_card_descriptions"):
    return {name:(ROOT/'prompt_templates/no_card_descriptions'/filename).read_text() for name,filename in STAGES}


def render(source,card,graph,previous):
    """Fill existing input slots. All system/procedure/rules text stays byte-for-byte intact."""
    if source.count('{{CARD_JSON}}')!=1 or source.count('{{API_KNOWLEDGE_GRAPH}}')!=1:
        raise ValueError("Please check the card and KG placeholders in the existing prompt.")
    replacements={'CARD_JSON':json.dumps(card,ensure_ascii=False,indent=2),'API_KNOWLEDGE_GRAPH':graph,
        'PREVIOUS_STAGE_CODE':'```python\n'+previous+'\n```','FORMULATION':''}
    # The approved formulation is carried inside the weak-form card; no equations are rewritten.
    import re
    text=re.sub(r'\{\{([A-Z_]+)\}\}',lambda m:replacements[m[1]],source)
    header,sep,user=text.partition('=== USER MESSAGE ===\n')
    if not sep:raise ValueError("The prompt is missing the USER MESSAGE delimiter.")
    return header.removeprefix('=== SYSTEM MESSAGE ===\n').strip(),user.strip(),text
