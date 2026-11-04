"""Space inference, ambiguity gating, unchanged cards, and durable review without API calls."""
from copy import deepcopy
import json
from pathlib import Path
import re
from unittest.mock import patch

from tests.fixtures import AuthoringFixture, response
from functionspace_agent import agent
from functionspace_agent.judgments import unresolved_targets
from problem_selection_agent.service import SelectionError


class FunctionSpaceJudgmentTests(AuthoringFixture):
    def test_filled_fields_cannot_generate_reconfirmation(self):
        payload=self.space_proposal()
        payload['response']['ambiguities']=[{'target':'unknowns.displacement.function_space.degree',
            'explanation':'Degree one is suitable. Please confirm.','options':None}]
        self.space_answer=payload
        state=self.start_spaces()
        turn=state['functionspace_turns'][-1]
        self.assertIn('proposed_card',turn['response'])
        self.assertNotIn('question',turn['response'])
        self.assertEqual(state['functionspace_draft'],turn['response']['proposed_card'])
        self.assertIsNone(state['functionspace_card'])
        self.assertEqual(state['authoring_status']['status'],'ready_for_review')

    def test_scalar_shape_degree_zero_and_empty_states_are_complete(self):
        assessment=self.space_proposal(self.thermal,degree=0)['response']
        assessment['card']['unknowns']['temperature']['function_space']['family']='DG'
        assessment['ambiguities']=[{'target':'state_variables','explanation':'Confirm no internal states.','options':None}]
        Reply=agent.response_model(self.thermal)
        parsed=Reply.model_validate_json(json.dumps({'response':assessment})).model_dump(mode='json',by_alias=True)['response']
        card=agent.assemble_draft(parsed,self.thermal)
        self.assertEqual(unresolved_targets(card),[])
        self.assertIsNone(agent.select_question(parsed,card))
        self.assertEqual(agent.check_card(card,self.thermal)['unknowns'][0]['shape'],[])
        self.assertEqual(card['unknowns'][0]['function_space']['degree'],0)

    def test_actual_unresolved_field_is_asked_while_known_fields_are_retained(self):
        self.space_answer=self.space_question()
        self.space_answer['response']['ambiguities'].insert(0,{
            'target':'unknowns.displacement.shape','explanation':'Confirm the vector shape.','options':None})
        state=self.start_spaces()
        reply=state['functionspace_turns'][-1]['response']
        self.assertEqual(reply['targets'],['unknowns.displacement.function_space.degree'])
        self.assertEqual(reply['draft_card']['unknowns'][0]['shape'],[3])
        self.assertEqual(reply['draft_card']['unknowns'][0]['function_space']['family'],'Lagrange')
        self.assertIsNone(reply['draft_card']['unknowns'][0]['function_space']['degree'])
        with self.assertRaises(SelectionError):self.service.confirm_spaces({'session_id':state['id'],'functionspace_turn_index':0})
        previous=deepcopy(state['functionspace_draft'])
        self.space_answer=self.space_proposal(degree=2)
        done=self.service.chat({'session_id':state['id'],'functionspace_turn_index':0,'message':'Use degree two.'})
        request=self.client.chat.completions.create.call_args.kwargs
        self.assertEqual(json.loads(request['messages'][2]['content'])['response'],state['functionspace_turns'][0]['assessment'])
        self.assertEqual(previous['unknowns'][0]['function_space']['degree'],None)
        self.assertEqual(done['functionspace_draft']['unknowns'][0]['function_space']['degree'],2)

    def test_names_and_coupling_are_server_owned(self):
        selection=self.thermo_spec()
        payload=self.space_proposal(selection)
        Reply=agent.response_model(selection)
        schema=Reply.model_json_schema()
        self.assertNotIn('coupling_type',json.dumps(schema))
        parsed=Reply.model_validate_json(json.dumps(payload)).model_dump(mode='json',by_alias=True)['response']
        card=agent.check_card(agent.assemble_draft(parsed,selection),selection)
        self.assertEqual([u['name'] for u in card['unknowns']],selection['problem']['unknowns'])
        self.assertEqual(card['coupling_type'],'multi_physics_one_way')
        invalid=deepcopy(payload)
        invalid['response']['card']['unknowns']['stress']=invalid['response']['card']['unknowns'].pop('displacement')
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(invalid))

    def test_partial_internal_states_use_named_targets_and_keep_empty_units(self):
        payload=self.space_proposal()
        payload['response']['card']['state_variables']=[
            {'name':'history_strain','symbol':'e_h','shape':[3,3],'unit':'',
                'function_space':{'family':'DG','degree':0}},
            {'name':'history_stress','symbol':'s_h','shape':[3,3],'unit':'MPa',
                'function_space':{'family':'DG','degree':None}}]
        payload['response']['ambiguities']=[
            {'target':'state_variables.history_strain.function_space.degree','explanation':'Confirm zero.','options':None},
            {'target':'state_variables.history_stress.function_space.degree','explanation':'Storage order is unresolved.','options':None}]
        self.space_answer=payload
        state=self.start_spaces()
        self.assertEqual(state['functionspace_turns'][-1]['response']['targets'],
            ['state_variables.history_stress.function_space.degree'])
        self.assertEqual(state['functionspace_draft']['state_variables'][0]['unit'],'')
        payload['response']['card']['state_variables'][1]['function_space']['degree']=0
        self.space_answer=payload
        state=self.service.chat({'session_id':state['id'],'functionspace_turn_index':0,'message':'Use DG zero.'})
        self.assertEqual(len(state['functionspace_turns'][-1]['response']['proposed_card']['state_variables']),2)

    def test_null_state_list_is_unresolved_and_empty_list_is_resolved(self):
        payload=self.space_question('state_variables','The internal-state definition needs clarification.')
        self.space_answer=payload
        state=self.start_spaces()
        self.assertEqual(state['functionspace_turns'][-1]['response']['targets'],['state_variables'])
        self.assertIsNone(state['functionspace_draft']['state_variables'])
        payload['response']['card']['state_variables']=[]
        self.space_answer=payload
        state=self.service.chat({'session_id':state['id'],'functionspace_turn_index':0,'message':'No internal states are needed.'})
        self.assertIn('proposed_card',state['functionspace_turns'][-1]['response'])

    def test_formulation_issue_blocks_approval_and_keeps_approved_physics(self):
        payload=self.space_proposal()
        payload['response']['ambiguities']=[{'target':'formulation',
            'explanation':'The constitutive formulation must specify its internal-state definition.','options':None}]
        self.space_answer=payload
        state=self.start_spaces()
        self.assertTrue(state['functionspace_turns'][-1]['response']['requires_formulation_review'])
        self.assertEqual(state['confirmed_selection'],self.elastic)
        self.assertEqual(state['formulation'],self.catalog.lookup(self.elastic)['formulation'])
        with self.assertRaises(SelectionError):self.service.confirm_spaces({'session_id':state['id'],'functionspace_turn_index':0})

    def test_missing_judgment_without_ambiguity_is_repaired(self):
        state=self.start_spaces()
        invalid=self.space_question();invalid['response']['ambiguities']=[]
        with patch.object(self.client.chat.completions,'create',side_effect=[response(invalid),response(self.space_proposal())]) as call:
            state=self.service.chat({'session_id':state['id'],'functionspace_turn_index':0,'message':'Review these spaces.'})
        self.assertEqual(call.call_count,2)
        self.assertEqual(state['functionspace_turns'][-1]['validation_repairs'],1)
        self.assertIsNone(state['functionspace_card'])

    def test_source_and_provider_schema_are_english(self):
        folder=Path(agent.__file__).parent
        for path in [*folder.glob('*.py'),*folder.glob('*.txt')]:
            self.assertIsNone(re.search("[\\uac00-\\ud7a3]",path.read_text()),path.name)
        self.assertIsNone(re.search("[\\uac00-\\ud7a3]",json.dumps(agent.response_model(self.elastic).model_json_schema(),ensure_ascii=False)))

    def test_context_omits_parameter_catalogs_without_changing_formulation(self):
        form=self.catalog.lookup(self.elastic)['formulation'];before=deepcopy(form)
        messages,_=agent.messages('Use quadratic elements.',self.elastic,form,[])
        content=messages[1]['content']
        self.assertIn('Use quadratic elements.',content)
        self.assertNotIn('boundary_parameters',content)
        self.assertNotIn('source_parameters',content)
        for key in ('weak_form','kinematics','constitutive','constitutive_parameters'):
            self.assertIn('"'+key+'"',content)
        self.assertEqual(form,before)

    def test_invalid_shapes_degrees_state_names_and_options_are_rejected(self):
        Reply=agent.response_model(self.elastic)
        for field,value in (('shape',[0]),('shape',[-1])):
            payload=self.space_proposal();payload['response']['card']['unknowns']['displacement'][field]=value
            with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(payload))
        for degree in (-1,True,1.5):
            payload=self.space_proposal(degree=degree)
            with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(payload))
        payload=self.space_proposal()
        payload['response']['card']['state_variables']=[{'name':'displacement','symbol':'u','shape':[3],
            'unit':'mm','function_space':{'family':'DG','degree':0}}]
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(payload))
        payload=self.space_question()
        payload['response']['ambiguities'][0]['options']=[{'label':'Confirm','description':'The only option.'}]
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(payload))

    def test_nonexistent_state_target_is_rejected(self):
        payload=self.space_proposal()['response']
        payload['ambiguities']=[{'target':'state_variables.missing.shape','explanation':'Missing state.','options':None}]
        with self.assertRaises(ValueError):agent.select_question(payload,agent.assemble_draft(payload,self.elastic))

    def test_legacy_question_and_proposal_history_can_be_replayed(self):
        legacy_question={'message':'','response':{'question_type':'input','question':'Which degree?',
            'targets':['unknowns.displacement.function_space.degree'],'options':[]}}
        legacy_card=agent.assemble_draft(self.space_proposal()['response'],self.elastic)
        legacy_proposal={'message':'Use linear elements.','response':{'explanation':'A suitable space.','proposed_card':legacy_card}}
        messages,_=agent.messages('Initial request.',self.elastic,self.catalog.lookup(self.elastic)['formulation'],
            [legacy_question,legacy_proposal],'Reconsider the degree.')
        for index in (2,4):
            old=json.loads(messages[index]['content'])['response']
            self.assertIn('card',old);self.assertIn('ambiguities',old)
            self.assertNotIn('question_type',old);self.assertNotIn('proposed_card',old)

    def test_approved_unknown_names_can_match_pydantic_attributes(self):
        selection=deepcopy(self.elastic);selection['problem']['unknowns']=['model_fields']
        payload=self.space_proposal(selection)
        parsed=agent.response_model(selection).model_validate_json(json.dumps(payload)).model_dump(mode='json',by_alias=True)['response']
        self.assertEqual(agent.assemble_draft(parsed,selection)['unknowns'][0]['name'],'model_fields')
