"""User decisions are distinct from model-filled fields and stay outside cards."""
from copy import deepcopy
import json

from common.provenance import decided, material_fields, reconcile, sync
from material_agent import agent
from problem_selection_agent.service import ProblemSelectionService, SelectionError
from tests.fixtures import AuthoringFixture


class FieldProvenanceTests(AuthoringFixture):
    def test_nonnull_model_unit_can_be_replaced_with_complete_candidate_pair(self):
        self.material_answer=self.material_recommendation()
        self.material_answer['response']['card']['constitutive_parameters']['youngs_modulus'][0]['unit']='Pa'
        self.material_answer['response']['ambiguities'][0]['options'][0]['updates'][0].update(value=210000,unit='MPa')
        state=self.start_materials()
        path='constitutive_parameters.youngs_modulus.0.unit'
        self.assertEqual(state['field_status']['material'][path]['status'],'proposed')
        self.assertEqual(state['field_status']['material'][path]['source'],'model_proposal')
        selected=self.service.choose_material({'session_id':state['id'],'material_turn_index':0,'option_index':0})
        self.assertEqual(selected['material_draft']['constitutive_parameters'][0]['unit'],'MPa')
        self.assertEqual(selected['field_status']['material'][path]['status'],'selected')
        self.assertEqual(selected['field_status']['material'][path]['source'],'user_selection')
        self.assertIsNone(selected['material_card'])

    def test_filled_proposals_can_be_recommended_and_modified_before_decision(self):
        raw=self.material_recommendation()['response']
        raw['card']['constitutive_parameters']['youngs_modulus'][0].update(value=100,unit='GPa')
        status=agent.field_provenance(raw)
        form=self.catalog.lookup(self.elastic)['formulation']
        reply,assessment,_,_=agent.evaluate(raw,form,self.mesh['summary'],field_status=status)
        self.assertEqual(reply['question_type'],'recommendation')
        candidate=assessment['ambiguities'][0]['options'][0]
        changed=agent.apply_candidate(assessment,candidate,status)
        self.assertEqual(changed['card']['constitutive_parameters']['youngs_modulus'][0]['value'],210)

    def test_user_input_requires_real_text_evidence_and_is_protected(self):
        raw=self.material_recommendation()['response']
        raw['card']['constitutive_parameters']['youngs_modulus'][0].update(value=205,unit='GPa')
        raw['user_inputs']=[{'parameter':'youngs_modulus','binding':0,'fields':['value','unit'],'quote':'E=205 GPa'}]
        with self.assertRaisesRegex(ValueError,'verbatim'):agent.field_provenance(raw,user_texts=['a steel sample'])
        status=agent.field_provenance(raw,user_texts=['Use E=205 GPa for the specimen.'])
        path='constitutive_parameters.youngs_modulus.0.value'
        self.assertEqual(status[path]['source'],'user_input');self.assertEqual(status[path]['status'],'specified')
        with self.assertRaisesRegex(ValueError,'user-decided'):
            agent.apply_candidate(raw,raw['ambiguities'][0]['options'][0],status)
        changed=deepcopy(raw);changed['card']['constitutive_parameters']['youngs_modulus'][0]['value']=210
        with self.assertRaisesRegex(ValueError,'Preserve the user-decided'):
            agent.field_provenance(changed,status,user_texts=['Use E=205 GPa for the specimen.'])

    def test_current_user_message_can_explicitly_revise_a_prior_decision(self):
        raw=self.material_proposal()['response']
        initial='Use E=210 GPa.'
        raw['user_inputs']=[{'parameter':'youngs_modulus','binding':0,'fields':['value','unit'],'quote':'E=210 GPa'}]
        status=agent.field_provenance(raw,user_texts=[initial])
        revised=deepcopy(raw);revised['card']['constitutive_parameters']['youngs_modulus'][0]['value']=205
        revised['user_inputs'][0]['quote']='E=205 GPa'
        latest='Change the modulus to E=205 GPa.'
        after=agent.field_provenance(revised,status,[initial,latest],latest)
        self.assertEqual(after['constitutive_parameters.youngs_modulus.0.value']['value'],205)

    def test_explicit_input_scope_and_null_evidence_are_validated(self):
        raw=self.material_question()['response']
        raw['user_inputs']=[{'parameter':'youngs_modulus','binding':0,'fields':['value'],'quote':'E=210 GPa'}]
        status=agent.field_provenance(raw,user_texts=['E=210 GPa'])
        self.assertEqual(status['constitutive_parameters.youngs_modulus.0.value']['status'],'unresolved')
        self.assertEqual(agent.verified_user_inputs(raw,status),[])
        Reply=agent.response_model(self.catalog.lookup(self.elastic)['formulation'],self.mesh['summary'])
        raw['user_inputs'][0]['parameter']='unapproved_parameter'
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps({'response':raw}))

    def test_unit_only_change_cannot_reinterpret_an_existing_numeric_value(self):
        raw=self.material_proposal()['response']
        candidate={'updates':[{'parameter':'youngs_modulus','binding':0,'regions':None,'value':None,'unit':'MPa'}]}
        with self.assertRaisesRegex(ValueError,'together'):agent.apply_candidate(raw,candidate)

    def test_explicit_edit_can_change_selected_values_without_an_api_call(self):
        self.material_answer=self.material_recommendation();state=self.start_materials()
        selected=self.service.choose_material({'session_id':state['id'],'material_turn_index':0,'option_index':0})
        calls=self.client.chat.completions.create.call_count
        edited=self.service.update_materials({'session_id':state['id'],'material_turn_index':1,
            'input':{'parameter':'youngs_modulus','binding':0,'value':205,'unit':'GPa'}})
        self.assertEqual(self.client.chat.completions.create.call_count,calls)
        path='constitutive_parameters.youngs_modulus.0.value'
        self.assertEqual(edited['field_status']['material'][path]['source'],'user_input')
        self.assertEqual(edited['field_status']['material'][path]['status'],'specified')
        self.assertEqual(edited['material_draft']['constitutive_parameters'][0]['value'],205)
        self.assertIsNone(edited['material_card'])
        old=selected['material_turns'][-1]['assessment']
        self.assertEqual(old['card']['constitutive_parameters']['youngs_modulus'][0]['value'],210)
        for item in ({'parameter':'bad_name','binding':0,'value':1,'unit':''},
            {'parameter':'youngs_modulus','binding':9,'value':1,'unit':''},
            {'parameter':'youngs_modulus','binding':0,'value':1,'unit':'','approved':True}):
            with self.assertRaises(SelectionError):self.service.update_materials({'session_id':state['id'],'material_turn_index':2,'input':item})
        with self.assertRaises(SelectionError):self.service.update_materials({'session_id':state['id'],'material_turn_index':1,
            'input':{'parameter':'youngs_modulus','binding':0,'value':1,'unit':''}})

    def test_approval_and_reload_keep_provenance_outside_the_card(self):
        self.material_answer=self.material_recommendation();state=self.start_materials()
        chosen=self.service.choose_material({'session_id':state['id'],'material_turn_index':0,'option_index':0})
        approved=self.service.confirm_materials({'session_id':state['id'],'material_turn_index':1})
        for record in approved['field_status']['material'].values():self.assertEqual(record['status'],'approved')
        self.assertEqual(set(approved['material_card']),{'constitutive_parameters'})
        for row in approved['material_card']['constitutive_parameters']:
            self.assertEqual(set(row),{'name','regions','value','unit'})
        folder=self.service.folder;self.service.close();self.service=ProblemSelectionService(folder,self.library,self.host)
        self.assertEqual(self.service.load(state['id'])['field_status'],approved['field_status'])
        self.assertEqual(chosen['field_status']['material']['constitutive_parameters.youngs_modulus.0.value']['status'],'selected')

    def test_user_evidence_is_reflected_in_service_and_context(self):
        self.material_answer=self.material_proposal()
        self.material_answer['response']['user_inputs']=[{
            'parameter':'youngs_modulus','binding':0,'fields':['value','unit'],'quote':'E=210 GPa'}]
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'A tensile test using E=210 GPa.'})
        state=self.service.confirm({'session_id':state['id'],'turn_index':0})
        state=self.service.confirm_spaces({'session_id':state['id'],'functionspace_turn_index':0})
        path='constitutive_parameters.youngs_modulus.0.value'
        self.assertEqual(state['field_status']['material'][path]['status'],'specified')
        messages,_=agent.messages(state['initial_request'],state['confirmed_selection'],state['formulation'],
            self.mesh['summary'],[],state['material_turns'],'Explain the assumptions.')
        self.assertIn('[User-decided material fields]',messages[-2]['content'])
        self.assertIn(path,messages[-2]['content'])

    def test_provenance_is_server_owned_for_all_stage_approvals(self):
        state=self.start_source_boundaries()
        for stage in ('selection','formulation','function_space','material'):
            self.assertTrue(state['field_status'][stage])
            self.assertTrue(all(r['status']=='approved' for r in state['field_status'][stage].values()))
        self.assertNotIn('field_status',state['functionspace_card'])
        state=self.service.confirm_boundary_parameter_selection({'session_id':state['id'],'boundary_parameter_turn_index':0})
        state=self.service.confirm_boundary_values({'session_id':state['id'],'boundary_value_turn_index':0})
        state=self.service.choose_solver({'session_id':state['id'],'solver_turn_index':0,'recommendation_index':0})
        self.assertTrue(all(r['status']=='selected' for r in state['field_status']['solver'].values() if r['value'] is not None))
        state=self.service.confirm_solver({'session_id':state['id'],'solver_turn_index':1})
        self.assertTrue(all(r['status']=='approved' for r in state['field_status']['solver'].values()))

    def test_old_nonnull_values_are_not_implicitly_user_decisions(self):
        state=self.start_materials()
        legacy=deepcopy(state);legacy.pop('field_status',None)
        for turn in legacy['material_turns']:turn.pop('field_status',None)
        meta=sync(legacy)
        regions=meta['material']['constitutive_parameters.youngs_modulus.0.regions']
        self.assertEqual(regions['status'],'proposed')
        self.assertFalse(decided(meta['material'],'constitutive_parameters.youngs_modulus.0.regions',regions['value']))
        status=reconcile({'zero':0,'dimensionless':'','scalar':[],'unknown':None})
        self.assertEqual(status['zero']['status'],'proposed');self.assertEqual(status['unknown']['status'],'unresolved')

    def test_reopening_a_stage_does_not_report_its_fields_as_still_approved(self):
        state=self.start_source_boundaries()
        state['material_card']=None
        reopened=sync(state)
        self.assertFalse(any(r['status']=='approved' for r in reopened['material'].values()))

    def test_legacy_backend_selection_can_be_recovered_without_rewriting_turns(self):
        self.material_answer=self.material_recommendation();state=self.start_materials()
        selected=self.service.choose_material({'session_id':state['id'],'material_turn_index':0,'option_index':0})
        legacy=deepcopy(selected);legacy.pop('field_status',None)
        for turn in legacy['material_turns']:turn.pop('field_status',None)
        before=deepcopy(legacy['material_turns'])
        recovered=sync(legacy)
        self.assertEqual(recovered['material']['constitutive_parameters.youngs_modulus.0.value']['status'],'selected')
        self.assertEqual(legacy['material_turns'],before)

    def test_model_cannot_supply_approval_flags_and_zero_is_valid_explicit_input(self):
        Reply=agent.response_model(self.catalog.lookup(self.elastic)['formulation'],self.mesh['summary'])
        raw=self.material_proposal();raw['response']['approved']=True
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(raw))
        self.material_answer=self.material_proposal();state=self.start_materials()
        edited=self.service.update_materials({'session_id':state['id'],'material_turn_index':0,
            'input':{'parameter':'poissons_ratio','binding':0,'value':0,'unit':''}})
        fields=edited['field_status']['material']
        self.assertEqual(fields['constitutive_parameters.poissons_ratio.0.value']['value'],0)
        self.assertEqual(fields['constitutive_parameters.poissons_ratio.0.unit']['value'],'')
        self.assertEqual(fields['constitutive_parameters.poissons_ratio.0.value']['status'],'specified')

    def test_editing_display_units_does_not_apply_length_conversion_twice(self):
        self.material_answer=self.material_proposal()
        self.material_answer['response']['card']['constitutive_parameters']['youngs_modulus'][0].update(value=210000000000,unit='N/m²')
        state=self.start_materials()
        row=state['material_draft']['constitutive_parameters'][0]
        self.assertEqual(row['value'],210000);self.assertEqual(row['unit'],'N/mm²')
        edited=self.service.update_materials({'session_id':state['id'],'material_turn_index':0,
            'input':{'parameter':'youngs_modulus','binding':0,'value':row['value'],'unit':row['unit']}})
        approved=self.service.confirm_materials({'session_id':state['id'],'material_turn_index':1})
        self.assertEqual(approved['material_card']['constitutive_parameters'][0]['value'],210000)
        self.assertEqual(edited['field_status']['material']['constitutive_parameters.youngs_modulus.0.unit']['status'],'specified')
