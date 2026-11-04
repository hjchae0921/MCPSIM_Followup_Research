"""Dirichlet selection and a separate, complete value approval workflow."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from tests import test_parameters as fixtures
from tests.fixtures import response
from boundary_condition_agent import parameter_selection as selection
from boundary_condition_agent import values
from problem_selection_agent.service import SelectionError


class BoundaryValuesTests(unittest.TestCase):
    def setUp(self):
        self.case=fixtures.ParameterSelectionTests();self.case.setUp();self.addCleanup(self.case.doCleanups)
        self.f=self.case.f;self.service=self.f.service

    def start(self):
        state=self.case.start();reply=deepcopy(state['boundary_parameter_turns'][-1]['response'])
        reply['assessment']['dirichlet_conditions']=[
            {'field':'displacement','requirement':'needed','regions':[{'name':'Grip_Left','dim':2,'tags':[2]}],'components':[],'reason':"Fully fixed on the left"},
            {'field':'displacement','requirement':'needed','regions':[{'name':'Grip_Right','dim':2,'tags':[3]}],'components':[0],'reason':"Axial tension on the right"}]
        self.case.answer=reply
        state=self.service.chat({'session_id':state['id'],'boundary_parameter_turn_index':0,'message':"Fix the left side and specify x-direction displacement on the right."})
        return self.service.confirm_boundary_parameter_selection({'session_id':state['id'],'boundary_parameter_turn_index':1})

    def test_questions_are_required_only_for_unresolved_values_or_units(self):
        rows=self.start()['boundary_value_requirements']
        reply={'explanation':'Resolve the remaining displacement.',
            'draft':[{'id':rows[0]['id'],'value':[0,0,0],'unit':'mm'},
                     {'id':rows[1]['id'],'value':None,'unit':'mm'}],
            'question':{'question_type':'input','question':'Specify the right displacement.',
                'options':[],'targets':[f'draft.{rows[1]["id"]}.value']}}
        self.assertEqual(values.check_reply(reply,rows),reply)
        for targets in ([f'draft.{rows[0]["id"]}.value'],[f'draft.{rows[1]["id"]}.unit'],
                        [f'draft.{rows[1]["id"]}.value']*2):
            bad=deepcopy(reply);bad['question']['targets']=targets
            with self.subTest(targets=targets),self.assertRaisesRegex(ValueError,'distinct unresolved'):
                values.check_reply(bad,rows)
        bad=deepcopy(reply);bad['question']=None
        with self.assertRaisesRegex(ValueError,'clarification question'):values.check_reply(bad,rows)
        reply['draft'][1]['value']=0
        with self.assertRaisesRegex(ValueError,'distinct unresolved'):values.check_reply(reply,rows)
        reply['question']=None
        self.assertTrue(values.complete(values.check_reply(reply,rows)['draft']))

    def test_recommendations_share_value_shape_and_question_scope_validation(self):
        rows=self.start()['boundary_value_requirements']
        reply={'explanation':'Review these trial values.',
            'draft':[{'id':row['id'],'value':None,'unit':None} for row in rows],
            'question':{'question_type':'recommendation','question':'Use these displacement values?',
                'targets':[f'draft.{row["id"]}.{key}' for row in rows for key in ('value','unit')],
                'options':[{'label':'Trial displacement','description':'Fix the left grip and pull the right grip.',
                    'values':[{'name':rows[0]['id'],'value':[0,0,0],'unit':'mm'},
                              {'name':rows[1]['id'],'value':0.1,'unit':'mm'}]}]}}
        checked=values.check_reply(reply,rows)
        self.assertIsNone(checked['draft'][0]['value'])
        for mutation in ('shape','duplicate','foreign','outside_question'):
            bad=deepcopy(reply);items=bad['question']['options'][0]['values']
            if mutation=='shape':items[0]['value']=0
            if mutation=='duplicate':items.append(deepcopy(items[0]))
            if mutation=='foreign':items[0]['name']='not_a_condition'
            if mutation=='outside_question':bad['question']['targets']=[f'draft.{rows[1]["id"]}.value']
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):values.check_reply(bad,rows)

    def test_invalid_value_question_is_repaired_without_changing_approved_conditions(self):
        state=self.start();rows=state['boundary_value_requirements'];approved=deepcopy(state['boundary_parameter_assessment'])
        valid={'explanation':'Review the complete values.',
            'draft':[{'id':rows[0]['id'],'value':[0,0,0],'unit':'mm'},
                     {'id':rows[1]['id'],'value':0.1,'unit':'mm'}],'question':None}
        invalid=deepcopy(valid)
        invalid['question']={'question_type':'input','question':'Confirm this filled value.',
            'options':[],'targets':[f'draft.{rows[0]["id"]}.value']}
        with patch.object(self.f.client.chat.completions,'create',side_effect=[response(invalid),response(valid)]) as call:
            result=self.service.chat({'session_id':state['id'],'boundary_value_turn_index':0,
                'message':'Use zero displacement on the left and 0.1 mm on the right.'})
        self.assertEqual(call.call_count,2)
        self.assertEqual(result['boundary_value_turns'][-1]['validation_repairs'],1)
        self.assertEqual(result['boundary_parameter_assessment'],approved)
        self.assertIsNone(result.get('boundary_value_card'))
        self.assertEqual(result['authoring_status']['status'],'ready_for_review')

    def test_values_only_for_needed_conditions_missing_zero_and_scalar_vector_shapes(self):
        state=self.start();sid=state['id'];rows=state['boundary_value_requirements']
        self.assertEqual(state['stage'],'boundary_value_review');self.assertEqual(len(rows),2)
        self.assertTrue(all(row['scope']=='dirichlet_conditions' for row in rows))
        self.assertEqual(rows[0]['shape'],[3]);self.assertEqual(rows[1]['shape'],[])
        with self.assertRaises(SelectionError):self.service.confirm_boundary_values({'session_id':sid,'boundary_value_turn_index':0})
        draft=[{'id':rows[0]['id'],'value':[0,0,0],'unit':'mm'},{'id':rows[1]['id'],'value':None,'unit':'mm'}]
        before=self.f.client.chat.completions.create.call_count
        state=self.service.update_boundary_values({'session_id':sid,'boundary_value_turn_index':0,'draft':draft})
        self.assertEqual(self.f.client.chat.completions.create.call_count,before)
        self.assertEqual(state['boundary_value_draft'][0]['value'],[0,0,0]);self.assertIsNone(state['boundary_value_draft'][1]['value'])
        with self.assertRaises(SelectionError):self.service.confirm_boundary_values({'session_id':sid,'boundary_value_turn_index':1})
        draft[1]['value']=0
        state=self.service.update_boundary_values({'session_id':sid,'boundary_value_turn_index':1,'draft':draft})
        final=self.service.confirm_boundary_values({'session_id':sid,'boundary_value_turn_index':2})
        self.assertEqual(final['stage'],'solver_review');self.assertTrue(self.service.snapshot(sid).next)
        self.assertEqual(final['boundary_value_card']['dirichlet_conditions'][1]['value'],0)
        self.assertEqual(final['boundary_value_card']['boundary_parameters'],[])
        self.assertEqual(self.f.client.chat.completions.create.call_count,before+1)
        self.assertFalse(final.get('solver_card'))

    def test_values_cannot_drop_or_add_regions_and_stale_inputs_are_rejected(self):
        state=self.start();sid=state['id'];rows=state['boundary_value_requirements']
        draft=[{'id':r['id'],'value':[0,0,0] if r['shape'] else 1,'unit':'mm'} for r in rows]
        for bad in (draft[:-1],draft+draft[:1],[dict(draft[0],value=0),draft[1]],
                    [dict(draft[0],id='other'),draft[1]],[dict(draft[0],region={'name':'new'}),draft[1]]):
            with self.assertRaises(SelectionError):self.service.update_boundary_values({'session_id':sid,'boundary_value_turn_index':0,'draft':bad})
        self.service.update_boundary_values({'session_id':sid,'boundary_value_turn_index':0,'draft':draft})
        with self.assertRaises(SelectionError):self.service.update_boundary_values({'session_id':sid,'boundary_value_turn_index':0,'draft':draft})

    def test_dialogue_receives_approved_conditions_and_preserves_partial_inputs(self):
        state=self.start();sid=state['id'];rows=state['boundary_value_requirements']
        draft=[{'id':rows[0]['id'],'value':[0,0,0],'unit':'mm'},{'id':rows[1]['id'],'value':None,'unit':None}]
        self.service.update_boundary_values({'session_id':sid,'boundary_value_turn_index':0,'draft':draft})
        draft[1].update(value=1,unit='mm')
        self.case.value_answer={'explanation':"Kept zero displacement on the left and applied the tensile value on the right.",'draft':draft,'question':None}
        state=self.service.chat({'session_id':sid,'boundary_value_turn_index':1,'message':"The right x-direction will be 1 mm."})
        context=json.loads(self.f.client.chat.completions.create.call_args.kwargs['messages'][1]['content'])
        self.assertEqual(len(context['required_values']),2)
        self.assertEqual(context['approved_conditions'],state['boundary_parameter_assessment'])
        self.assertEqual(context['current_draft'][0]['value'],[0,0,0])
        self.assertNotIn('solver',context)
        self.assertEqual(state['boundary_value_draft'][1]['value'],1)
        final=self.service.confirm_boundary_values({'session_id':sid,'boundary_value_turn_index':2})
        self.assertEqual(final['boundary_value_card']['dirichlet_conditions'][1]['unit'],'mm')

    def test_dirichlet_requires_each_unknown_real_boundaries_valid_components_and_no_duplicates(self):
        state=self.case.start();unknowns=state['functionspace_card']['unknowns'];assessment=state['boundary_parameter_turns'][0]['response']['assessment']
        for mutation in ('missing','unknown','region','component','duplicate'):
            bad=deepcopy(assessment);items=bad['dirichlet_conditions'];item=items[0]
            if mutation=='missing':items.clear()
            elif mutation=='unknown':item['field']='not_a_field'
            else:
                item.update(requirement='needed',regions=[{'name':'Grip_Left','dim':2,'tags':[2]}],components=[])
                if mutation=='region':item['regions'][0]['tags']=[88]
                if mutation=='component':item['components']=[3]
                if mutation=='duplicate':items.append(deepcopy(item))
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):selection.check_assessment(bad,state['formulation'],self.f.mesh['summary'],unknowns)

    def test_required_values_cover_boundary_source_and_dirichlet_per_region(self):
        state=self.start();assessment=deepcopy(state['boundary_parameter_assessment'])
        assessment['boundary_parameters'][0].update(requirement='needed',regions=[{'name':'Grip_Right','dim':2,'tags':[3]}])
        assessment['source_parameters'][0].update(requirement='needed',regions=[{'name':'Specimen','dim':3,'tags':[1]}])
        rows=values.requirements(assessment,state['formulation'],self.f.mesh['summary'],state['functionspace_card']['unknowns'])
        self.assertEqual([r['scope'] for r in rows],['boundary_parameters','source_parameters','dirichlet_conditions','dirichlet_conditions'])
        draft=[{'id':r['id'],'value':[0,0,0] if r.get('shape') else 0,'unit':'mm' if r['scope']=='dirichlet_conditions' else 'N'} for r in rows]
        card=values.card(draft,rows)
        self.assertEqual(len(card['boundary_parameters']),1);self.assertEqual(len(card['source_parameters']),1);self.assertEqual(len(card['dirichlet_conditions']),2)
        def strict(node):
            if isinstance(node,dict):
                if '$ref' in node:self.assertEqual(set(node),{'$ref'})
                if node.get('type')=='object':self.assertFalse(node['additionalProperties']);self.assertEqual(set(node['required']),set(node['properties']))
                for child in node.values():strict(child)
            elif isinstance(node,list):
                for child in node:strict(child)
        strict(values.response_model(rows).model_json_schema())

    def test_old_assessment_requires_reassessment_and_retry_keeps_approved_requirements(self):
        state=self.case.start();sid=state['id']
        state['boundary_parameter_turns'][-1]['response']['assessment'].pop('dirichlet_conditions')
        self.service.workflow.graph.update_state(self.service.workflow.config(sid),{'boundary_parameter_turns':state['boundary_parameter_turns']},as_node='boundary_parameter_selection')
        self.service._run(sid,None)
        with self.assertRaises(SelectionError):self.service.confirm_boundary_parameter_selection({'session_id':sid,'boundary_parameter_turn_index':0})
        # A fresh, complete selection can still advance after a failed value request.
        self.case.value_answer=ValueError('temporary values failure')
        reply=deepcopy(state['boundary_parameter_turns'][-1]['response'])
        reply['assessment']['dirichlet_conditions']=[{'field':'displacement','requirement':'needed','regions':[{'name':'Grip_Left','dim':2,'tags':[2]}],'components':[],'reason':"Fixed"}]
        self.case.answer=reply
        state=self.service.chat({'session_id':sid,'boundary_parameter_turn_index':0,'message':"Review Dirichlet."})
        with self.assertRaises(SelectionError):self.service.confirm_boundary_parameter_selection({'session_id':sid,'boundary_parameter_turn_index':1})
        self.assertTrue(self.service.load(sid)['can_continue'])
        self.case.value_answer=None
        final=self.service.continue_session({'session_id':sid})
        self.assertEqual(final['stage'],'boundary_value_review');self.assertEqual(len(final['boundary_value_requirements']),1)


if __name__=='__main__':unittest.main()
