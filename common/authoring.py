"""Card field scopes and server-derived HITL progress, independent of model prose.

Targets are stable field identifiers; named list items use their approved names or ids.
They are dialogue metadata, not additional fields in approved physics/coder cards.
"""


def selection_targets():
    return ['problem.'+key for key in ('type','unknowns','linearity','time_dependence','history_dependence',
            'dimension','coupling.type','coupling.dependencies')]+[
        'materials.constitutive_models.'+key for key in ('model','fields','symmetry')]


def space_targets(selection):
    return [f'unknowns.{name}.{key}' for name in selection['problem']['unknowns']
        for key in ('quantity','shape','function_space.family','function_space.degree')]+[
        'state_variables.'+key for key in ('name','symbol','shape','unit','function_space.family','function_space.degree')]


def material_targets(formulation):
    return [f'constitutive_parameters.{p["name"]}.{key}'
        for p in formulation['constitutive_parameters'] for key in ('regions','value','unit')]


def boundary_targets(formulation,unknowns):
    return [f'{scope}.{p["name"]}.{key}' for scope in ('boundary_parameters','source_parameters')
        for p in formulation[scope] for key in ('requirement','regions')]+[
        f'dirichlet_conditions.{u["name"]}.{key}' for u in unknowns for key in ('requirement','regions','components')]


def value_targets(rows):
    return [f'draft.{r["id"]}.{key}' for r in rows for key in ('value','unit')]


def solver_targets(selection):
    linear=('type','ksp_type','pc_type','factor_solver','rtol','atol','max_iterations','options')
    if selection['problem']['linearity']=='linear':return ['solver.linear.'+k for k in linear]
    return ['solver.nonlinear.'+k for k in ('method','line_search','rtol','atol','stol','max_iterations','options')]+[
        'solver.nonlinear.linear_solver.'+k for k in linear]


def progress(state):
    """Only validated objects and explicit approval state determine readiness."""
    stage=state.get('stage','selection_review')
    form=state.get('formulation')
    approved=[name for name,key in [('selection','confirmed_selection'),('function_space','functionspace_card'),
        ('material','material_card'),('boundary_parameters','boundary_parameter_assessment'),
        ('boundary_values','boundary_value_card'),('solver','solver_card')] if state.get(key) is not None]
    if form is not None and (state.get('saved_files') or (state.get('lookup') or {}).get('status')=='ready'):
        approved.insert(1,'formulation')
    stages={
        'selection_review':('selection','turns'),
        'function_space_review':('function_space','functionspace_turns'),
        'material_review':('material','material_turns'),
        'boundary_parameter_review':('boundary_parameters','boundary_parameter_turns'),
        'boundary_value_review':('boundary_values','boundary_value_turns'),
        'solver_review':('solver','solver_turns'),
    }
    if stage=='complete':
        return {'stage':approved[-1] if approved else 'selection','status':'approved',
                'question_targets':[],'approved_stages':approved}
    if stage in ('expert_review','revise_formulation','generate_formulation'):
        return {'stage':'formulation','status':'ready_for_review' if stage=='expert_review' and form is not None else 'processing',
                'question_targets':[],'approved_stages':approved}
    if stage not in stages:
        return {'stage':stage,'status':'processing','question_targets':[],'approved_stages':approved}
    name,key=stages[stage];turns=state.get(key,[]);reply=turns[-1]['response'] if turns else {}
    if name=='selection':ready=reply.get('kind') in ('proposal','registration_request') and bool(reply.get('spec'))
    elif name in ('function_space','material'):ready=bool(reply.get('proposed_card'))
    elif name=='boundary_parameters':
        from boundary_condition_agent.parameter_selection import ready as conditions_ready
        assessment=reply.get('assessment',{})
        ready=conditions_ready(assessment)
    elif name=='boundary_values':
        draft=state.get('boundary_value_draft',[]);rows=state.get('boundary_value_requirements',[])
        ready=len(draft)==len(rows) and {d.get('id') for d in draft}=={r['id'] for r in rows} and all(
            d.get('value') is not None and d.get('unit') is not None for d in draft)
    else:ready=bool(reply.get('proposed_card') or reply.get('recommendations'))
    question=reply.get('question')
    targets=(question or {}).get('targets',[]) if isinstance(question,dict) else reply.get('targets',reply.get('question_targets',[]))
    return {'stage':name,'status':'ready_for_review' if ready else 'needs_input',
            'question_targets':targets,'approved_stages':approved}
