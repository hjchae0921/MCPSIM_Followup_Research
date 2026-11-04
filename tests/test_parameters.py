"""Reduced boundary experiment: classify candidates, converse, approve, then stop."""
from copy import deepcopy
import json
import unittest
from unittest.mock import DEFAULT, patch

from tests import fixtures
from boundary_condition_agent import parameter_selection as agent
from problem_selection_agent.service import SelectionError


class ParameterSelectionTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.AuthoringFixture()
        self.f.setUp()
        self.addCleanup(self.f.tearDown)
        self.answer=None
        self.value_answer=None
        original=self.f.dispatch
        def dispatch(**request):
            if request['response_format']['json_schema']['name']=='boundary_values':
                if isinstance(self.value_answer,Exception):raise self.value_answer
                if self.value_answer is not None:return fixtures.response(self.value_answer)
                context=json.loads(request['messages'][1]['content'])
                return fixtures.response({'explanation':"Please enter the required values and units.",'draft':[{'id':row['id'],'value':None,'unit':None} for row in context['required_values']],
                    'question':{'question_type':'input','question':"Please enter the required values and units.",'options':[],'targets':['draft.'+context['required_values'][0]['id']+'.value']}})
            if request['response_format']['json_schema']['name']!='boundary_parameter_selection':return original(**request)
            if isinstance(self.answer,Exception):raise self.answer
            if self.answer is not None:return fixtures.response(agent.provider_reply(self.answer))
            context=json.loads(request['messages'][1]['content'])
            assessment={key:[{'name':p['name'],'requirement':'not_needed','regions':[],'reason':"Not used."} for p in context[key]] for key in ('boundary_parameters','source_parameters')}
            assessment['dirichlet_conditions']=[{'field':u['name'],'requirement':'not_needed','regions':[],'components':[],'reason':"Not used."} for u in context['unknowns']]
            return fixtures.response({'explanation':"Because displacement is specified, the candidate surface forces and body forces are not used.",
                'assessment':assessment,'recommendations':[]})
        self.f.client.chat.completions.create.side_effect=dispatch

    def start(self):
        return self.f.start_source_boundaries()

    def dirichlet_reply(self,state):
        reply=agent.provider_reply(state['boundary_parameter_turns'][-1]['response'])
        reply['assessment']['dirichlet_conditions']=[
            {'field':'displacement','requirement':'needed','regions':[{'name':'Grip_Left','dim':2,'tags':[2]}],
             'components':[0,1,2],'reason':"Left fixed"},
            {'field':'displacement','requirement':'needed','regions':[{'name':'Grip_Right','dim':2,'tags':[3]}],
             'components':[0],'reason':"Right tension"}]
        return reply

    def test_dirichlet_schema_encodes_usage_and_checker_rejects_field_level_contradictions(self):
        state=self.start();Reply=agent.response_model(state['formulation'],self.f.mesh['summary'],state['functionspace_card']['unknowns'])
        valid=self.dirichlet_reply(state)
        Reply.model_validate_json(json.dumps(valid))
        for mutation in ('needed_without_region','not_needed_with_region','not_needed_with_component'):
            bad=deepcopy(valid);item=bad['assessment']['dirichlet_conditions'][0]
            if mutation=='needed_without_region':item['regions']=[]
            else:
                item.update(requirement='not_needed',components=[])
                if mutation=='not_needed_with_component':item.update(regions=[],components=[0])
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(bad))
        contradictory=deepcopy(valid)
        contradictory['assessment']['dirichlet_conditions'].append(
            {'field':'displacement','requirement':'not_needed','regions':[],'components':[],'reason':"The other faces are free surfaces"})
        before=deepcopy(contradictory)
        with self.assertRaisesRegex(ValueError,'whole field'):
            agent.check_reply(contradictory,state['formulation'],self.f.mesh['summary'],state['functionspace_card']['unknowns'])
        self.assertEqual(contradictory,before)

    def test_invalid_boundary_answer_is_repaired_by_model_and_still_requires_review(self):
        state=self.start();valid=self.dirichlet_reply(state);invalid=deepcopy(valid)
        invalid['assessment']['dirichlet_conditions'].append(
            {'field':'displacement','requirement':'not_needed','regions':[],'components':[],'reason':"The other faces are free surfaces"})
        before={key:deepcopy(state[key]) for key in ('confirmed_selection','formulation','functionspace_card','material_card')}
        with patch.object(self.f.client.chat.completions,'create',side_effect=[fixtures.response(invalid),fixtures.response(valid)]) as call:
            result=self.f.service.chat({'session_id':state['id'],'boundary_parameter_turn_index':0,'message':"Please check the boundary conditions."})
            self.assertEqual(call.call_count,2)
            first,second=[c.kwargs for c in call.call_args_list]
            self.assertEqual(first['model'],second['model']);self.assertEqual(first['response_format'],second['response_format'])
            self.assertEqual(second['messages'][:-2],first['messages'])
            self.assertEqual(json.loads(second['messages'][-2]['content']),agent.wire_reply(invalid))
            self.assertIn('whole field',second['messages'][-1]['content'])
        self.assertEqual(result['stage'],'boundary_parameter_review')
        self.assertEqual(result['boundary_parameter_turns'][-1]['response'],agent.present_review(valid))
        self.assertEqual(result['boundary_parameter_turns'][-1]['validation_repairs'],1)
        self.assertFalse(result.get('boundary_parameter_assessment'));self.assertFalse(result.get('boundary_value_card'))
        self.assertEqual({key:result[key] for key in before},before)
        saved=list((self.f.service.folder/state['id']/'boundary_parameter_selection').glob('*/response.json'))
        self.assertEqual(len(saved),3)

    def test_repair_limit_keeps_last_valid_turn_and_allows_retry(self):
        state=self.start();valid=self.dirichlet_reply(state);self.answer=deepcopy(valid)
        self.answer['assessment']['dirichlet_conditions'].append(
            {'field':'displacement','requirement':'not_needed','regions':[],'components':[],'reason':"The other faces are free surfaces"})
        before=self.f.client.chat.completions.create.call_count
        with self.assertRaisesRegex(SelectionError,'whole field'):
            self.f.service.chat({'session_id':state['id'],'boundary_parameter_turn_index':0,'message':"Please check the boundary conditions."})
        self.assertEqual(self.f.client.chat.completions.create.call_count,before+2)
        pending=self.f.service.load(state['id']);self.assertTrue(pending['can_continue'])
        self.assertEqual(pending['boundary_parameter_turns'],state['boundary_parameter_turns'])
        self.answer=valid;result=self.f.service.continue_session({'session_id':state['id']})
        self.assertEqual(result['stage'],'boundary_parameter_review')
        self.assertEqual(len(result['boundary_parameter_turns']),2)

    def test_material_and_boundary_approval_hands_off_to_solver(self):
        state=self.start();self.assertEqual(state['stage'],'boundary_parameter_review')
        self.assertFalse(state.get('boundary_plan'));self.assertFalse(state.get('boundary_card'))
        request=self.f.client.chat.completions.create.call_args.kwargs
        self.assertEqual(request['model'],'gpt-5.4-mini');self.assertEqual(request['reasoning_effort'],'low')
        context=json.loads(request['messages'][1]['content'])
        self.assertEqual(set(context),{'user_request','weak_form','boundary_parameters','source_parameters','boundary_regions','volume_regions','coordinate_unit','unknowns'})
        self.assertEqual(context['weak_form'],state['formulation']['weak_form'])
        for forbidden in ('solver','material_card','function_space','constitutive_parameters'):
            self.assertNotIn(forbidden,context)
        before=self.f.client.chat.completions.create.call_count
        final=self.f.service.confirm_boundary_parameter_selection({'session_id':state['id'],'boundary_parameter_turn_index':0})
        self.assertEqual(final['stage'],'boundary_value_review')
        final=self.f.service.confirm_boundary_values({'session_id':state['id'],'boundary_value_turn_index':0})
        self.assertEqual(final['stage'],'solver_review');self.assertTrue(self.f.service.snapshot(state['id']).next)
        self.assertEqual(self.f.client.chat.completions.create.call_count,before+1)
        self.assertTrue(final['boundary_parameter_assessment']);self.assertFalse(final.get('solver_card'))
        self.assertTrue(hasattr(self.f.service,'start_solver'))

    def test_questions_are_derived_only_for_unresolved_condition_details(self):
        state=self.start();form=state['formulation'];summary=self.f.mesh['summary']
        unknowns=state['functionspace_card']['unknowns'];reply=self.dirichlet_reply(state)
        item=reply['assessment']['dirichlet_conditions'][0]
        item.update(requirement='needed',regions=None,components=[0])
        checked=agent.check_reply(reply,form,summary,unknowns)
        self.assertEqual(checked['determination'],'undetermined')
        self.assertEqual(checked['question_targets'],['dirichlet_conditions.displacement.regions'])
        self.assertEqual(checked['unresolved_fields'],checked['question_targets'])
        self.assertIn('application regions',checked['question'])
        self.assertEqual(checked['assessment']['dirichlet_conditions'][0],item)
        item.update(regions=[{'name':'Grip_Left','dim':2,'tags':[2]}],components=None)
        checked=agent.check_reply(reply,form,summary,unknowns)
        self.assertEqual(checked['question_targets'],['dirichlet_conditions.displacement.components'])
        item['components']=[]
        checked=agent.check_reply(reply,form,summary,unknowns)
        self.assertEqual(checked['determination'],'determined');self.assertIsNone(checked['question'])
        item.update(requirement=None,regions=None,components=None)
        checked=agent.check_reply(reply,form,summary,unknowns)
        self.assertEqual(checked['question_targets'],['dirichlet_conditions.displacement.requirement'])

    def test_discussion_and_unresolved_judgment_cannot_be_approved(self):
        state=self.start();reply=agent.provider_reply(state['boundary_parameter_turns'][-1]['response'])
        reply['assessment']['boundary_parameters'][0].update(requirement=None,regions=None)
        self.answer=reply
        state=self.f.service.chat({'session_id':state['id'],'boundary_parameter_turn_index':0,'message':"Please review whether surface forces are used."})
        with self.assertRaises(SelectionError):self.f.service.confirm_boundary_parameter_selection({'session_id':state['id'],'boundary_parameter_turn_index':1})
        with self.assertRaises(SelectionError):self.f.service.chat({'session_id':state['id'],'boundary_parameter_turn_index':0,'message':"Stale response"})
        self.answer=None
        state=self.f.service.chat({'session_id':state['id'],'boundary_parameter_turn_index':1,'message':"Body forces and surface forces are not used."})
        self.assertEqual(len(state['boundary_parameter_turns']),3)
        request=self.f.client.chat.completions.create.call_args.kwargs
        self.assertEqual(len(request['messages']),6)
        self.assertIn("Please review whether surface forces are used.",request['messages'][3]['content'])

    def test_schema_and_validation_cover_actual_regions_and_exact_candidates(self):
        state=self.start();form=state['formulation'];summary=self.f.mesh['summary']
        unknowns=state['functionspace_card']['unknowns'];Reply=agent.response_model(form,summary,unknowns)
        def strict(node):
            if isinstance(node,dict):
                if '$ref' in node:self.assertEqual(set(node),{'$ref'})
                if node.get('type')=='object':
                    self.assertFalse(node['additionalProperties']);self.assertEqual(set(node['required']),set(node['properties']))
                for child in node.values():strict(child)
            elif isinstance(node,list):
                for child in node:strict(child)
        strict(Reply.model_json_schema())
        reply=agent.provider_reply(state['boundary_parameter_turns'][0]['response']);Reply.model_validate_json(json.dumps(reply))
        assessment=deepcopy(reply['assessment']);p=assessment['boundary_parameters'][0]
        p.update(requirement='needed',regions=[{'name':'Grip_Right','dim':2,'tags':[3]}])
        agent.check_assessment(assessment,form,summary,unknowns)
        p['regions'][0]['tags']=[99]
        with self.assertRaises(ValueError):agent.check_assessment(assessment,form,summary,unknowns)
        p['regions']=[{'name':'Specimen','dim':3,'tags':[1]}]
        with self.assertRaises(ValueError):agent.check_assessment(assessment,form,summary,unknowns)
        assessment=deepcopy(reply['assessment']);assessment['boundary_parameters'].pop()
        with self.assertRaises(ValueError):agent.check_assessment(assessment,form,summary,unknowns)
        invalid=deepcopy(reply);invalid['value']=0
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(invalid))
        empty=deepcopy(form);empty.update(boundary_parameters=[],source_parameters=[])
        agent.response_model(empty,summary).model_validate({'explanation':"There are no matching candidates.",'assessment':{'boundary_parameters':[],'source_parameters':[],'dirichlet_conditions':[]},'recommendations':[]})

    def test_restart_preserves_previous_cards_and_failed_node_can_retry(self):
        state=self.start();sid=state['id']
        self.f.service.confirm_boundary_parameter_selection({'session_id':sid,'boundary_parameter_turn_index':0})
        self.f.service.confirm_boundary_values({'session_id':sid,'boundary_value_turn_index':0})
        previous=self.f.service.load(sid)['boundary_value_card']
        self.answer=ValueError('temporary error')
        with self.assertRaises(SelectionError):self.f.service.start_boundary_parameter_selection({'session_id':sid})
        self.assertTrue(self.f.service.load(sid)['can_continue'])
        self.answer=None
        state=self.f.service.continue_session({'session_id':sid})
        self.assertEqual(state['stage'],'boundary_parameter_review')
        self.assertEqual(state['boundary_value_history'][-1]['card'],previous)
        self.assertEqual(len(state['boundary_parameter_turns']),2)

    def test_recommended_combination_is_applied_exactly_without_model_call_and_can_be_edited(self):
        state=self.start();sid=state['id'];reply=agent.provider_reply(state['boundary_parameter_turns'][-1]['response'])
        alternative=deepcopy(reply['assessment'])
        alternative['boundary_parameters'][0].update(requirement='needed',regions=[{'name':'Grip_Right','dim':2,'tags':[3]}])
        reply['recommendations']=[{'label':"Displacement control",'description':"Specify displacement without surface forces.",'assessment':reply['assessment']},
            {'label':"Surface force control",'description':"Apply surface forces to the right boundary.",'assessment':alternative}]
        self.answer=reply
        state=self.f.service.chat({'session_id':sid,'boundary_parameter_turn_index':0,'message':"Please suggest possible combinations."})
        before=self.f.client.chat.completions.create.call_count
        state=self.f.service.choose_boundary_parameter_combination({'session_id':sid,'boundary_parameter_turn_index':1,'recommendation_index':1})
        self.assertEqual(self.f.client.chat.completions.create.call_count,before)
        self.assertEqual(state['stage'],'boundary_parameter_review')
        self.assertIsNone(state['boundary_parameter_assessment'])
        self.assertEqual(state['boundary_parameter_turns'][-1]['response']['assessment'],alternative)
        for bad in ({'boundary_parameter_turn_index':1,'recommendation_index':0},
                    {'boundary_parameter_turn_index':2,'recommendation_index':0}):
            with self.assertRaises(SelectionError):self.f.service.choose_boundary_parameter_combination({'session_id':sid,**bad})
        self.answer=None
        state=self.f.service.chat({'session_id':sid,'boundary_parameter_turn_index':2,'message':"I will set it directly. Neither surface forces nor body forces are used."})
        self.assertTrue(all(p['requirement']=='not_needed' for p in state['boundary_parameter_turns'][-1]['response']['assessment']['boundary_parameters']))
        final=self.f.service.confirm_boundary_parameter_selection({'session_id':sid,'boundary_parameter_turn_index':3})
        final=self.f.service.confirm_boundary_values({'session_id':sid,'boundary_value_turn_index':0})
        self.assertEqual(final['stage'],'solver_review');self.assertFalse(final.get('solver_card'))

    def test_recommendations_must_use_real_regions_and_have_complete_usage(self):
        state=self.start();reply=agent.provider_reply(state['boundary_parameter_turns'][-1]['response'])
        assessment=deepcopy(reply['assessment'])
        assessment['boundary_parameters'][0].update(requirement='needed',regions=[{'name':'Grip_Right','dim':2,'tags':[99]}])
        reply['recommendations']=[{'label':"Condition combination",'description':"Check the application region.",'assessment':assessment}]
        with self.assertRaises(ValueError):agent.check_reply(reply,state['formulation'],self.f.mesh['summary'],state['functionspace_card']['unknowns'])
        assessment['boundary_parameters'][0].update(requirement=None,regions=None)
        with self.assertRaises(ValueError):agent.check_reply(reply,state['formulation'],self.f.mesh['summary'],state['functionspace_card']['unknowns'])
        reply['recommendations']*=3
        with self.assertRaises(ValueError):agent.Reply.model_validate(reply)

    def test_needed_condition_with_unresolved_region_only_asks_for_its_region(self):
        state=self.start();reply=agent.provider_reply(state['boundary_parameter_turns'][-1]['response'])
        reply['assessment']['boundary_parameters'][0].update(requirement='needed',regions=None)
        self.answer=reply
        state=self.f.service.chat({'session_id':state['id'],'boundary_parameter_turn_index':0,'message':'A traction is required; its region is not selected.'})
        last=state['boundary_parameter_turns'][-1]['response']
        self.assertEqual(last['determination'],'undetermined')
        self.assertEqual(last['question_targets'],['boundary_parameters.traction.regions'])
        self.assertEqual(state['authoring_status']['status'],'needs_input')
        with self.assertRaises(SelectionError):
            self.f.service.confirm_boundary_parameter_selection({'session_id':state['id'],'boundary_parameter_turn_index':1})
        reply['assessment']['boundary_parameters'][0]['regions']=[{'name':'Grip_Right','dim':2,'tags':[3]}]
        self.answer=reply
        state=self.f.service.chat({'session_id':state['id'],'boundary_parameter_turn_index':1,'message':'Use Grip_Right.'})
        self.assertEqual(state['boundary_parameter_turns'][-1]['response']['determination'],'determined')
        self.assertEqual(state['authoring_status']['status'],'ready_for_review')
        self.assertNotIn('boundary_parameters',state['authoring_status']['approved_stages'])
        self.assertIsNone(state['boundary_parameter_assessment'])
        # Server-only fields must never become part of the provider's response history.
        request=self.f.client.chat.completions.create.call_args.kwargs
        for message in request['messages']:
            if message['role']=='assistant':
                self.assertEqual(set(json.loads(message['content'])),{'explanation','assessment','recommendations'})
        self.value_answer={'explanation':'Enter the traction value.',
            'draft':[{'id':'condition_1','value':None,'unit':None}],
            'question':{'question_type':'input','question':'What is the traction?',
                'options':[],'targets':['draft.condition_1.value','draft.condition_1.unit']}}
        state=self.f.service.confirm_boundary_parameter_selection({'session_id':state['id'],'boundary_parameter_turn_index':2})
        self.assertEqual(state['stage'],'boundary_value_review')
        self.assertEqual(state['boundary_parameter_assessment'],reply['assessment'])
        self.assertNotIn('determination',state['boundary_parameter_assessment'])
        self.assertEqual(state['boundary_value_requirements'][0]['region']['name'],'Grip_Right')

    def test_nullable_usage_and_components_are_not_confused_with_an_unused_condition(self):
        state=self.start();reply=self.dirichlet_reply(state)
        unknowns=state['functionspace_card']['unknowns'];form=state['formulation'];summary=self.f.mesh['summary']
        Reply=agent.response_model(form,summary,unknowns)
        item=reply['assessment']['dirichlet_conditions'][0]
        item.update(requirement='needed',regions=None,components=None)
        Reply.model_validate_json(json.dumps(reply))
        checked=agent.check_reply(reply,form,summary,unknowns)
        self.assertEqual(set(checked['question_targets']),{'dirichlet_conditions.displacement.regions','dirichlet_conditions.displacement.components'})
        for field in ('regions','components'):
            unused=agent.provider_reply(state['boundary_parameter_turns'][-1]['response'])
            unused['assessment']['dirichlet_conditions'][0][field]=None
            with self.subTest(field=field):
                Reply.model_validate_json(json.dumps(unused))
                checked=agent.check_reply(unused,form,summary,unknowns)
                self.assertEqual(checked['determination'],'determined')
                self.assertEqual(checked['assessment']['dirichlet_conditions'][0][field],[])
        for usage in ('undetermined','required','unknown'):
            invalid=deepcopy(reply);invalid['assessment']['dirichlet_conditions'][0]['requirement']=usage
            with self.subTest(usage=usage),self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(invalid))
        legacy=deepcopy(reply);item=legacy['assessment']['dirichlet_conditions'][0]
        item['status']=item.pop('requirement')
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(legacy))

    def test_scalar_whole_field_components_are_derived_from_the_approved_shape(self):
        state=self.start();reply=agent.provider_reply(state['boundary_parameter_turns'][-1]['response'])
        unknowns=[{'name':'temperature','quantity':'temperature','shape':[]}]
        item={'field':'temperature','requirement':'needed','regions':[{'name':'Grip_Left','dim':2,'tags':[2]}],
            'components':[],'reason':'Prescribed temperature.'}
        reply['assessment']['dirichlet_conditions']=[item]
        self.assertEqual(agent.check_reply(reply,state['formulation'],self.f.mesh['summary'],unknowns)['determination'],'determined')
        item['components']=None
        checked=agent.check_reply(reply,state['formulation'],self.f.mesh['summary'],unknowns)
        self.assertEqual(checked['assessment']['dirichlet_conditions'][0]['components'],[])
        self.assertEqual(checked['question_targets'],[])
        self.assertEqual(checked['determination'],'determined')

    def test_legacy_checkpoints_are_projected_without_rewriting_or_model_calls(self):
        state=self.start();sid=state['id'];old=deepcopy(state['boundary_parameter_turns'])
        response=old[-1]['response']
        for scope in agent.SCOPES:
            for item in response['assessment'][scope]:item['status']=item.pop('requirement')
        response['assessment']['boundary_parameters'][0].update(status='undetermined',regions=[])
        response['assessment']['dirichlet_conditions'][0].update(status='needed',
            regions=[{'name':'Grip_Left','dim':2,'tags':[2]}],components=[])
        response['question']='Old unrelated question.';response['question_targets']=['problem.time_dependence']
        for key in ('determination','unresolved_fields'):response.pop(key,None)
        self.f.service.workflow.graph.update_state(self.f.service.workflow.config(sid),{'boundary_parameter_turns':old},as_node='boundary_parameter_selection')
        before=self.f.client.chat.completions.create.call_count
        result=self.f.service.load(sid);current=result['boundary_parameter_turns'][-1]['response']
        self.assertEqual(current['question_targets'],['boundary_parameters.traction.requirement'])
        self.assertEqual(current['determination'],'undetermined')
        self.assertIsNone(current['assessment']['boundary_parameters'][0]['requirement'])
        self.assertIsNone(current['assessment']['boundary_parameters'][0]['regions'])
        self.assertEqual(current['assessment']['dirichlet_conditions'][0]['components'],[])
        self.assertEqual(self.f.service.snapshot(sid).values['boundary_parameter_turns'],old)
        self.assertEqual(self.f.client.chat.completions.create.call_count,before)


if __name__=='__main__':unittest.main()
