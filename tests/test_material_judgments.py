"""Material decisions, partial cards and candidate application without paid API calls."""
from copy import deepcopy
import json
from pathlib import Path

from material_agent import agent
from material_agent.judgments import binding_at, missing_fields
from common.provenance import mark, material_fields, reconcile
from problem_selection_agent.service import SelectionError
from tests.fixtures import AuthoringFixture


class MaterialJudgmentTests(AuthoringFixture):
    def evaluate(self, payload=None, summary=None, allow_generic=False, field_status=None):
        return agent.evaluate((payload or self.material_proposal())['response'],
            self.catalog.lookup(self.elastic)['formulation'], summary or self.mesh['summary'], allow_generic,field_status)

    def test_complete_card_needs_no_questions_and_summary_uses_only_card(self):
        payload=self.material_proposal()
        payload['response']['ambiguities']=self.material_question()['response']['ambiguities']
        fields=material_fields(payload['response']['card']['constitutive_parameters'])
        status=mark(reconcile(fields),fields,'user_input','specified')
        reply,_,draft,_=self.evaluate(payload,field_status=status)
        self.assertEqual(reply['proposed_card'],draft)
        self.assertNotIn('question_type',reply)
        self.assertIn('youngs_modulus = 210.0 GPa on Specimen.',reply['explanation'])
        self.assertNotIn('explanation',draft)

    def test_null_is_unresolved_but_zero_and_empty_unit_are_known(self):
        payload=self.material_question()
        binding_at(payload['response'],'poissons_ratio',0)['value']=0
        reply,raw,draft,_=self.evaluate(payload)
        self.assertEqual(reply['targets'],['constitutive_parameters.youngs_modulus.0.value',
            'constitutive_parameters.youngs_modulus.0.unit'])
        self.assertEqual(draft['constitutive_parameters'][1]['value'],0)
        self.assertEqual(draft['constitutive_parameters'][1]['unit'],'')
        self.assertEqual(missing_fields(raw),{('youngs_modulus',0,'value'),('youngs_modulus',0,'unit')})

    def test_exact_parameter_names_real_volumes_and_binding_indices_are_enforced(self):
        cases=[]
        bad=self.material_proposal();bad['response']['card']['constitutive_parameters']['extra']=[];cases.append(bad)
        bad=self.material_proposal();del bad['response']['card']['constitutive_parameters']['poissons_ratio'];cases.append(bad)
        for regions in ([],['Specimen'],['volume_999'],['volume_1','volume_1']):
            bad=self.material_proposal();binding_at(bad['response'],'youngs_modulus',0)['regions']=regions;cases.append(bad)
        bad=self.material_question();bad['response']['ambiguities'][0]['binding']=4;cases.append(bad)
        for bad in cases:
            with self.subTest(payload=bad),self.assertRaises(ValueError):self.evaluate(bad)

    def test_heterogeneous_bindings_use_mesh_regions_and_reject_overlap(self):
        summary=deepcopy(self.mesh['summary'])
        summary['volume_groups'].append({'name':'Other','dim':3,'tags':[12]})
        payload=self.material_proposal()
        row=deepcopy(binding_at(payload['response'],'youngs_modulus',0));row.update(regions=['volume_2'],value=70)
        payload['response']['card']['constitutive_parameters']['youngs_modulus'].append(row)
        reply,_,_,_=self.evaluate(payload,summary)
        self.assertEqual(reply['proposed_card']['constitutive_parameters'][1]['regions'],[{'name':'Other','dim':3,'tags':[12]}])
        row['regions']=['volume_1']
        with self.assertRaises(ValueError):self.evaluate(payload,summary)

    def test_matrix_coefficients_are_rectangular_and_finite(self):
        form={'constitutive_parameters':[{'name':'stiffness','symbol':'C'}]}
        def assess(value):
            return {'card':{'constitutive_parameters':{'stiffness':[
                {'regions':['volume_1'],'value':value,'unit':'MPa'}]}},'ambiguities':[]}
        reply,_,_,_=agent.evaluate(assess([[1,0],[0,2]]),form,self.mesh['summary'])
        self.assertEqual(reply['proposed_card']['constitutive_parameters'][0]['value'],[[1,0],[0,2]])
        for value in ([[1,2],[3]],[],float('nan'),float('inf'),True):
            with self.subTest(value=value),self.assertRaises(ValueError):agent.evaluate(assess(value),form,self.mesh['summary'])

    def test_unexplained_missing_fields_require_model_repair(self):
        payload=self.material_question();payload['response']['ambiguities']=[]
        with self.assertRaisesRegex(ValueError,'Explain the unresolved material fields'):self.evaluate(payload)

    def test_candidates_cannot_overwrite_user_decided_fields_or_answer_another_question(self):
        cases=[]
        bad=self.material_recommendation();bad['response']['ambiguities'][0]['options'][0]['updates'][0]['regions']=['volume_999'];cases.append(bad)
        bad=self.material_recommendation();bad['response']['ambiguities'][0]['options'][0]['updates'][1]['unit']='MPa';cases.append(bad)
        bad=self.material_recommendation();bad['response']['ambiguities'][0]['options'][0]['updates'].pop(0);cases.append(bad)
        bad=self.material_recommendation();patch=bad['response']['ambiguities'][0]['options'][0]['updates'][0]
        patch.update(value=None,unit=None);cases.append(bad)
        for bad in cases:
            status=mark({}, {'constitutive_parameters.poissons_ratio.0.unit':''}, 'user_input', 'specified')
            with self.subTest(payload=bad),self.assertRaises(ValueError):self.evaluate(bad,field_status=status)

    def test_candidate_click_updates_without_api_call_but_still_requires_approval(self):
        self.material_answer=self.material_recommendation()
        state=self.start_materials();calls=self.client.chat.completions.create.call_count
        selected=self.service.choose_material({'session_id':state['id'],'material_turn_index':0,'option_index':0})
        self.assertEqual(self.client.chat.completions.create.call_count,calls)
        self.assertEqual(selected['stage'],'material_review');self.assertIsNone(selected['material_card'])
        self.assertEqual(selected['authoring_status']['status'],'ready_for_review')
        self.assertEqual(selected['material_draft'],self.material_card())
        self.assertEqual(selected['material_turns'][-1]['origin'],'recommendation_choice')
        self.assertEqual(state['material_turns'][0]['assessment']['card']['constitutive_parameters']['youngs_modulus'][0]['value'],None)
        for data in ({'material_turn_index':0,'option_index':0},{'material_turn_index':1,'option_index':0}):
            with self.assertRaises(SelectionError):self.service.choose_material({'session_id':state['id'],**data})
        approved=self.service.confirm_materials({'session_id':state['id'],'material_turn_index':1})
        self.assertEqual(approved['material_card'],self.material_card())

    def material_sets(self):
        definitions=[('youngs_modulus','MPa'),('poissons_ratio',''),('thermal_expansion','1/K'),
            ('thermal_conductivity','W/(mm K)')]
        form={'constitutive_parameters':[{'name':name,'symbol':name} for name,_ in definitions]}
        raw={'card':{'constitutive_parameters':{name:[{'regions':['volume_1'],'value':None,'unit':unit}]
            for name,unit in definitions}},'ambiguities':[]}
        options=[{'label':label,'description':'A consistent illustrative material-property set.',
            'updates':[{'parameter':name,'binding':0,'regions':None,'value':value,'unit':unit}
                for (name,unit),value in zip(definitions,values)]}
            for label,values in [('Material A',[210000,0.3,1.2e-5,0.045]),('Material B',[69000,0.33,2.3e-5,0.167])]]
        raw['ambiguities']=[{'parameter':name,'binding':0,'fields':['value'],
            'explanation':'Choose a material-property set for the specimen.',
            'options':options if i==0 else None} for i,(name,_) in enumerate(definitions)]
        return form,raw

    def test_material_set_question_lists_all_updated_properties_and_selects_them_together(self):
        form,raw=self.material_sets()
        reply,assessment,_,_=agent.evaluate(raw,form,self.mesh['summary'])
        names=list(raw['card']['constitutive_parameters'])
        self.assertEqual(reply['targets'],[f'constitutive_parameters.{name}.0.{key}' for name in names for key in ('value','unit')])
        self.assertEqual(len(reply['options']),2)
        self.assertTrue(all(len(option['values'])==4 for option in reply['options']))
        for option in assessment['ambiguities'][0]['options']:
            updated=agent.apply_candidate(assessment,option)
            fields=agent.selection_status(updated,option)
            result,_,_,_=agent.evaluate(updated,form,self.mesh['summary'],allow_generic=True,field_status=fields)
            self.assertIn('proposed_card',result)
            self.assertNotIn('question',result)
            self.assertFalse(missing_fields(updated))
        self.assertEqual(raw['card']['constitutive_parameters'][names[0]][0]['value'],None)

    def test_material_set_retains_user_values_and_only_targets_remaining_properties(self):
        form,raw=self.material_sets()
        binding_at(raw,'youngs_modulus',0)['value']=123456
        raw['ambiguities'].pop(0)
        _,template=self.material_sets()
        candidate=template['ambiguities'][0]['options'][0]
        candidate['updates'].pop(0)
        raw['ambiguities'][0]['options']=[candidate]
        fields=mark({}, {'constitutive_parameters.youngs_modulus.0.value':123456},'user_input','specified')
        reply,assessment,_,_=agent.evaluate(raw,form,self.mesh['summary'],field_status=fields)
        self.assertFalse(any('youngs_modulus' in path for path in reply['targets']))
        updated=agent.apply_candidate(assessment,candidate)
        fields=agent.selection_status(updated,candidate,fields)
        result,_,_,_=agent.evaluate(updated,form,self.mesh['summary'],allow_generic=True,field_status=fields)
        self.assertEqual(result['proposed_card']['constitutive_parameters'][0]['value'],123456)

    def test_material_set_leaves_unrelated_reference_inputs_for_a_separate_question(self):
        form,raw=self.material_sets()
        form['constitutive_parameters'].append({'name':'reference_temperature','symbol':'T0'})
        raw['card']['constitutive_parameters']['reference_temperature']=[{'regions':['volume_1'],'value':None,'unit':'K'}]
        raw['ambiguities'].append({'parameter':'reference_temperature','binding':0,'fields':['value'],
            'explanation':'What is the stress-free reference temperature?','options':None})
        reply,assessment,_,_=agent.evaluate(raw,form,self.mesh['summary'])
        self.assertFalse(any('reference_temperature' in path for path in reply['targets']))
        updated=agent.apply_candidate(assessment,assessment['ambiguities'][0]['options'][0])
        fields=agent.selection_status(updated,assessment['ambiguities'][0]['options'][0])
        result,_,_,_=agent.evaluate(updated,form,self.mesh['summary'],allow_generic=True,field_status=fields)
        self.assertEqual(result['targets'],['constitutive_parameters.reference_temperature.0.value'])
        self.assertEqual(result['question_type'],'input')

    def test_material_set_does_not_fill_another_volume(self):
        form,raw=self.material_sets()
        summary=deepcopy(self.mesh['summary'])
        summary['volume_groups'].append({'name':'Other','dim':3,'tags':[7]})
        for name,rows in raw['card']['constitutive_parameters'].items():
            rows.append({**deepcopy(rows[0]),'regions':['volume_2']})
            raw['ambiguities'].append({'parameter':name,'binding':1,'fields':['value'],
                'explanation':'Specify the properties on the other volume.','options':None})
        reply,assessment,_,_=agent.evaluate(raw,form,summary)
        self.assertTrue(all('.0.' in path for path in reply['targets']))
        updated=agent.apply_candidate(assessment,assessment['ambiguities'][0]['options'][0])
        for rows in updated['card']['constitutive_parameters'].values():
            self.assertIsNotNone(rows[0]['value']);self.assertIsNone(rows[1]['value'])
        fields=agent.selection_status(updated,assessment['ambiguities'][0]['options'][0])
        result,_,_,_=agent.evaluate(updated,form,summary,allow_generic=True,field_status=fields)
        self.assertEqual(result['targets'],['constitutive_parameters.youngs_modulus.1.value'])

    def test_partial_candidate_advances_to_only_remaining_missing_fields(self):
        self.material_answer=self.material_recommendation()
        self.material_answer['response']['ambiguities'][0]['options'][0]['updates'].pop()
        state=self.start_materials();calls=self.client.chat.completions.create.call_count
        selected=self.service.choose_material({'session_id':state['id'],'material_turn_index':0,'option_index':0})
        reply=selected['material_turns'][-1]['response']
        self.assertEqual(reply['targets'],['constitutive_parameters.poissons_ratio.0.value'])
        self.assertEqual(reply['question_type'],'input');self.assertEqual(reply['options'],[])
        self.assertIsNone(selected['material_card']);self.assertEqual(self.client.chat.completions.create.call_count,calls)

    def test_units_are_normalized_once_when_candidate_only_supplies_a_unit(self):
        payload=self.material_recommendation()
        row=binding_at(payload['response'],'youngs_modulus',0);row['value']=210000000000
        option=payload['response']['ambiguities'][0]['options'][0]
        option['updates'][0].update(value=None,unit='N/m²')
        fields=mark({}, {'constitutive_parameters.youngs_modulus.0.value':210000000000,
            'constitutive_parameters.poissons_ratio.0.unit':''},'user_input','specified')
        reply,raw,_,_=self.evaluate(payload,field_status=fields)
        self.assertEqual(reply['targets'],['constitutive_parameters.youngs_modulus.0.unit',
            'constitutive_parameters.poissons_ratio.0.value'])
        self.assertAlmostEqual(reply['options'][0]['values'][0]['value'],210000)
        updated=agent.apply_candidate(raw,option)
        fields=agent.selection_status(updated,option,fields)
        result,_,_,_=self.evaluate({'response':updated},field_status=fields)
        final=result['proposed_card']['constitutive_parameters'][0]
        self.assertEqual(final['unit'],'N/mm²');self.assertAlmostEqual(final['value'],210000)
        self.assertEqual(row['value'],210000000000)
        again,_,_,_=self.evaluate({'response':updated},field_status=fields)
        self.assertEqual(again,result)

    def test_empty_parameters_require_no_api_and_cannot_invent_volume_references(self):
        state=self.start_spaces()
        state.update(formulation={**state['formulation'],'constitutive_parameters':[]},material_selection=[])
        calls=self.client.chat.completions.create.call_count
        result=self.service.propose_materials(state)
        self.assertEqual(result['turn']['response']['proposed_card'],{'constitutive_parameters':[]})
        self.assertEqual(self.client.chat.completions.create.call_count,calls)
        Reply=agent.response_model({'constitutive_parameters':[]},self.mesh['summary'])
        Reply.model_validate_json(json.dumps({'response':{**agent.empty_assessment({'constitutive_parameters':[]}),
            'material_sets':{'volume_1':None}}}))
        summary={**self.mesh['summary'],'volume_groups':[]}
        with self.assertRaises(ValueError):self.evaluate(summary=summary)

    def test_legacy_card_history_is_replayed_in_new_shape_without_mutation(self):
        original={'message':'Use the specified properties.','response':{'explanation':'Legacy overview.',
            'proposed_card':self.material_card()}}
        before=deepcopy(original)
        raw=agent.provider_reply(original,self.catalog.lookup(self.elastic)['formulation'],self.mesh['summary'])
        self.assertEqual(self.evaluate({'response':raw})[0]['proposed_card'],self.material_card())
        self.assertEqual(original,before)
        msgs,_=agent.messages('Tensile test.',self.elastic,self.catalog.lookup(self.elastic)['formulation'],
            self.mesh['summary'],[],[original])
        self.assertNotIn('Legacy overview',json.dumps(msgs))

    def test_prompt_is_english_scoped_and_rules_are_short(self):
        root=Path(agent.__file__).parent
        for path in list(root.glob('*.py'))+list(root.glob('*.txt')):
            self.assertFalse(any('\uac00'<=c<='\ud7a3' for c in path.read_text()),path.name)
        prompt=(root/'material_prompt.txt').read_text()
        self.assertEqual(sum(line.startswith('- ') for line in prompt.split('RULES')[1].split('=== USER MESSAGE ===')[0].splitlines()),4)
        messages,_=agent.messages('Tensile test.',self.elastic,self.catalog.lookup(self.elastic)['formulation'],
            self.mesh['summary'],[{'name':'Specimen','dim':3,'tags':[1]}],[])
        text=messages[1]['content']
        self.assertIn('volume_1',text);self.assertNotIn('boundary_parameters',text)
        self.assertNotIn('source_parameters',text)
