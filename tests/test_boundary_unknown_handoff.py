"""Approved field shapes drive boundary contracts; models decide only constraints."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from tests import test_boundary_classification as classification
from tests.fixtures import response
from boundary_condition_agent import parameter_selection as agent, values
from problem_selection_agent.service import ProblemSelectionService


class BoundaryUnknownHandoffTests(unittest.TestCase):
    def setUp(self):
        example=classification.BoundaryClassificationTests();example.setUp()
        self.form=example.form;self.summary=example.summary
        self.unknowns=[{'name':'displacement','quantity':'displacement','shape':[3],
            'function_space':{'family':'Lagrange','degree':1}},
            {'name':'temperature','quantity':'temperature','shape':[],
                'function_space':{'family':'Lagrange','degree':1}}]
        self.form['weak_form'].append({'field':'temperature','unknown':'T','test_function':'w','type':'linear',
            'bilinear_form':r'a(T,w)=\int_\Omega k\nabla T\cdot\nabla w\,dx','linear_form':'L(w)=0'})
        self.raw={'explanation':'Constrain displacement and prescribe the left temperature.',
            'assessment':example.assessment,'recommendations':[]}
        self.raw['assessment']['dirichlet_conditions'][0]['components']=[0,1,2]
        self.raw['assessment']['dirichlet_conditions'].append({'field':'temperature','requirement':'needed',
            'regions':[example.left],'components':None,'reason':'Prescribed support temperature.'})

    def state(self):
        return {'id':'test_handoff','initial_request':'Fix the left end and maintain its temperature.',
            'formulation':deepcopy(self.form),'functionspace_card':{'unknowns':deepcopy(self.unknowns),'state_variables':[]},
            'mesh':{'id':'test_mesh','summary':deepcopy(self.summary)}}

    def test_scalar_components_are_absent_and_vector_indices_come_from_the_approved_shape(self):
        schema=agent.response_model(self.form,self.summary,self.unknowns,wire=True).model_json_schema()
        slots=schema['$defs']['DirichletFieldUses']['properties']
        self.assertEqual(set(slots),{u['name'] for u in self.unknowns})
        def properties(field):
            ref=slots[field]['items']['$ref'].split('/')[-1]
            return schema['$defs'][ref]['properties']
        self.assertNotIn('components',properties('temperature'))
        self.assertNotIn('shape',properties('temperature'))
        indices=properties('displacement')['components']['anyOf'][0]['items']['enum']
        self.assertEqual(indices,[0,1,2])

    def test_decoding_supplies_scalar_components_for_current_and_recommended_conditions(self):
        self.raw['recommendations']=[{'label':'Prescribed constraints','description':'Use the stated conditions.',
            'assessment':deepcopy(self.raw['assessment'])}]
        before=deepcopy(self.raw)
        wire=agent.wire_reply(self.raw,self.unknowns)
        self.assertNotIn('components',wire['assessment']['dirichlet_conditions']['temperature'][0])
        Reply=agent.response_model(self.form,self.summary,self.unknowns,wire=True)
        parsed=Reply.model_validate_json(json.dumps(wire)).model_dump(mode='json',by_alias=True)
        checked=agent.check_reply(agent.internal_reply(parsed,self.unknowns),self.form,self.summary,self.unknowns)
        self.assertEqual(checked['assessment']['dirichlet_conditions'][1]['components'],[])
        self.assertEqual(checked['recommendations'][0]['assessment']['dirichlet_conditions'][1]['components'],[])
        self.assertEqual(checked['determination'],'determined');self.assertIsNone(checked['question'])
        self.assertEqual(self.raw,before)

    def test_legacy_scalar_nulls_are_resolved_without_rewriting_the_reply(self):
        before=deepcopy(self.raw)
        shown=agent.present_review(self.raw,self.unknowns)
        self.assertEqual(shown['assessment']['dirichlet_conditions'][1]['components'],[])
        self.assertEqual(shown['question_targets'],[])
        self.assertEqual(self.raw,before)
        self.assertEqual(agent.check_assessment(self.raw['assessment'],self.form,self.summary,self.unknowns)['dirichlet_conditions'][1]['components'],[])

    def test_unknown_regions_and_vector_components_still_require_real_choices(self):
        self.raw['assessment']['dirichlet_conditions'][0]['components']=None
        self.raw['assessment']['dirichlet_conditions'][1]['regions']=None
        checked=agent.check_reply(self.raw,self.form,self.summary,self.unknowns)
        self.assertEqual(set(checked['question_targets']),{'dirichlet_conditions.displacement.components',
            'dirichlet_conditions.temperature.regions'})
        self.assertEqual(checked['determination'],'undetermined')

    def test_model_cannot_supply_scalar_components_or_redefine_unknowns(self):
        Reply=agent.response_model(self.form,self.summary,self.unknowns,wire=True)
        wire=agent.wire_reply(self.raw,self.unknowns)
        for mutation in ('scalar_components','scalar_shape','extra_field','unknowns'):
            invalid=deepcopy(wire)
            if mutation=='scalar_components':invalid['assessment']['dirichlet_conditions']['temperature'][0]['components']=None
            elif mutation=='scalar_shape':invalid['assessment']['dirichlet_conditions']['temperature'][0]['shape']=[3]
            elif mutation=='extra_field':invalid['assessment']['dirichlet_conditions']['stress']=[]
            else:invalid['unknowns']=[{'name':'temperature','shape':[3]}]
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(invalid))
        for indices in ([3],[-1],[0,0]):
            invalid=deepcopy(wire);invalid['assessment']['dirichlet_conditions']['displacement'][0]['components']=indices
            with self.subTest(indices=indices),self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(invalid))

    def test_tensor_index_choices_follow_its_existing_shape(self):
        unknowns=[{'name':'tensor_field','quantity':'tensor','shape':[2,2]}]
        schema=agent.response_model(self.form,self.summary,unknowns,wire=True).model_json_schema()
        ref=schema['$defs']['DirichletFieldUses']['properties']['tensor_field']['items']['$ref'].split('/')[-1]
        self.assertEqual(schema['$defs'][ref]['properties']['components']['anyOf'][0]['items']['enum'],[0,1,2,3])

    def test_message_history_and_value_shapes_reuse_the_approved_unknowns(self):
        state=self.state();state['boundary_parameter_turns']=[{'message':'Existing proposal.','response':deepcopy(self.raw)}]
        before=deepcopy(state);messages,_=agent.messages(state,self.summary)
        context=json.loads(messages[1]['content'])
        self.assertEqual(context['unknowns'],[{k:u[k] for k in ('name','quantity','shape')} for u in self.unknowns])
        replay=json.loads(messages[-1]['content'])
        self.assertNotIn('components',replay['assessment']['dirichlet_conditions']['temperature'][0])
        self.assertEqual(state,before)
        rows=values.requirements(self.raw['assessment'],self.form,self.summary,self.unknowns)
        self.assertEqual({row['field']:row['shape'] for row in rows},{'displacement':[3],'temperature':[]})
        self.assertEqual(next(row for row in rows if row['field']=='temperature')['components'],[])

    def test_service_accepts_the_handoff_in_one_call_without_scalar_clarification(self):
        state=self.state();before=deepcopy(state)
        self.raw['recommendations']=[{'label':'Requested constraints','description':'Fix the support and its temperature.',
            'assessment':deepcopy(self.raw['assessment'])}]
        client=Mock();client.chat.completions.create.return_value=response(agent.wire_reply(self.raw,self.unknowns))
        host=SimpleNamespace(mesh_info=lambda _:state['mesh'],client=lambda _:client,redact_error=str)
        with tempfile.TemporaryDirectory() as folder:
            service=ProblemSelectionService(Path(folder)/'sessions',Path(folder)/'library',host)
            try:result=service.select_boundary_parameters(state)
            finally:service.close()
        self.assertEqual(client.chat.completions.create.call_count,1)
        self.assertEqual(result['turn']['response']['determination'],'determined')
        self.assertIsNone(result['turn']['response']['question'])
        self.assertNotIn('validation_repairs',result['turn'])
        self.assertEqual(result['turn']['response']['assessment']['dirichlet_conditions'][1]['components'],[])
        self.assertEqual(state,before)

    def test_loading_old_scalar_questions_uses_the_card_without_approving_or_rewriting(self):
        state=self.state();state.update(id='c'*32,stage='boundary_parameter_review',turns=[],
            boundary_parameter_assessment=None,boundary_parameter_turns=[{'message':'Old proposal.',
                'response':deepcopy(self.raw)}])
        raw_turns=deepcopy(state['boundary_parameter_turns'])
        client=Mock();host=SimpleNamespace(mesh_info=lambda _:state['mesh'],client=lambda _:client,redact_error=str)
        with tempfile.TemporaryDirectory() as folder:
            service=ProblemSelectionService(Path(folder)/'sessions',Path(folder)/'library',host)
            try:
                service.workflow.graph.update_state(service.workflow.config(state['id']),state,as_node='boundary_parameter_selection')
                loaded=service.load(state['id'])
                current=loaded['boundary_parameter_turns'][-1]['response']
                self.assertEqual(current['assessment']['dirichlet_conditions'][1]['components'],[])
                self.assertIsNone(current['question'])
                self.assertIsNone(loaded['boundary_parameter_assessment'])
                self.assertNotIn('boundary_parameters',loaded['authoring_status']['approved_stages'])
                self.assertEqual(service.snapshot(state['id']).values['boundary_parameter_turns'],raw_turns)
                client.chat.completions.create.assert_not_called()
            finally:service.close()


if __name__=='__main__':unittest.main()
