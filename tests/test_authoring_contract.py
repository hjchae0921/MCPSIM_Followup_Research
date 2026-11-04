"""Stage scopes and approval/readiness are validated without model API calls."""
from copy import deepcopy
import json
from unittest.mock import patch

from tests.fixtures import AuthoringFixture, response
from common.authoring import progress
from problem_selection_agent.spec import reply_model
from problem_selection_agent.service import SelectionError
from functionspace_agent import agent as spaces
from material_agent import agent as materials
from boundary_condition_agent import values, parameter_selection
from solver_agent import agent as solvers


class AuthoringContractTests(AuthoringFixture):
    def schemas(self):
        choices=self.catalog.choices()
        form=self.catalog.lookup(self.elastic)['formulation']
        unknowns=spaces.assemble_draft(self.space_proposal()['response'],self.elastic)['unknowns']
        rows=[{'id':'condition_1','name':'traction','shape':[3]}]
        return [
            (reply_model(choices['types'],choices['models'],3),'problem.type',True),
            (spaces.response_model(self.elastic),'unknowns.displacement.function_space.degree',True),
            (materials.response_model(form,self.mesh['summary']),'constitutive_parameters.youngs_modulus.value',True),
            (values.response_model(rows),'draft.condition_1.value',False),
            (solvers.response_model(self.elastic,self.environment),'solver.linear.pc_type',True),
            (parameter_selection.response_model(form,self.mesh['summary'],unknowns),None,None)]

    def test_each_stage_rejects_targets_from_other_cards_and_strict_schema_has_no_ref_siblings(self):
        for Reply,target,wrapped in self.schemas():
            schema=Reply.model_json_schema()
            def strict(node):
                if isinstance(node,dict):
                    if '$ref' in node:self.assertEqual(set(node),{'$ref'})
                    if node.get('type')=='object':
                        self.assertFalse(node['additionalProperties'])
                        self.assertEqual(set(node['required']),set(node['properties']))
                    for item in node.values():strict(item)
                elif isinstance(node,list):
                    for item in node:strict(item)
            strict(schema)
            if target is None:continue
            question={'question_type':'input','question':"Please check the current item.",'options':[],'targets':[target]}
            payload={'response':question} if wrapped else {'explanation':"Check value",'draft':[{'id':'condition_1','value':None,'unit':None}],'question':question}
            if target=='problem.type':
                payload=self.assessment_question(target)
                question=payload['response']['ambiguities'][0]
            elif target.startswith('unknowns.'):
                payload=self.space_question(target)
                question=payload['response']['ambiguities'][0]
            elif target.startswith('constitutive_parameters.'):
                payload=self.material_payload(self.material_question())
                question=payload['response']['ambiguities'][0]
            with self.subTest(target=target):
                Reply.model_validate_json(json.dumps(payload))
                key='parameter' if target.startswith('constitutive_parameters.') else 'target' if target=='problem.type' or target.startswith('unknowns.') else 'targets'
                question[key]='outside_stage.some_parameter.value' if key in ('target','parameter') else ['outside_stage.some_parameter.value']
                with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(payload))
                del question[key]
                with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(payload))

    def test_selection_and_functionspace_cannot_emit_numerical_recommendations(self):
        for Reply,target,_ in self.schemas()[:2]:
            q={'question_type':'recommendation','question':"I recommend a heat flux value.",'targets':[target],
                'options':[{'label':"Recommendation",'description':"Assumed conditions",'values':[{'name':'heat_flux','value':1.0,'unit':'W/mm²'}]}]}
            if target.startswith('problem.'):q['kind']='question'
            with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps({'response':q}))

    def test_recommendation_values_are_limited_to_approved_parameters_and_condition_ids(self):
        schemas=self.schemas()
        for index,target,name in ((2,'constitutive_parameters.youngs_modulus.value','youngs_modulus'),(3,'draft.condition_1.value','condition_1')):
            Reply,_,wrapped=schemas[index]
            question={'question_type':'recommendation','question':"Please review the recommended values.",'targets':[target],
                'options':[{'label':"Recommendation",'description':"Applied assumptions",'values':[{'name':name,'value':1.0,'unit':''}]}]}
            payload={'response':question} if wrapped else {'explanation':"Recommended value",'draft':[{'id':'condition_1','value':None,'unit':None}],'question':question}
            if index==2:
                payload=self.material_payload(self.material_recommendation())
            Reply.model_validate_json(json.dumps(payload))
            if index==2:payload['response']['material_sets']['volume_1']['options'][0]['values']['unapproved_parameter']={'value':1,'unit':''}
            else:question['options'][0]['values'][0]['name']='unapproved_parameter'
            with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(payload))

    def test_completion_words_are_not_a_proposal_or_approval_and_status_is_checkpointed(self):
        q=self.assessment_question('problem.linearity',explanation='The specification is complete.')
        self.client.chat.completions.create.return_value=response(q)
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':"I will pull the specimen."})
        self.assertEqual(state['authoring_status']['status'],'needs_input')
        self.assertIsNone(state['confirmed_selection'])
        self.assertEqual(state['authoring_status'],self.service.snapshot(state['id']).values['authoring_status'])
        with self.assertRaises(SelectionError):self.service.confirm({'session_id':state['id'],'turn_index':0})
        self.client.chat.completions.create.return_value=response(self.proposal(self.elastic))
        state=self.service.chat({'session_id':state['id'],'turn_index':0,'message':"I will use a linear model."})
        self.assertEqual(state['authoring_status']['status'],'ready_for_review')
        self.assertNotIn('selection',state['authoring_status']['approved_stages'])
        state=self.service.confirm({'session_id':state['id'],'turn_index':1})
        self.assertEqual(state['authoring_status']['stage'],'function_space')
        self.assertEqual(state['authoring_status']['status'],'ready_for_review')
        self.assertIn('selection',state['authoring_status']['approved_stages'])
        self.assertIn('formulation',state['authoring_status']['approved_stages'])
        self.assertNotIn('function_space',state['authoring_status']['approved_stages'])
        self.assertEqual(state['authoring_status'],self.service.snapshot(state['id']).values['authoring_status'])

    def test_invalid_scope_gets_one_repair_without_changing_approved_inputs(self):
        state=self.start_spaces();before={k:deepcopy(state[k]) for k in ('confirmed_selection','formulation')}
        invalid={'response':{'question_type':'input','question':"Please tell me the heat flux.",'options':[],
            'targets':['boundary_parameters.heat_flux.value']}}
        valid=self.space_proposal(degree=2)
        with patch.object(self.client.chat.completions,'create',side_effect=[response(invalid),response(valid)]) as call:
            state=self.service.chat({'session_id':state['id'],'functionspace_turn_index':0,'message':"Please suggest a function space."})
            self.assertEqual(call.call_count,2)
            self.assertIn('the same output schema',call.call_args.kwargs['messages'][-1]['content'])
        self.assertEqual(state['authoring_status']['status'],'ready_for_review')
        self.assertEqual(state['functionspace_turns'][-1]['validation_repairs'],1)
        self.assertIsNone(state['functionspace_card'])
        for key,value in before.items():self.assertEqual(state[key],value)
        with patch.object(self.client.chat.completions,'create',return_value=response(invalid)) as call:
            with self.assertRaises(SelectionError):self.service.chat({'session_id':state['id'],'functionspace_turn_index':1,'message':"Please check again."})
            self.assertEqual(call.call_count,2)
        failed=self.service.load(state['id'])
        self.assertTrue(failed['can_continue']);self.assertIsNone(failed['functionspace_card'])
        for key,value in before.items():self.assertEqual(failed[key],value)

    def test_status_covers_values_candidates_and_explicit_solver_approval(self):
        state=self.start_source_boundaries()
        state=self.service.confirm_boundary_parameter_selection({'session_id':state['id'],'boundary_parameter_turn_index':0})
        self.assertEqual(state['authoring_status']['status'],'ready_for_review') # no values are required
        self.assertNotIn('boundary_values',state['authoring_status']['approved_stages'])
        state=self.service.confirm_boundary_values({'session_id':state['id'],'boundary_value_turn_index':0})
        self.assertEqual(state['authoring_status']['status'],'ready_for_review')
        self.assertNotIn('solver',state['authoring_status']['approved_stages'])
        state=self.service.choose_solver({'session_id':state['id'],'solver_turn_index':0,'recommendation_index':0})
        self.assertIsNone(state['solver_card'])
        state=self.service.confirm_solver({'session_id':state['id'],'solver_turn_index':1})
        self.assertEqual(state['authoring_status']['status'],'approved')
        self.assertEqual(state['authoring_status']['stage'],'solver')
        self.assertIn('solver',state['authoring_status']['approved_stages'])
        self.assertNotIn('authoring_status',state['solver_card'])
        partial={'stage':'boundary_value_review','boundary_value_requirements':[{'id':'condition_1'}],
            'boundary_value_draft':[{'id':'condition_1','value':0,'unit':None}]}
        self.assertEqual(progress(partial)['status'],'needs_input')
        partial['boundary_value_draft'][0]['unit']=''
        self.assertEqual(progress(partial)['status'],'ready_for_review')

    def test_loading_legacy_reply_derives_status_without_rewriting_it_or_model_calls(self):
        state=self.start();sid=state['id']
        old=deepcopy(state['turns']);old[-1]['response']={'kind':'question','question_type':'input','options':[],
            'question':"Completed."} # no targets in older data
        self.service.workflow.graph.update_state(self.service.workflow.config(sid),{'turns':old,'authoring_status':{}},as_node='selection')
        count=self.client.chat.completions.create.call_count
        loaded=self.service.load(sid)
        self.assertEqual(loaded['authoring_status']['status'],'needs_input')
        self.assertEqual(loaded['turns'],old)
        self.assertEqual(self.service.snapshot(sid).values['turns'],old)
        self.assertEqual(self.client.chat.completions.create.call_count,count)

    def test_boundary_assessment_completion_and_questions_belong_to_the_server(self):
        state=self.start_source_boundaries()
        reply=parameter_selection.provider_reply(state['boundary_parameter_turns'][-1]['response'])
        reply['assessment']['boundary_parameters'][0].update(requirement='needed',regions=None)
        form=state['formulation'];unknowns=state['functionspace_card']['unknowns'];summary=self.mesh['summary']
        checked=parameter_selection.check_reply(reply,form,summary,unknowns)
        self.assertEqual(checked['question_targets'],['boundary_parameters.traction.regions'])
        self.assertEqual(checked['determination'],'undetermined')
        self.assertNotIn('question',parameter_selection.provider_reply(checked))
        self.assertNotIn('determination',parameter_selection.provider_reply(checked))
        Reply=parameter_selection.response_model(form,summary,unknowns)
        for extra in ('question','question_targets','determination','unresolved_fields'):
            invalid={**reply,extra:checked[extra]}
            with self.subTest(extra=extra),self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(invalid))
