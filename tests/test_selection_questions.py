"""Fixed choices, recorded answers and registration routing need no paid calls."""
from copy import deepcopy
import json
from unittest.mock import patch

from tests.fixtures import AuthoringFixture, response
from problem_selection_agent.library_matching import enforce_answers
from problem_selection_agent.questions import fixed_values, select_question, wire_assessment
from problem_selection_agent.service import ProblemSelectionService, SelectionError
from problem_selection_agent.spec import reply_model
from web.app import POST_ROUTES


class SelectionQuestionTests(AuthoringFixture):
    def start_question(self, target='problem.time_dependence'):
        self.client.chat.completions.create.return_value = response(self.assessment_question(target))
        return self.service.chat({'mesh_id': self.mesh['id'], 'message': "Please choose the specimen analysis model."})

    def test_fixed_questions_generate_all_schema_choices_and_cannot_supply_custom_options(self):
        Reply = reply_model([], [], 3)
        expected = {
            'problem.linearity': ('linear', 'nonlinear'),
            'problem.time_dependence': ('independent', 'dependent'),
            'problem.history_dependence': (False, True),
            'problem.coupling.type': ('single_physics', 'multi_physics_one_way', 'multi_physics_fully_coupled'),
        }
        self.assertEqual(fixed_values(), expected)
        for target, values in expected.items():
            with self.subTest(target=target):
                parsed = Reply.model_validate_json(json.dumps(self.assessment_question(target))).model_dump(mode='json')['response']
                shown = select_question(parsed)
                self.assertEqual(shown['question_type'], 'choice')
                self.assertEqual(shown['targets'], [target])
                self.assertEqual(tuple(option['value'] for option in shown['options']), values)
                custom = self.assessment_question(target)
                custom['response']['ambiguities'][0]['options'] = [{'label': "Arbitrary value", 'description': "Arbitrary candidate"}]
                with self.assertRaises(ValueError): Reply.model_validate_json(json.dumps(custom))
                direct = {'response': {'kind': 'question', 'question_type': 'input',
                    'question': "Please enter it.", 'targets': [target], 'options': []}}
                with self.assertRaises(ValueError): Reply.model_validate_json(json.dumps(direct))

    def test_free_model_candidates_remain_model_generated_and_scoped(self):
        Reply = reply_model([], [], 3)
        candidates = self.assessment_question('problem.type')
        candidates['response']['ambiguities'][0]['options'] = [
                {'label': "Linear elasticity", 'description': "Linear response for small deformation"},
                {'label': "Hyperelasticity", 'description': "Elastic response with finite deformation"}]
        parsed = Reply.model_validate_json(json.dumps(candidates)).model_dump(mode='json',by_alias=True)
        self.assertEqual(parsed, candidates)
        self.assertEqual(select_question(parsed['response'])['question_type'],'choice')
        candidates['response']['ambiguities'][0]['options'].pop()
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(candidates))

    def test_fixed_options_are_rejected_without_silently_changing_the_response(self):
        Reply=reply_model([],[],3)
        for target in fixed_values():
            for options in (None,[{'label':'untrusted','description':'An alternative outside the server enum.'}]):
                with self.subTest(target=target,options=options):
                    raw=self.assessment_question(target)
                    raw['response']['ambiguities'][0]['options']=options
                    before=deepcopy(raw)
                    prepared=enforce_answers(raw,{})
                    with self.assertRaises(ValueError) as caught:
                        Reply.model_validate_json(json.dumps(prepared))
                    errors=caught.exception.errors()
                    self.assertEqual(len(errors),1)
                    self.assertEqual(errors[0]['type'],'fixed_options_forbidden')
                    self.assertEqual(errors[0]['ctx']['target'],target)
                    self.assertEqual(raw,before)
                    self.assertEqual(prepared,raw)
        raw=self.assessment_question('problem.type')
        raw['response']['ambiguities'][0]['options']=[{'label':'linear_elasticity','description':'Small strain.'},
            {'label':'hyperelasticity','description':'Finite strain.'}]
        self.assertEqual(enforce_answers(raw,{}),raw)
        raw['response']['ambiguities'][0]['unexpected']='still invalid'
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(enforce_answers(raw,{})))

    def test_unresolved_fixed_choices_require_repair_before_server_options_are_shown(self):
        raw=self.assessment_question('problem.time_dependence')
        raw['response']['ambiguities'][0]['options']=[{'label':'anything','description':'Do not display this.'}]
        self.client.chat.completions.create.side_effect=[response(raw),
            response(self.assessment_question('problem.time_dependence'))]
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Clarify whether physical time is relevant.'})
        turn=state['turns'][0]
        self.assertEqual(turn['response']['fixed_target'],'problem.time_dependence')
        self.assertEqual([o['value'] for o in turn['response']['options']],['independent','dependent'])
        self.assertEqual(self.client.chat.completions.create.call_count,2)
        self.assertEqual(turn['validation_repairs'],1)
        self.assertIn('Only free-choice targets may include options',turn['validation_errors'][0])
        self.assertIsNone(state['confirmed_selection'])

    def test_filled_fixed_fields_still_reject_options_before_proposal_review(self):
        raw=self.proposal(self.elastic)
        raw['response']['ambiguities']=[{'target':'problem.coupling.type','explanation':'Already classified.',
            'options':[{'label':'made_up','description':'Do not use model alternatives.'}]},
            {'target':'problem.time_dependence','explanation':'Already classified.','options':None}]
        self.client.chat.completions.create.side_effect=[response(raw),response(self.proposal(self.elastic)),
            response({'response':{'library_id':'linear_elasticity_isotropic_formulation.json'}})]
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Use this steady linear elastic model.'})
        self.assertEqual(state['turns'][0]['response']['kind'],'proposal')
        self.assertEqual(state['turns'][0]['response']['spec'],self.elastic)
        self.assertEqual(self.client.chat.completions.create.call_count,3)
        self.assertEqual(state['turns'][0]['validation_repairs'],1)
        self.assertIsNone(state['confirmed_selection'])

    def test_library_review_also_requires_repair_of_fixed_options(self):
        raw=self.assessment_question('problem.time_dependence')
        raw['response']['ambiguities'][0]['options']=None
        self.client.chat.completions.create.side_effect=[response(self.proposal(self.elastic)),response(raw),
            response(self.assessment_question('problem.time_dependence'))]
        state=self.start()
        self.assertEqual(state['turns'][0]['response']['fixed_target'],'problem.time_dependence')
        self.assertEqual(self.client.chat.completions.create.call_count,3)
        self.assertEqual(state['turns'][0]['library_review']['validation_repairs'],1)

    def test_generated_schema_allows_options_only_for_free_targets(self):
        schema=reply_model([],[],3).model_json_schema()
        definitions=schema['$defs']
        fixed=definitions['FixedSelectionAmbiguity']
        free=definitions['SelectionAmbiguity']
        self.assertEqual(set(fixed['properties']),{'target','explanation'})
        self.assertEqual(set(free['properties']),{'target','explanation','options'})
        self.assertFalse(fixed['additionalProperties']);self.assertFalse(free['additionalProperties'])
        fixed_targets=set(definitions['FixedSelectionTarget']['enum'])
        free_targets=set(definitions['SelectionQuestionTarget']['enum'])
        self.assertEqual(fixed_targets,set(fixed_values()))
        self.assertFalse(fixed_targets & free_targets)

    def test_repeated_fixed_options_cannot_advance_or_approve_the_workflow(self):
        raw=self.assessment_question('problem.time_dependence')
        raw['response']['ambiguities'][0]['options']=None
        self.client.chat.completions.create.return_value=response(raw)
        with self.assertRaisesRegex(SelectionError,'Only free-choice targets may include options') as caught:
            self.service.chat({'mesh_id':self.mesh['id'],'message':'Clarify physical time dependence.'})
        state=self.service.load(caught.exception.session_id)
        self.assertEqual(self.client.chat.completions.create.call_count,2)
        self.assertTrue(state['can_continue'])
        self.assertEqual(state['turns'],[])
        self.assertIsNone(state['confirmed_selection'])

    def test_choice_records_canonical_value_and_does_not_approve_spec(self):
        state = self.start_question()
        with self.assertRaises(SelectionError): self.service.confirm({'session_id': state['id'], 'turn_index': 0})
        self.client.chat.completions.create.return_value = response(self.proposal(self.elastic))
        state = self.service.choose_selection({'session_id': state['id'], 'turn_index': 0, 'choice_index': 0,
            'value': 'dependent'})  # Untrusted client values are not used.
        self.assertEqual(state['selection_answers'], {'problem.time_dependence': 'independent'})
        self.assertIsNone(state['confirmed_selection'])
        self.assertEqual(state['stage'], 'selection_review')
        self.assertEqual(state['authoring_status']['status'], 'ready_for_review')
        request = self.selection_request()
        Reply = reply_model([], [], 3, state['selection_answers'])
        wrong = self.proposal(self.elastic); wrong['response']['spec']['problem']['time_dependence'] = 'dependent'
        with self.assertRaises(ValueError): Reply.model_validate_json(json.dumps(wrong))
        replay = json.loads(request['messages'][2]['content'])['response']
        self.assertEqual(replay, wire_assessment(self.assessment_question('problem.time_dependence')['response']))
        self.assertEqual(json.loads(request['messages'][-1]['content'].split('\n', 1)[1]), state['selection_answers'])
        self.assertEqual(POST_ROUTES['/api/selection/choose'], 'choose_selection')
        folder = self.service.folder; self.service.close()
        self.service = ProblemSelectionService(folder, self.library, self.host)
        self.assertEqual(self.service.load(state['id'])['selection_answers'], state['selection_answers'])

    def test_invalid_stale_or_nonfixed_choice_never_calls_model(self):
        state = self.start_question()
        calls = self.client.chat.completions.create.call_count
        for changes in ({'turn_index': -1}, {'choice_index': -1}, {'choice_index': 2}, {'choice_index': True}):
            with self.assertRaises(SelectionError):
                self.service.choose_selection({'session_id': state['id'], 'turn_index': 0, 'choice_index': 0, **changes})
        self.assertEqual(self.client.chat.completions.create.call_count, calls)
        self.client.chat.completions.create.return_value = response(self.proposal(self.elastic))
        state = self.service.choose_selection({'session_id': state['id'], 'turn_index': 0, 'choice_index': 0})
        calls = self.client.chat.completions.create.call_count
        for index in (0, 1):
            with self.assertRaises(SelectionError):
                self.service.choose_selection({'session_id': state['id'], 'turn_index': index, 'choice_index': 0})
        self.assertEqual(self.client.chat.completions.create.call_count, calls)

    def test_user_can_revise_a_previous_fixed_choice(self):
        state = self.start_question()
        self.client.chat.completions.create.return_value = response(self.proposal(self.elastic))
        state = self.service.choose_selection({'session_id': state['id'], 'turn_index': 0, 'choice_index': 0})
        self.client.chat.completions.create.return_value = response(self.assessment_question('problem.time_dependence'))
        state = self.service.chat({'session_id': state['id'], 'message': "I want to change to time-dependent."})
        revised = deepcopy(self.elastic); revised['problem']['time_dependence'] = 'dependent'
        self.client.chat.completions.create.return_value = response(self.proposal(revised))
        state = self.service.choose_selection({'session_id': state['id'], 'turn_index': 2, 'choice_index': 1})
        self.assertEqual(state['selection_answers'], {'problem.time_dependence': 'dependent'})
        self.assertEqual(state['turns'][-1]['response']['spec'], revised)
        self.assertIsNone(state['confirmed_selection'])

    def test_library_matching_and_registration_branch_are_server_owned(self):
        existing = self.start()
        self.assertEqual(existing['turns'][-1]['response']['kind'], 'proposal')
        missing = self.start(self.thermal)
        reply = missing['turns'][-1]['response']
        self.assertEqual(reply['kind'], 'registration_request')
        self.assertEqual(reply['spec'], self.thermal)
        request = self.client.chat.completions.create.call_args.kwargs
        self.assertNotIn('registration_request', json.dumps(request['response_format']))
        self.assertEqual(set(self.library.glob('*.json')), {self.library/'linear_elasticity_isotropic_formulation.json'})

    def test_confirmed_answer_is_enforced_without_an_extra_model_repair(self):
        state = self.start_question()
        invalid = self.proposal(self.elastic); invalid['response']['spec']['problem']['time_dependence'] = 'dependent'
        with patch.object(self.client.chat.completions, 'create', side_effect=[response(invalid), response(self.proposal(self.elastic))]) as call:
            state = self.service.choose_selection({'session_id': state['id'], 'turn_index': 0, 'choice_index': 0})
        self.assertEqual(call.call_count, 2)
        self.assertEqual(state['turns'][-1].get('validation_repairs',0), 0)
        self.assertEqual(state['turns'][-1]['response']['spec']['problem']['time_dependence'], 'independent')

    def test_old_session_without_answer_state_still_accepts_chat_and_confirm(self):
        state = self.start()
        self.assertEqual(state['selection_answers'], {})
        old = dict(self.service.snapshot(state['id']).values)
        old.pop('selection_answers')
        result = self.service.classify(old)
        self.assertEqual(result['response']['kind'], 'proposal')

    def test_known_values_cannot_generate_reconfirmation_questions(self):
        payload=self.proposal(self.elastic)
        payload['response']['ambiguities']=[
            {'target':'problem.linearity','explanation':'This is linear. Please confirm.'},
            {'target':'problem.coupling.type','explanation':'This is single physics. Please confirm.'}]
        self.client.chat.completions.create.return_value=response(payload)
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'A steady, linear single-physics problem.'})
        self.assertEqual(state['turns'][0]['response']['kind'],'proposal')
        self.assertEqual(state['selection_draft'],self.elastic)
        self.assertEqual(state['selection_draft']['problem']['history_dependence'],False)
        self.assertIsNone(state['confirmed_selection'])
        self.assertEqual(self.client.chat.completions.create.call_count,2)
        self.assertNotIn('question_type',state['turns'][0]['response'])

    def test_only_an_actual_unresolved_field_is_asked_and_other_judgments_survive(self):
        payload=self.assessment_question('materials.constitutive_models.symmetry')
        payload['response']['ambiguities'].insert(0,
            {'target':'problem.linearity','explanation':'This is linear. Please confirm.'})
        self.client.chat.completions.create.return_value=response(payload)
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Resolve the physical model.'})
        shown=state['turns'][0]['response']
        self.assertEqual(shown['targets'],['materials.constitutive_models.symmetry'])
        self.assertEqual(state['selection_draft']['problem']['linearity'],'linear')
        self.assertEqual(state['selection_draft']['problem']['coupling']['type'],'single_physics')
        self.client.chat.completions.create.return_value=response(self.proposal(self.elastic))
        state=self.service.chat({'session_id':state['id'],'message':'Use isotropic symmetry.'})
        request=self.selection_request()
        self.assertEqual(json.loads(request['messages'][2]['content'])['response'],wire_assessment(payload['response']))
        self.assertEqual(state['turns'][-1]['response']['kind'],'proposal')

    def test_unexplained_missing_values_get_repair_instead_of_arbitrary_questions(self):
        invalid=self.assessment_question('problem.type');invalid['response']['ambiguities']=[]
        with patch.object(self.client.chat.completions,'create',side_effect=[response(invalid),response(self.proposal(self.elastic)),response({'response':{'library_id':'linear_elasticity_isotropic_formulation.json'}})]) as call:
            state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Select the model.'})
        self.assertEqual(call.call_count,3)
        self.assertEqual(state['turns'][-1]['response']['kind'],'proposal')

    def test_single_physics_dependencies_are_filled_structurally(self):
        payload=self.proposal(self.elastic)
        payload['response']['spec']['problem']['coupling']['dependencies']=None
        self.client.chat.completions.create.return_value=response(payload)
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Select the model.'})
        self.assertEqual(state['turns'][-1]['response']['spec'],self.elastic)

    def test_legacy_question_checkpoint_can_continue_with_field_judgments(self):
        state=self.start_question()
        old_turn=deepcopy(state['turns'][0]);old_turn.pop('assessment')
        self.service.workflow.graph.update_state(self.service.workflow.config(state['id']),
            {'turns':[old_turn]},as_node='selection')
        # update_state schedules the review node; enter its interrupt before sending a reply.
        self.service._run(state['id'],None)
        calls=self.client.chat.completions.create.call_count
        loaded=self.service.load(state['id'])
        self.assertEqual(loaded['turns'],[old_turn])
        self.assertEqual(self.client.chat.completions.create.call_count,calls)
        self.client.chat.completions.create.return_value=response(self.proposal(self.elastic))
        continued=self.service.chat({'session_id':state['id'],'message':'Use a steady model.'})
        request=self.selection_request()
        replay=json.loads(request['messages'][2]['content'])['response']
        self.assertNotIn('kind',replay)
        self.assertIsNotNone(replay['ambiguities']['problem.time_dependence'])
        self.assertEqual(continued['turns'][-1]['response']['kind'],'proposal')
