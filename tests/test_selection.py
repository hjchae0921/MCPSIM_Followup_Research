"""Selection, formulation, function-space and material regression tests."""
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
from problem_selection_agent.explanation import describe_selection
from functionspace_agent import agent as space_agent
from material_agent import agent as material_agent
from common.dialogue import InputQuestion, ChoiceQuestion, RecommendationQuestion

from tests.fixtures import AuthoringFixture, response

class SelectionTests(AuthoringFixture):
    def test_catalog_matches_semantically_without_mutating_old_identifiers(self):
        legacy=self.thermo_spec()
        spec=normalized(legacy)
        self.assertEqual(legacy['problem']['coupling']['type'],'multiphysics_one_way')
        self.assertEqual(spec['problem']['coupling']['type'],'multi_physics_one_way')
        swapped=deepcopy(spec);swapped['problem']['unknowns'].reverse()
        swapped['materials'][0]['constitutive_models'].reverse()
        for model in swapped['materials'][0]['constitutive_models']:model['fields'].reverse()
        self.assertEqual(canonical(spec),canonical(swapped))
        self.assertEqual(self.catalog.lookup(self.elastic)['status'],'ready')


    def test_free_model_names_fixed_enums_and_mesh_dimension_are_enforced(self):
        choices=self.catalog.choices();Reply=reply_model(choices['types'],choices['models'],3)
        Reply.model_validate_json(json.dumps(self.proposal(self.elastic)))
        missing_spec=self.proposal(self.elastic)
        del missing_spec['response']['spec']
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(missing_spec))
        for key,value in [('type','required'),('dimension',2),('linearity','required')]:
            spec=deepcopy(self.elastic);spec['problem'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(self.proposal(spec)))
        spec=deepcopy(self.elastic);spec['materials'][0]['constitutive_models'][0]['model']='unsupported_model'
        spec['problem']['type']='new_physical_problem'
        Reply.model_validate_json(json.dumps(self.proposal(spec)))
        def strict(node):
            if isinstance(node,dict):
                if node.get('type')=='object':
                    self.assertFalse(node['additionalProperties']);self.assertEqual(set(node['required']),set(node['properties']))
                for item in node.values():strict(item)
            elif isinstance(node,list):
                for item in node:strict(item)
        strict(Reply.model_json_schema())


    def test_registration_keeps_real_problem_and_model_names(self):
        choices=self.catalog.choices();Reply=reply_model(choices['types'],choices['models'],3)
        spec=normalized(self.thermo_spec())
        spec['problem']['type']='thermoelastic'
        spec['materials'][0]['constitutive_models'][1]['model']='thermoelastic'
        parsed=Reply.model_validate_json(json.dumps(self.proposal(spec))).model_dump(mode='json',by_alias=True)
        self.assertEqual(parsed['response']['spec']['problem']['type'],'thermoelastic')
        for placeholder in ('none','required','unknown'):
            invalid=deepcopy(spec);invalid['problem']['type']=placeholder
            with self.assertRaises(ValueError):Selection.model_validate(invalid)


    def test_missing_mesh_does_not_call_classifier(self):
        with self.assertRaises(SelectionError):self.service.chat({'message':"It analyzes any problem."})
        self.client.chat.completions.create.assert_not_called()


    def test_classifier_uses_only_editable_prompt_and_catalog(self):
        state=self.start()
        request=self.selection_request()
        self.assertEqual(request['model'],'gpt-5.4-mini')
        self.assertEqual(request['reasoning_effort'],'low')
        self.assertIn('INITIAL_RAW_REQUEST',request['messages'][1]['content'])
        self.assertIsNone(state['confirmed_selection'])


    def test_ready_library_returns_exact_formula_without_gpt55(self):
        state=self.start()
        final=self.service.confirm({'session_id':state['id'],'turn_index':0})
        self.assertEqual(final['stage'],'function_space_review')
        self.assertIsNone(final['generation'])
        self.assertEqual(final['confirmed_selection'],self.elastic)
        self.assertNotIn('explanation',final['confirmed_selection'])
        self.assertEqual(final['turns'][0]['response']['explanation'],describe_selection(self.elastic))
        self.assertEqual(self.client.chat.completions.create.call_count,3)
        saved=json.loads((self.library/'linear_elasticity_isotropic_formulation.json').read_text())
        self.assertEqual(list(saved),['problem','materials','formulation'])
        self.assertEqual(final['formulation'],saved['formulation'])
        self.assertEqual(final['lookup']['file'],'linear_elasticity_isotropic_formulation.json')
        self.assertEqual(self.catalog.lookup(self.thermal)['status'],'missing')


    def test_only_confirmed_json_reaches_gpt55_and_no_unreviewed_catalog_write(self):
        state=self.start(self.thermal)
        before=set(self.library.rglob('*.json'))
        self.client.chat.completions.create.return_value=response(self.thermal_form())
        review=self.service.confirm({'session_id':state['id'],'turn_index':0})
        self.assertEqual(review['stage'],'expert_review')
        request=self.client.chat.completions.create.call_args.kwargs
        self.assertEqual(request['model'],'gpt-5.5');self.assertEqual(request['reasoning_effort'],'medium')
        self.assertEqual(len(request['messages']),2)
        self.assertEqual(json.loads(request['messages'][1]['content']),review['confirmed_selection'])
        self.assertNotIn('INITIAL_RAW_REQUEST',json.dumps(request['messages']))
        self.assertEqual(set(self.library.rglob('*.json')),before)
        before_calls=self.client.chat.completions.create.call_count
        self.assertEqual(self.service.load(state['id']),review)
        self.assertEqual(self.client.chat.completions.create.call_count,before_calls)


    def test_expert_edit_approval_saves_one_file_and_makes_it_reusable(self):
        state=self.start(self.thermal)
        self.client.chat.completions.create.return_value=response(self.thermal_form())
        review=self.service.confirm({'session_id':state['id'],'turn_index':0})
        formula=deepcopy(review['formulation']);formula['weak_form'][0]['linear_form']='L(w)=0'
        with self.assertRaises(SelectionError):self.service.approve({'session_id':state['id'],'formulation':formula})
        before=self.client.chat.completions.create.call_count
        final=self.service.approve({'session_id':state['id'],'expert_approved':True,'formulation':formula})
        self.assertEqual(final['stage'],'function_space_review');self.assertEqual(final['formulation'],formula)
        self.assertEqual(self.client.chat.completions.create.call_count,before+1)
        path=self.library/final['saved_files']['file']
        self.assertEqual(path.name,'steady_heat_isotropic_formulation.json')
        record=json.loads(path.read_text())
        self.assertEqual(record,{**self.thermal,'formulation':formula})
        self.assertEqual(len(list(self.library.glob('*.json'))),2)
        self.assertEqual(self.catalog.lookup(self.thermal)['status'],'ready')
        self.assertEqual(self.catalog.lookup(self.thermal)['formulation'],formula)
        with self.assertRaises(SelectionError):self.service.approve({'session_id':state['id'],'expert_approved':True,'formulation':formula})
        repeated=self.catalog.register(self.thermal,formula)
        self.assertEqual(repeated['file'],final['saved_files']['file'])
        self.assertEqual(json.loads(path.read_text()),record)
        self.assertEqual(list(self.library.glob('.pending*')),[])


    def test_models_and_reasoning_are_independent_with_formulation_fixed(self):
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':"Analysis request",
            'settings':{'classifier_model':'moonshotai/kimi-k2.5','classifier_reasoning':'none'}})
        request=self.client.chat.completions.create.call_args.kwargs
        self.assertEqual(request['model'],'moonshotai/kimi-k2.5')
        self.assertEqual(request['extra_body']['reasoning'],{'enabled':False,'effort':'none'})
        self.assertEqual(state['settings']['classifier_reasoning'],'none')
        self.client.chat.completions.create.return_value=response(self.proposal(self.thermal))
        state=self.service.chat({'session_id':state['id'],'message':"Change to heat transfer.",
            'settings':{'classifier_model':'gpt-5.4-mini','classifier_reasoning':'default'}})
        request=self.client.chat.completions.create.call_args.kwargs
        self.assertEqual(request['model'],'gpt-5.4-mini');self.assertEqual(request['reasoning_effort'],'low')
        self.client.chat.completions.create.return_value=response(self.thermal_form())
        state=self.service.confirm({'session_id':state['id'],'turn_index':1,
            'settings':{'formulation_model':'gpt-5.4','formulation_reasoning':'low'}})
        request=self.client.chat.completions.create.call_args.kwargs
        self.assertEqual(request['model'],'gpt-5.5');self.assertEqual(request['reasoning_effort'],'medium')
        self.assertEqual(json.loads(request['messages'][1]['content']),self.thermal)
        self.assertNotIn('settings',state['confirmed_selection'])


    def test_failed_generation_retries_with_the_fixed_formulation_model(self):
        state=self.start(self.thermal)
        self.client.chat.completions.create.side_effect=ValueError('test failure')
        with self.assertRaises(SelectionError):self.service.confirm({'session_id':state['id'],'turn_index':0})
        self.assertTrue(self.service.load(state['id'])['can_continue'])
        self.client.chat.completions.create.side_effect=None
        self.client.chat.completions.create.return_value=response(self.thermal_form())
        review=self.service.continue_session({'session_id':state['id'],
            'settings':{'formulation_model':'gpt-5.4-mini','formulation_reasoning':'low'}})
        self.assertEqual(review['stage'],'expert_review')
        self.assertEqual(self.client.chat.completions.create.call_args.kwargs['model'],'gpt-5.5')


    def test_expert_feedback_uses_edited_draft_without_saving_or_changing_selection(self):
        state=self.start_review();before=set(self.library.glob('*.json'))
        edited=deepcopy(state['formulation']);edited['constitutive_parameters'][0]['name']='edited_conductivity'
        revised=deepcopy(edited);revised['weak_form'][0]['test_function']='z'
        self.client.chat.completions.create.return_value=response({'explanation':"Modified the test function notation.",'formulation':revised})
        review=self.service.chat({'session_id':state['id'],'message':"Please use z consistently for the test function.",
            'formulation':edited,'settings':{'formulation_model':'gpt-5.4','formulation_reasoning':'medium'}})
        request=self.client.chat.completions.create.call_args.kwargs
        self.assertEqual(request['model'],'gpt-5.5');self.assertEqual(request['reasoning_effort'],'medium')
        self.assertEqual(json.loads(request['messages'][1]['content']),{'selection':self.thermal})
        self.assertEqual(json.loads(request['messages'][-1]['content']),{'formulation':edited,'feedback':"Please use z consistently for the test function."})
        self.assertEqual(review['stage'],'expert_review');self.assertEqual(review['formulation'],revised)
        self.assertEqual(review['confirmed_selection'],self.thermal)
        self.assertEqual(review['generation'],state['generation']);self.assertEqual(review['review_turns'][0]['input_formulation'],edited)
        self.assertEqual(set(self.library.glob('*.json')),before);self.assertIsNone(review['saved_files'])


    def test_discussion_preserves_draft_and_latest_review_requires_explicit_approval(self):
        state=self.start_review();edited=deepcopy(state['formulation'])
        edited['constitutive_parameters'][0]['name']='edited_conductivity'
        self.client.chat.completions.create.return_value=response({'explanation':"Explains the sign convention based on outward heat flux.",'formulation':None})
        review=self.service.chat({'session_id':state['id'],'message':"Please explain this sign. Do not change the equation.",'formulation':edited})
        self.assertEqual(review['formulation'],edited);self.assertIsNone(review['review_turns'][0]['formulation'])
        with self.assertRaises(SelectionError):self.service.approve({'session_id':state['id'],'expert_approved':True,'formulation':edited})
        with self.assertRaises(SelectionError):self.service.chat({'session_id':state['id'],'message':"This is a question from the previous window."})
        calls=self.client.chat.completions.create.call_count
        final=self.service.approve({'session_id':state['id'],'expert_approved':True,'formulation':edited,'review_turn_index':1})
        saved=json.loads((self.library/final['saved_files']['file']).read_text())
        self.assertEqual(saved,{**self.thermal,'formulation':edited})
        self.assertNotIn('review_turns',saved);self.assertNotIn('explanation',saved)
        self.assertEqual(self.client.chat.completions.create.call_count,calls+1)


    def test_review_history_and_restart_do_not_regenerate_initial_draft(self):
        state=self.start_review()
        self.client.chat.completions.create.return_value=response({'explanation':"This is the first answer.",'formulation':None})
        first=self.service.chat({'session_id':state['id'],'message':"This is the first question."})
        self.client.chat.completions.create.return_value=response({'explanation':"Responding to the previous question.",'formulation':None})
        second=self.service.chat({'session_id':state['id'],'message':"Please continue the explanation.",'review_turn_index':1})
        request=self.client.chat.completions.create.call_args.kwargs
        self.assertEqual(json.loads(request['messages'][2]['content'])['feedback'],"This is the first question.")
        self.assertEqual(json.loads(request['messages'][3]['content']),{'explanation':"This is the first answer.",'formulation':None})
        self.assertEqual(len(second['review_turns']),2);self.assertEqual(second['generation'],state['generation'])
        calls=self.client.chat.completions.create.call_count
        folder=self.service.folder;self.service.close();self.service=ProblemSelectionService(folder,self.library,self.host)
        self.assertEqual(self.service.load(state['id']),second)
        self.assertEqual(self.client.chat.completions.create.call_count,calls)
        self.assertEqual(first['formulation'],second['formulation'])


    def test_failed_review_keeps_previous_draft_and_retries_feedback(self):
        state=self.start_review();edited=deepcopy(state['formulation'])
        edited['constitutive_parameters'][0]['name']='edited_conductivity'
        self.client.chat.completions.create.side_effect=ValueError('test review failure')
        with self.assertRaises(SelectionError):self.service.chat({'session_id':state['id'],'message':"Please review the current draft.",'formulation':edited})
        failed=self.service.load(state['id'])
        self.assertTrue(failed['can_continue']);self.assertEqual(failed['stage'],'revise_formulation')
        self.assertEqual(failed['formulation'],state['formulation']);self.assertEqual(failed['review_input'],edited)
        self.assertEqual(failed['review_message'],"Please review the current draft.");self.assertEqual(failed['review_turns'],[])
        self.client.chat.completions.create.side_effect=None
        self.client.chat.completions.create.return_value=response({'explanation':"After review, keep the current draft.",'formulation':None})
        review=self.service.continue_session({'session_id':state['id'],'settings':{'formulation_model':'gpt-5.4-mini'}})
        self.assertEqual(review['stage'],'expert_review');self.assertEqual(review['formulation'],edited)
        self.assertEqual(len(review['review_turns']),1);self.assertEqual(review['generation'],state['generation'])


    def test_question_cannot_be_confirmed_and_stale_proposal_is_rejected(self):
        self.client.chat.completions.create.return_value=response(self.assessment_question('problem.linearity'))
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':"Please identify the physical model."})
        with self.assertRaises(SelectionError):self.service.confirm({'session_id':state['id'],'turn_index':0})
        self.client.chat.completions.create.return_value=response(self.proposal(self.elastic))
        state=self.service.chat({'session_id':state['id'],'message':"It is small-strain linear elasticity."})
        with self.assertRaises(SelectionError):self.service.confirm({'session_id':state['id'],'turn_index':0})
        self.assertEqual(len(state['turns']),2)


    def test_restart_restores_expert_review_without_another_model_call(self):
        state=self.start(self.thermal)
        self.client.chat.completions.create.return_value=response(self.thermal_form())
        review=self.service.confirm({'session_id':state['id'],'turn_index':0})
        before=self.client.chat.completions.create.call_count
        folder=self.service.folder;self.service.close()
        self.service=ProblemSelectionService(folder,self.library,self.host)
        self.assertEqual(self.service.load(state['id']),review)
        self.assertEqual(self.client.chat.completions.create.call_count,before)


    def test_library_match_hands_off_approved_inputs_to_function_space(self):
        state=self.start_spaces()
        self.assertEqual(state['stage'],'function_space_review');self.assertIsNone(state['functionspace_card'])
        request=self.client.chat.completions.create.call_args.kwargs
        self.assertEqual(request['model'],'gpt-5.4-mini');self.assertEqual(request['reasoning_effort'],'low')
        self.assertIn(json.dumps(self.elastic,ensure_ascii=False),request['messages'][1]['content'])
        context={k:v for k,v in state['formulation'].items() if k not in ('boundary_parameters','source_parameters')}
        self.assertIn(json.dumps(context,ensure_ascii=False),request['messages'][1]['content'])
        self.assertIn('INITIAL_RAW_REQUEST',request['messages'][1]['content'])
        self.assertNotIn('uploaded.msh',request['messages'][1]['content'])
        self.assertNotIn('choose a model',request['messages'][0]['content'])
        self.assertEqual(len(state['functionspace_turns']),1)


    def test_function_space_revision_and_confirmation_hands_off_to_materials(self):
        state=self.start_spaces();approved_form=deepcopy(state['formulation'])
        self.space_answer=self.space_proposal(degree=2)
        revised=self.service.chat({'session_id':state['id'],'message':"Please change to second order.",'functionspace_turn_index':0})
        self.assertEqual(len(revised['functionspace_turns']),2);self.assertIsNone(revised['functionspace_card'])
        self.assertEqual(revised['formulation'],approved_form);self.assertEqual(revised['confirmed_selection'],self.elastic)
        with self.assertRaises(SelectionError):self.service.confirm_spaces({'session_id':state['id'],'functionspace_turn_index':0})
        calls=self.client.chat.completions.create.call_count
        done=self.service.confirm_spaces({'session_id':state['id'],'functionspace_turn_index':1})
        self.assertEqual(done['stage'],'material_review')
        self.assertEqual(done['functionspace_card']['unknowns'][0]['function_space'],{'family':'Lagrange','degree':2})
        self.assertEqual(set(done['functionspace_card']),{'unknowns','coupling_type','state_variables'})
        self.assertEqual(self.client.chat.completions.create.call_count,calls+1)
        self.assertTrue(self.service.snapshot(state['id']).next)
        self.assertNotIn('boundary_card',done);self.assertNotIn('solver',done)
        with self.assertRaises(SelectionError):self.service.start_spaces({'session_id':state['id']})


    def test_function_space_question_waits_for_answer(self):
        self.space_answer=self.space_question(explanation='Which polynomial degree is needed?')
        state=self.start_spaces()
        with self.assertRaises(SelectionError):self.service.confirm_spaces({'session_id':state['id'],'functionspace_turn_index':0})
        self.space_answer=self.space_proposal(degree=2)
        answered=self.service.chat({'session_id':state['id'],'message':"Please make it second order.",'functionspace_turn_index':0})
        self.assertEqual(answered['functionspace_turns'][-1]['response']['proposed_card']['unknowns'][0]['function_space']['degree'],2)
        request=self.client.chat.completions.create.call_args.kwargs
        self.assertIn('Which polynomial degree is needed?',request['messages'][2]['content'])


    def test_function_space_context_prevents_changing_unknowns_and_coupling(self):
        Reply=space_agent.response_model(self.elastic)
        bad=self.space_proposal();bad['response']['card']['unknowns']['stress']=bad['response']['card']['unknowns'].pop('displacement')
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(bad))
        bad=self.space_proposal();bad['response']['card']['coupling_type']='multiphysics_one_way'
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(bad))
        card=space_agent.assemble_draft(self.space_proposal()['response'],self.elastic)
        card['coupling_type']='multiphysics_one_way'
        with self.assertRaises(ValueError):space_agent.check_card(card,self.elastic)


    def test_failed_function_space_retry_does_not_repeat_formulation_work(self):
        state=self.start()
        self.space_answer=ValueError('test space failure')
        with self.assertRaises(SelectionError):self.service.confirm({'session_id':state['id'],'turn_index':0})
        failed=self.service.load(state['id'])
        self.assertEqual(failed['stage'],'function_space');self.assertTrue(failed['can_continue'])
        self.assertIsNotNone(failed['formulation'])
        self.space_answer=None
        restored=self.service.continue_session({'session_id':state['id'],'settings':{'functionspace_model':'qwen/qwen3.5-27b'}})
        self.assertEqual(restored['stage'],'function_space_review');self.assertIsNone(restored['generation'])
        self.assertEqual(self.client.chat.completions.create.call_args.kwargs['model'],'qwen/qwen3.5-27b')


    def test_function_space_waiting_checkpoint_restores_without_model_calls(self):
        state=self.start_spaces();calls=self.client.chat.completions.create.call_count
        folder=self.service.folder;self.service.close();self.service=ProblemSelectionService(folder,self.library,self.host)
        self.assertEqual(self.service.load(state['id']),state)
        self.assertEqual(self.client.chat.completions.create.call_count,calls)


    def test_existing_formulation_only_session_can_start_function_space(self):
        state=self.start_spaces();state['stage']='complete';state['functionspace_turns']=[];state['functionspace_card']=None
        state.pop('can_continue',None)
        self.service.workflow.graph.update_state(self.service.workflow.config(state['id']),state,as_node='function_space_review')
        calls=self.client.chat.completions.create.call_count
        resumed=self.service.start_spaces({'session_id':state['id']})
        self.assertEqual(resumed['stage'],'function_space_review')
        self.assertEqual(len(resumed['functionspace_turns']),1)
        self.assertEqual(self.client.chat.completions.create.call_count,calls+1)
        self.assertEqual(resumed['formulation'],state['formulation'])


    def test_material_stage_asks_for_missing_values_and_uses_only_material_context(self):
        state=self.start_materials()
        self.assertEqual(state['stage'],'material_review');self.assertIsNone(state['material_card'])
        self.assertNotIn('proposed_card',state['material_turns'][0]['response'])
        request=self.client.chat.completions.create.call_args.kwargs
        self.assertEqual(request['model'],'gpt-5.4-mini');self.assertEqual(request['reasoning_effort'],'low')
        text=request['messages'][1]['content']
        self.assertIn('youngs_modulus',text);self.assertIn('poissons_ratio',text);self.assertIn('Specimen',text)
        self.assertNotIn('traction',text);self.assertNotIn('body_force',text)
        with self.assertRaises(SelectionError):self.service.confirm_materials({'session_id':state['id'],'material_turn_index':0})


    def test_material_confirmation_preserves_input_units_and_hands_off_to_boundaries(self):
        state=self.start_materials();before=set(self.library.glob('*.json'))
        self.material_answer=self.material_proposal()
        selected=[{'name':'Specimen','dim':3,'tags':[1]}]
        proposed=self.service.chat({'session_id':state['id'],'message':"E=210 GPa, nu=0.3, applies to the entire specimen.",
            'material_turn_index':0,'material_selection':selected})
        self.assertEqual(proposed['material_turns'][-1]['selection'],selected)
        self.assertEqual(proposed['functionspace_card'],state['functionspace_card'])
        self.assertEqual(proposed['formulation'],state['formulation'])
        with self.assertRaises(SelectionError):self.service.confirm_materials({'session_id':state['id'],'material_turn_index':0})
        calls=self.client.chat.completions.create.call_count
        final=self.service.confirm_materials({'session_id':state['id'],'material_turn_index':1})
        self.assertEqual(final['stage'],'boundary_parameter_review');self.assertEqual(self.client.chat.completions.create.call_count,calls+1)
        self.assertEqual(final['material_card']['constitutive_parameters'][0]['value'],210.0)
        self.assertEqual(final['material_card']['constitutive_parameters'][0]['unit'],'GPa')
        self.assertEqual(set(final['material_card']),{'constitutive_parameters'})
        self.assertNotIn('solver_card',final);self.assertIsNone(final['boundary_parameter_assessment'])
        self.assertEqual(set(self.library.glob('*.json')),before)
        with self.assertRaises(SelectionError):self.service.start_materials({'session_id':state['id']})


    def test_material_card_rejects_unknown_missing_overlapping_and_facet_bindings(self):
        card=self.material_card();cases=[]
        bad=deepcopy(card);bad['constitutive_parameters'][0]['name']='extra_parameter';cases.append(bad)
        bad=deepcopy(card);bad['constitutive_parameters'].pop();cases.append(bad)
        bad=deepcopy(card);bad['constitutive_parameters'][0]['regions'][0]['dim']=2;cases.append(bad)
        bad=deepcopy(card);bad['constitutive_parameters'][0]['regions'][0]['tags']=[999];cases.append(bad)
        bad=deepcopy(card);bad['constitutive_parameters'].append(deepcopy(bad['constitutive_parameters'][0]));cases.append(bad)
        for bad in cases:
            with self.assertRaises(ValueError):material_agent.check_card(bad,self.catalog.lookup(self.elastic)['formulation'],self.mesh['summary'])
        state=self.start_materials()
        before=self.client.chat.completions.create.call_count
        with self.assertRaises(SelectionError):self.service.chat({'session_id':state['id'],'message':"Applies to the selected region.",
            'material_turn_index':0,'material_selection':[{'name':'Specimen','dim':2,'tags':[1]}]})
        self.assertEqual(self.client.chat.completions.create.call_count,before)


    def test_materials_can_bind_different_values_to_different_volumes(self):
        summary=deepcopy(self.mesh['summary']);summary['volume_groups'].append({'name':'Other','dim':3,'tags':[2]})
        card=self.material_card()
        for parameter in deepcopy(card['constitutive_parameters']):
            parameter['regions']=[{'name':'Other','dim':3,'tags':[2]}];parameter['value']*=0.5
            card['constitutive_parameters'].append(parameter)
        validated=material_agent.check_card(card,self.catalog.lookup(self.elastic)['formulation'],summary)
        self.assertEqual(len(validated['constitutive_parameters']),4)


    def test_material_checkpoint_and_existing_functionspace_sessions_resume(self):
        state=self.start_materials();calls=self.client.chat.completions.create.call_count
        folder=self.service.folder;self.service.close();self.service=ProblemSelectionService(folder,self.library,self.host)
        self.assertEqual(self.service.load(state['id']),state);self.assertEqual(self.client.chat.completions.create.call_count,calls)
        state.update(stage='complete',material_turns=[],material_card=None);state.pop('can_continue',None)
        self.service.workflow.graph.update_state(self.service.workflow.config(state['id']),state,as_node='material_review')
        resumed=self.service.start_materials({'session_id':state['id']})
        self.assertEqual(resumed['stage'],'material_review');self.assertEqual(resumed['functionspace_card'],state['functionspace_card'])
        self.assertEqual(self.client.chat.completions.create.call_count,calls+1)


    def test_failed_material_retry_keeps_approved_inputs(self):
        state=self.start_spaces();self.material_answer=ValueError('test material failure')
        with self.assertRaises(SelectionError):self.service.confirm_spaces({'session_id':state['id'],'functionspace_turn_index':0})
        failed=self.service.load(state['id']);self.assertTrue(failed['can_continue']);self.assertEqual(failed['stage'],'material_parameters')
        self.assertIsNotNone(failed['functionspace_card'])
        self.material_answer=None
        restored=self.service.continue_session({'session_id':state['id'],'settings':{'material_model':'moonshotai/kimi-k2.5'}})
        self.assertEqual(restored['stage'],'material_review');self.assertEqual(self.client.chat.completions.create.call_args.kwargs['model'],'moonshotai/kimi-k2.5')
        self.assertEqual(restored['formulation'],state['formulation'])


    def test_input_questions_have_no_choices_and_recommendations_allow_one_or_two_candidates(self):
        value={'question_type':'input','question':"Please tell me the values and units for heat input and convection coefficient.",'options':[]}
        self.assertEqual(InputQuestion.model_validate(value).model_dump(),value)
        bad=deepcopy(value);bad['options']=[{'label':"Enter value",'description':"Please enter a number."}]
        with self.assertRaises(ValueError):InputQuestion.model_validate(bad)
        alternatives=[{'label':"Temperature specification",'description':"Specifies the temperature of the face."},
                      {'label':"Heat input specification",'description':"Specifies the heat flowing into the face."}]
        choice={'question_type':'choice','question':"What condition should be applied to the bottom face?",'options':alternatives}
        self.assertEqual(ChoiceQuestion.model_validate(choice).model_dump(),choice)
        self.assertEqual(ChoiceQuestion.model_validate({**choice,'options':alternatives[:1]}).options[0].label,"Temperature specification")
        with self.assertRaises(ValueError):ChoiceQuestion.model_validate({**choice,'options':[]})
        recommended={'question_type':'recommendation','question':"Please check the assumptions and choose a recommended value or enter a value directly.",
            'options':[{'label':"Initial value for exploration",'description':"This is a value assumed for an example condition and is not an actual measured value.",
                'values':[{'name':'parameter','value':1.0,'unit':'W'}]}]}
        for count in (1,2):
            self.assertEqual(len(RecommendationQuestion.model_validate({**recommended,'options':recommended['options']*count}).options),count)
        for count in (0,3):
            with self.assertRaises(ValueError):RecommendationQuestion.model_validate({**recommended,'options':recommended['options']*count})
        with self.assertRaises(ValueError):RecommendationQuestion.model_validate({**recommended,'options':[{'label':"Enter manually",'description':"Please enter a value."}]})


    def test_recommended_material_values_stay_unconfirmed_until_user_accepts_and_approves(self):
        self.material_answer=self.material_recommendation()
        state=self.start_materials()
        self.assertIsNone(state['material_card'])
        with self.assertRaises(SelectionError):self.service.confirm_materials({'session_id':state['id'],'material_turn_index':0})
        self.material_answer=self.material_proposal()
        proposed=self.service.chat({'session_id':state['id'],'material_turn_index':0,
            'message':"I will use the example values E=210 GPa, ν=0.3 for the entire specimen."})
        self.assertIsNone(proposed['material_card']);self.assertIn('proposed_card',proposed['material_turns'][-1]['response'])
        approved=self.service.confirm_materials({'session_id':state['id'],'material_turn_index':1})
        self.assertEqual(approved['material_card'],self.material_card())

