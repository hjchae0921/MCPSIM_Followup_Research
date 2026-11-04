"""Isolated libraries and mocked API fixtures; no paid calls."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, DEFAULT
from web import app
from problem_selection_agent.catalog import Catalog
from problem_selection_agent.service import ProblemSelectionService, SelectionError
from problem_selection_agent.spec import Selection, canonical, normalized, reply_model
from functionspace_agent import agent as space_agent
from material_agent import agent as material_agent
from common.dialogue import InputQuestion, ChoiceQuestion, RecommendationQuestion

def response(value):
    if isinstance(value,dict) and isinstance(value.get('response'),dict) and 'spec' in value['response']:
        from problem_selection_agent.questions import wire_assessment
        value={**value,'response':wire_assessment(value['response'])}
    if isinstance(value,dict) and isinstance(value.get('assessment'),dict):
        from boundary_condition_agent.parameter_selection import wire_reply
        value=wire_reply(value)
    return SimpleNamespace(model='test-served-model',usage=None,
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(value),refusal=None),finish_reason='stop')],
        model_dump_json=lambda **kwargs:json.dumps(value))

class AuthoringFixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.library=root/'library';self.library.mkdir()
        path=app.ROOT/'library/linear_elasticity_isotropic_formulation.json'
        shutil.copy(path,self.library/path.name)
        # Keep this test contract independent of user edits to live field names.
        fixture=json.loads((self.library/path.name).read_text())
        aliases={name:'displacement' for name in fixture['problem']['unknowns']}
        fixture['problem']['unknowns']=['displacement']
        for material in fixture['materials']:
            for model in material['constitutive_models']:
                model['fields']=[aliases.get(name,name) for name in model['fields']]
                model['model']='linear_elasticity'
        for form in fixture['formulation']['weak_form']:
            form['field']=aliases.get(form['field'],form['field'])
        for parameter in fixture['formulation']['boundary_parameters']:
            if parameter['name']=='prescribed_traction':parameter['name']='traction'
        (self.library/path.name).write_text(json.dumps(fixture))
        self.client=Mock()
        self.mesh={'id':'a'*32,'summary':{'dimension':3,'filename':'uploaded.msh','coordinate_unit':'mm',
            'volume_groups':[{'name':'Specimen','dim':3,'tags':[1],'volume_si':0.002}],
            'boundary_groups':[{'name':'Grip_Left','dim':2,'tags':[2],'area_si':0.01},
                               {'name':'Grip_Right','dim':2,'tags':[3],'area_si':0.02}]}}
        self.environment={'environment_id':'test-runtime','petsc_version':'3.25.1','dolfinx_version':'0.10.0',
            'scalar_type':'float64','probe_mpi_size':1,'execution_mpi_size':None,
            'ksp_types':['preonly','cg','gmres','fgmres'],'pc_types':['lu','gamg','hypre','jacobi','none','fieldsplit'],
            'snes_types':['newtonls','newtontr'],'line_search_types':['bt','basic','none'],
            'factor_solvers':['mumps','petsc'],'external_packages':['mumps','hypre'],
            'validation_scope':{'problem_matrix_compatibility':'not_checked','parallel_compatibility':'not_checked'}}
        self.host=SimpleNamespace(client=lambda model=None:self.client,mesh_info=lambda _:self.mesh,redact_error=str,
            solver_environment=lambda refresh=False:deepcopy(self.environment))
        self.service=ProblemSelectionService(root/'sessions',self.library,self.host)
        self.catalog=Catalog(self.library)
        self.elastic=self.spec('linear_elasticity')
        self.thermal=deepcopy(self.elastic)
        self.thermal['problem']['type']='steady_heat'
        self.thermal['problem']['unknowns']=['temperature']
        self.thermal['materials'][0]['constitutive_models']=[{'model':'fourier','fields':['temperature'],'symmetry':'isotropic'}]
        self.space_answer=None
        self.material_answer=None
        self.solver_answer=None
        self.library_answer=None
        self.client.chat.completions.create.side_effect=self.dispatch
        self.client.chat.completions.create.return_value=response(self.proposal(self.elastic))


    def space_proposal(self,spec=None,degree=1):
        names=(spec or self.elastic)['problem']['unknowns']
        return {'response':{'explanation':'Lagrange spaces are appropriate for the approved formulation.',
            'card':{'unknowns':{name:{'quantity':name,'shape':[3] if name=='displacement' else [],
                'function_space':{'family':'Lagrange','degree':degree}} for name in names},
                'state_variables':[]},'ambiguities':[]}}

    def space_question(self,target='unknowns.displacement.function_space.degree',explanation='Which degree is required?'):
        result=self.space_proposal()
        current=result['response']['card']
        parts=target.split('.')
        for key in parts[:-1]:current=current[key]
        current[parts[-1]]=None
        result['response']['ambiguities']=[{'target':target,'explanation':explanation,'options':None}]
        return result


    def tearDown(self):
        self.service.close();self.temp.cleanup()


    def spec(self,kind):
        return next(e['spec'] for e in self.catalog.entries() if e['spec']['problem']['type']==kind)


    @staticmethod
    def proposal(spec):
        result={'spec':deepcopy(spec),'ambiguities':[]}
        return {'response':result}

    def assessment_question(self,target,explanation='The request leaves this model choice ambiguous.'):
        result=self.proposal(self.elastic)
        current=result['response']['spec']
        parts=target.split('.')
        if parts[0]=='materials':
            current['materials'][0]['constitutive_models'][0][parts[-1]]=None
        else:
            for key in parts[:-1]:current=current[key]
            current[parts[-1]]=None
        item={'target':target,'explanation':explanation}
        if target not in ('problem.linearity','problem.time_dependence','problem.history_dependence','problem.coupling.type'):
            item['options']=None
        result['response']['ambiguities']=[item]
        return result


    def start(self,spec=None):
        self.client.chat.completions.create.return_value=response(self.proposal(spec or self.elastic))
        return self.service.chat({'mesh_id':self.mesh['id'],'message':"INITIAL_RAW_REQUEST: Analyze a 3D specimen."})

    def selection_request(self):
        return next(call.kwargs for call in reversed(self.client.chat.completions.create.call_args_list)
            if call.kwargs['response_format']['json_schema']['name']=='selection_reply')


    def thermal_form(self):
        return {'weak_form':[{'field':'temperature','unknown':'T','test_function':'w','type':'linear',
            'bilinear_form':r'a(T,w)=\int_\Omega k\nabla T\cdot\nabla w\,dx',
            'linear_form':r'L(w)=\int_\Omega Qw\,dx'}], 'kinematics':None,
            'constitutive':[r'\mathbf{q}=-k\nabla T'],
            'constitutive_parameters':[{'name':'conductivity','symbol':'k'}],
            'boundary_parameters':[], 'source_parameters':[{'name':'heat_source','symbol':'Q'}]}


    def thermo_spec(self):
        spec=deepcopy(self.thermal)
        spec['problem'].update(type='linear_thermoelasticity',unknowns=['temperature','displacement'],
            coupling={'type':'multiphysics_one_way','dependencies':[{'from':'temperature','to':'displacement'}]})
        spec['materials'][0]['constitutive_models'].append({'model':'linear_thermoelasticity',
            'fields':['temperature','displacement'],'symmetry':'isotropic'})
        return spec

    def thermoelastic_fixture(self, *, fully_coupled=False):
        """Construct an isolated coupling fixture from the current formulation."""
        record=json.loads((app.ROOT/'library/thermoelasticity_isotropic_formulation.json').read_text())
        aliases={name:('temperature' if name.lower() in {'t','temperature'} else 'displacement')
            for name in record['problem']['unknowns']}
        record['problem']['unknowns']=['temperature','displacement']
        directions=[{'from':'temperature','to':'displacement'}]
        if fully_coupled:directions.append({'from':'displacement','to':'temperature'})
        record['problem']['coupling']={'type':'multi_physics_fully_coupled' if fully_coupled else 'multi_physics_one_way',
            'dependencies':directions}
        for material in record['materials']:
            for model in material['constitutive_models']:
                model['fields']=[aliases.get(name,name) for name in model['fields']]
        for form in record['formulation']['weak_form']:
            form['field']=aliases.get(form['field'],form['field'])
        return record


    def start_review(self):
        state=self.start(self.thermal)
        self.client.chat.completions.create.return_value=response(self.thermal_form())
        return self.service.confirm({'session_id':state['id'],'turn_index':0})


    def start_spaces(self):
        state=self.start()
        return self.service.confirm({'session_id':state['id'],'turn_index':0})


    def start_materials(self):
        state=self.start_spaces()
        return self.service.confirm_spaces({'session_id':state['id'],'functionspace_turn_index':0})


    def material_proposal(self):
        return {'response':{'card':{'constitutive_parameters':{
            'youngs_modulus':[{'regions':['volume_1'],'value':210.0,'unit':'GPa'}],
            'poissons_ratio':[{'regions':['volume_1'],'value':0.3,'unit':''}]}},'ambiguities':[],'user_inputs':[]}}

    def material_card(self):
        from material_agent.agent import evaluate
        return evaluate(self.material_proposal()['response'],self.catalog.lookup(self.elastic)['formulation'],
            self.mesh['summary'])[0]['proposed_card']

    def material_question(self):
        result=self.material_proposal()
        parameters=result['response']['card']['constitutive_parameters']
        parameters['youngs_modulus'][0].update(value=None,unit=None)
        parameters['poissons_ratio'][0]['value']=None
        result['response']['ambiguities']=[
            {'parameter':'youngs_modulus','binding':0,'fields':['value','unit'],
                'explanation':'Specify the elastic modulus and its unit.','options':None},
            {'parameter':'poissons_ratio','binding':0,'fields':['value'],
                'explanation':'Specify the dimensionless Poisson ratio.','options':None}]
        return result

    def material_recommendation(self):
        result=self.material_question()
        result['response']['ambiguities'][0]['options']=[{
            'label':'Steel-like trial values','description':'Assumes a homogeneous isotropic steel for exploration.',
            'updates':[
                {'parameter':'youngs_modulus','binding':0,'regions':None,'value':210.0,'unit':'GPa'},
                {'parameter':'poissons_ratio','binding':0,'regions':None,'value':0.3,'unit':''}]}]
        return result

    def material_payload(self,value):
        """Encode concise internal test fixtures as the public region-set response."""
        if 'material_sets' in value['response']:
            return value
        raw=deepcopy(value['response'])
        groups={f'volume_{i}':None for i,_ in enumerate(self.mesh['summary']['volume_groups'],1)}
        inputs=[];covered=set()
        for item in raw['ambiguities']:
            if not item.get('options'):
                inputs.append(item);continue
            options=[];regions=set();names=[]
            for option in item['options']:
                values={name:None for name in raw['card']['constitutive_parameters']}
                for patch in option['updates']:
                    name=patch['parameter'];row=raw['card']['constitutive_parameters'][name][patch['binding']]
                    regions.update(patch['regions'] or row['regions'] or [])
                    if name not in names:names.append(name)
                    covered.add((name,patch['binding']))
                    values[name]={key:patch[key] if patch[key] is not None else row[key] for key in ('value','unit')}
                options.append({'label':option['label'],'description':option['description'],'values':values})
            key=sorted(regions)[0]
            if groups[key] is not None:raise ValueError('Use a single set in material API test fixtures.')
            groups[key]={'regions':sorted(regions),'explanation':item['explanation'],'options':options}
        raw['ambiguities']=[item for item in inputs if (item['parameter'],item['binding']) not in covered]
        raw['material_sets']=groups
        return {'response':raw}


    def start_source_boundaries(self):
        self.material_answer=self.material_proposal()
        state=self.start_materials()
        return self.service.confirm_materials({'session_id':state['id'],'material_turn_index':0})


    def dispatch(self,**request):
        name=request['response_format']['json_schema']['name']
        if name=='selection_library_review':
            if isinstance(self.library_answer,Exception):raise self.library_answer
            if self.library_answer is not None:return response(self.library_answer)
            context=json.loads(request['messages'][1]['content'])
            spec=context['initial_draft']
            found=next((item for item in context['library_candidates'] if canonical(item['spec'])==canonical(spec)),None)
            return response({'response':{'library_id':found['id']}} if found else self.proposal(spec))
        if name=='solver_parameters':
            if isinstance(self.solver_answer,Exception):raise self.solver_answer
            return response(self.solver_answer or self.solver_recommendation())
        if name=='boundary_parameter_selection':
            from boundary_condition_agent.parameter_selection import wire_reply
            context=json.loads(request['messages'][1]['content'])
            assessment={key:[{'name':p['name'],'requirement':'not_needed','regions':[],'reason':"Not used."}
                for p in context[key]] for key in ('boundary_parameters','source_parameters')}
            assessment['dirichlet_conditions']=[{'field':u['name'],'requirement':'not_needed','regions':[],'components':[],'reason':"Not used."} for u in context['unknowns']]
            return response(wire_reply({'explanation':"Review the required conditions.",'assessment':assessment,'recommendations':[]},context['unknowns']))
        if name=='material_parameters':
            if isinstance(self.material_answer,Exception):raise self.material_answer
            return response(self.material_payload(self.material_answer or self.material_question()))
        if name=='function_space':
            if isinstance(self.space_answer,Exception):raise self.space_answer
            thermal='"type": "steady_heat"' in request['messages'][1]['content']
            return response(self.space_answer or self.space_proposal(self.thermal if thermal else self.elastic))
        return DEFAULT

    @staticmethod
    def solver_linear():
        return {'type':'direct','ksp_type':'preonly','pc_type':'lu','factor_solver':'mumps',
            'rtol':None,'atol':None,'max_iterations':None,'options':[]}

    def solver_recommendation(self):
        return {'response':{'explanation':"Recommended based on the finalized physical specifications and installation environment.",
            'recommendations':[{'label':"Direct method",'description':"Recommendation of the direct method for the current mesh size.",
                'card':{'solver':{'linear':self.solver_linear(),'nonlinear':None}}}]}}
