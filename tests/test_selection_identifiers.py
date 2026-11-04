"""Identifier-only classification context and post-judgment library matching."""
from copy import deepcopy
import json
import shutil
from unittest.mock import patch

from tests.fixtures import AuthoringFixture, response
from web.app import ROOT
from common.coupling import COUPLING, normalized_coupling


class SelectionIdentifierTests(AuthoringFixture):
    def add_thermoelasticity(self):
        record=self.thermoelastic_fixture(fully_coupled=True)
        (self.library/'thermoelasticity_isotropic_formulation.json').write_text(json.dumps(record))
        return {key:record[key] for key in ('problem','materials')}

    def catalog_input(self):
        request=self.selection_request()
        marker='[Known problem and constitutive-model identifiers]'
        return json.loads(request['messages'][1]['content'].split(marker,1)[1].strip()),request

    def test_classifier_receives_identifiers_without_existing_specifications(self):
        self.add_thermoelasticity()
        self.start()
        catalog,request=self.catalog_input()
        self.assertEqual(set(catalog),{'types','models'})
        expected=self.catalog.choices()
        self.assertEqual(catalog,{key:expected[key] for key in ('types','models')})
        self.assertTrue(all(isinstance(value,str) for values in catalog.values() for value in values))
        self.assertNotIn('selections',catalog)
        schema=request['response_format']['json_schema']['schema']
        self.assertEqual(schema['$defs']['PartialCoupling']['properties']['type']['anyOf'][0]['enum'],list(COUPLING))
        self.assertNotIn('enum',schema['$defs']['PartialProblem']['properties']['type']['anyOf'][0])
        self.assertEqual(normalized_coupling('multiphysics_one_way'),'multi_physics_one_way')

    def test_missing_one_way_combination_is_preserved_and_routed_after_judgment(self):
        existing=self.add_thermoelasticity()
        self.assertEqual(existing['problem']['coupling']['type'],'multi_physics_fully_coupled')
        requested=deepcopy(existing)
        requested['problem']['time_dependence']='independent'
        requested['problem']['coupling']={'type':'multi_physics_one_way',
            'dependencies':[{'from':'temperature','to':'displacement'}]}
        before={p.name:p.read_bytes() for p in self.library.glob('*.json')}
        events=[]
        def model_response(**request):
            events.append('model')
            return response(self.proposal(requested))
        lookup=self.service.catalog.lookup
        def checked_lookup(spec):
            events.append('lookup')
            self.assertEqual(spec,requested)
            return lookup(spec)
        with patch.object(self.client.chat.completions,'create',side_effect=model_response) as call:
            with patch.object(self.service.catalog,'lookup',side_effect=checked_lookup):
                state=self.service.chat({'mesh_id':self.mesh['id'],
                    'message':'Compute steady thermal deformation. Neglect temperature changes caused by deformation.'})
        self.assertEqual(call.call_count,2)
        self.assertEqual(events,['model','model','lookup'])
        reply=state['turns'][0]['response']
        self.assertEqual(reply['kind'],'registration_request')
        self.assertEqual(reply['spec'],requested)
        self.assertIn('one-way multiphysics coupling',reply['explanation'])
        self.assertIsNone(state['confirmed_selection'])
        self.assertIsNone(state['generation'])
        self.assertEqual({p.name:p.read_bytes() for p in self.library.glob('*.json')},before)

    def test_legacy_coupling_spelling_does_not_create_a_false_missing_match(self):
        existing=self.add_thermoelasticity()
        alias=deepcopy(existing)
        alias['problem']['coupling']['type']='multiphysics_fully_coupled'
        self.client.chat.completions.create.return_value=response(self.proposal(alias))
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Use the approved fully coupled thermoelastic model.'})
        reply=state['turns'][0]['response']
        self.assertEqual(reply['kind'],'proposal')
        self.assertEqual(reply['spec'],existing)
        self.assertEqual(self.client.chat.completions.create.call_count,2)
