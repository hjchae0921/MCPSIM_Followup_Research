"""The public API groups recommendations structurally, without label heuristics."""
from copy import deepcopy
import json

from common.provenance import mark
from material_agent import agent
from tests.fixtures import AuthoringFixture


class MaterialSetSchemaTests(AuthoringFixture):
    def material_case(self):
        definitions=[('youngs_modulus','MPa'),('poissons_ratio',''),('thermal_expansion','1/K'),('thermal_conductivity','W/(mm K)')]
        names=[name for name,_ in definitions]+['reference_temperature']
        form={'constitutive_parameters':[{'name':name,'symbol':name} for name in names]}
        card={'constitutive_parameters':{name:[{'regions':['volume_1'],'value':None,'unit':unit}] for name,unit in definitions}}
        card['constitutive_parameters']['reference_temperature']=[{'regions':['volume_1'],'value':None,'unit':'K'}]
        options=[{'label':label,'description':'One consistent material and condition assumption.',
            'values':{**{name:{'value':value,'unit':unit} for (name,unit),value in zip(definitions,values)},'reference_temperature':None}}
            for label,values in [('Material A',[210000,0.3,1.2e-5,0.045]),('Material B',[69000,0.33,2.3e-5,0.167])]]
        public={'card':card,'user_inputs':[],
            'material_sets':{'volume_1':{'regions':['volume_1'],
                'explanation':'Choose a material-property set for the specimen.','options':options}},
            'ambiguities':[{'parameter':'reference_temperature','binding':0,'fields':['value'],
                'explanation':'Specify the stress-free reference temperature.','options':None}]}
        return form,public

    def compile(self, public, form, summary=None):
        return agent.to_assessment(public,form,summary or self.mesh['summary'])[0]

    def test_each_option_contains_all_four_properties_and_selection_is_atomic(self):
        form,public=self.material_case();raw=self.compile(public,form)
        reply,raw,_,_=agent.evaluate(raw,form,self.mesh['summary'])
        self.assertEqual(len(reply['options']),2)
        self.assertTrue(all(len(option['values'])==4 for option in reply['options']))
        for option in raw['ambiguities'][0]['options']:
            updated=agent.apply_candidate(raw,option)
            status=agent.selection_status(updated,option)
            after,_,_,_=agent.evaluate(updated,form,self.mesh['summary'],allow_generic=True,field_status=status)
            self.assertEqual(after['targets'],['constitutive_parameters.reference_temperature.0.value'])
            self.assertEqual(after['options'],[])

    def test_per_property_numerical_choices_are_not_a_valid_public_response(self):
        form,public=self.material_case()
        public['material_sets']['volume_1']=None
        public['ambiguities'].append(self.material_recommendation()['response']['ambiguities'][0])
        with self.assertRaises(ValueError):self.compile(public,form)
        public['ambiguities'].pop()
        public['material_sets']['volume_1']=[self.material_case()[1]['material_sets']['volume_1']]*4
        with self.assertRaises(ValueError):self.compile(public,form)

    def test_incomplete_candidates_cannot_silently_reintroduce_sequential_choices(self):
        form,public=self.material_case()
        for name in ('poissons_ratio','thermal_expansion','thermal_conductivity'):
            public['material_sets']['volume_1']['options'][0]['values'][name]=None
        with self.assertRaisesRegex(ValueError,'complete property set'):self.compile(public,form)

    def test_same_region_cannot_be_split_into_multiple_recommendation_groups(self):
        form,public=self.material_case();summary=deepcopy(self.mesh['summary'])
        summary['volume_groups'].append({'name':'Other','dim':3,'tags':[7]})
        public['material_sets']['volume_2']=deepcopy(public['material_sets']['volume_1'])
        public['material_sets']['volume_2']['regions']=['volume_1','volume_2']
        with self.assertRaisesRegex(ValueError,'one material_sets entry'):self.compile(public,form,summary)

    def test_bindings_are_selected_from_regions_instead_of_model_supplied_indices(self):
        form,public=self.material_case();summary=deepcopy(self.mesh['summary'])
        summary['volume_groups'].append({'name':'Other','dim':3,'tags':[7]})
        public['material_sets']['volume_2']=None
        for name,rows in public['card']['constitutive_parameters'].items():
            if name!='reference_temperature':rows.insert(0,{**deepcopy(rows[0]),'regions':['volume_2']})
        raw=self.compile(public,form,summary)
        self.assertTrue(all(patch['binding']==1 for patch in raw['ambiguities'][0]['options'][0]['updates']))

    def test_shared_material_regions_can_use_one_set(self):
        form,public=self.material_case();summary=deepcopy(self.mesh['summary'])
        summary['volume_groups'].append({'name':'Other','dim':3,'tags':[7]})
        public['material_sets']['volume_2']=None
        public['material_sets']['volume_1']['regions']=['volume_1','volume_2']
        for name,rows in public['card']['constitutive_parameters'].items():
            if name!='reference_temperature':rows.append({**deepcopy(rows[0]),'regions':['volume_2']})
        raw=self.compile(public,form,summary)
        self.assertEqual(len(raw['ambiguities'][0]['members']),8)
        self.assertEqual(len(raw['ambiguities'][0]['options'][0]['updates']),8)

    def test_duplicate_clarification_is_retained_as_context_for_the_single_set(self):
        form,public=self.material_case()
        public['ambiguities'].append({'parameter':'youngs_modulus','binding':0,'fields':['value'],
            'explanation':'Pick the material again for the modulus.','options':None})
        raw=self.compile(public,form)
        self.assertEqual(len(raw['ambiguities']),2)
        self.assertIn('Pick the material again',raw['ambiguities'][0]['explanation'])
        option=raw['ambiguities'][0]['options'][0]
        updated=agent.apply_candidate(raw,option)
        fields=agent.selection_status(updated,option)
        after,_,_,_=agent.evaluate(updated,form,self.mesh['summary'],allow_generic=True,field_status=fields)
        self.assertEqual(after['targets'],['constitutive_parameters.reference_temperature.0.value'])

    def test_explicit_user_values_are_retained_when_other_properties_are_selected(self):
        form,public=self.material_case();public['card']['constitutive_parameters']['youngs_modulus'][0]['value']=205000
        for option in public['material_sets']['volume_1']['options']:option['values']['youngs_modulus']=None
        raw=self.compile(public,form)
        status=mark({}, {'constitutive_parameters.youngs_modulus.0.value':205000},'user_input','specified')
        reply,raw,_,_=agent.evaluate(raw,form,self.mesh['summary'],field_status=status)
        self.assertFalse(any('youngs_modulus' in target for target in reply['targets']))
        updated=agent.apply_candidate(raw,raw['ambiguities'][0]['options'][0],status)
        self.assertEqual(updated['card']['constitutive_parameters']['youngs_modulus'][0]['value'],205000)

    def test_property_set_proposal_survives_selection_and_next_prompt(self):
        form,public=self.material_case();path=self.library/'linear_elasticity_isotropic_formulation.json'
        record=json.loads(path.read_text());record['formulation']['constitutive_parameters']=form['constitutive_parameters'];path.write_text(json.dumps(record))
        self.material_answer={'response':public};state=self.start_materials();calls=self.client.chat.completions.create.call_count
        selected=self.service.choose_material({'session_id':state['id'],'material_turn_index':0,'option_index':0})
        self.assertEqual(self.client.chat.completions.create.call_count,calls)
        self.assertEqual(selected['material_turns'][-1]['response']['targets'],['constitutive_parameters.reference_temperature.0.value'])
        self.assertEqual(selected['material_turns'][-1]['proposal'],state['material_turns'][-1]['proposal'])
        messages,_=agent.messages(state['initial_request'],state['confirmed_selection'],state['formulation'],
            self.mesh['summary'],[],selected['material_turns'],'Explain the remaining question.')
        last=json.loads(next(message['content'] for message in reversed(messages) if message['role']=='assistant'))['response']
        agent.response_model(state['formulation'],self.mesh['summary']).model_validate_json(json.dumps({'response':last}))
        self.assertEqual(last['card']['constitutive_parameters']['youngs_modulus'][0]['value'],210000)

    def test_independent_questions_on_one_region_are_presented_together(self):
        form,public=self.material_case();public['material_sets']['volume_1']=None
        public['ambiguities']=[{'parameter':name,'binding':0,'fields':['value','unit'],
            'explanation':'Provide '+name+' for the specimen.','options':None} for name in ('youngs_modulus','poissons_ratio')]
        raw=self.compile(public,form)
        self.assertEqual(len(raw['ambiguities']),1)
        reply,_,_,_=agent.evaluate(raw,form,self.mesh['summary'])
        self.assertEqual(reply['question_type'],'input')
        self.assertTrue(any('youngs_modulus' in path for path in reply['targets']))
        self.assertTrue(any('poissons_ratio' in path for path in reply['targets']))

    def test_a_decided_first_property_does_not_hide_the_rest_of_the_set(self):
        form,public=self.material_case();raw=self.compile(public,form)
        raw['card']['constitutive_parameters']['youngs_modulus'][0]['value']=210000
        fields=mark({}, {'constitutive_parameters.youngs_modulus.0.value':210000,
            'constitutive_parameters.youngs_modulus.0.unit':'MPa'},'user_input','specified')
        reply,_,_,_=agent.evaluate(raw,form,self.mesh['summary'],allow_generic=True,field_status=fields)
        self.assertEqual(len(reply['options']),1)
        self.assertTrue(any('poissons_ratio' in path for path in reply['targets']))
        self.assertTrue(any('thermal_conductivity' in path for path in reply['targets']))
