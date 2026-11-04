"""Regression cases for provider-facing contracts without paid API requests."""
from copy import deepcopy
import json

from tests import test_material_sets as material_tests
from tests.fixtures import AuthoringFixture
from problem_selection_agent.spec import reply_model
from problem_selection_agent.questions import fixed_values, wire_assessment, internal_assessment, select_question
from material_agent import agent as materials
from boundary_condition_agent import parameter_selection as boundary
from common.contracts import generation_schema


class ProviderContractsTests(AuthoringFixture):
    def test_fixed_targets_have_closed_slots_and_only_free_targets_expose_options(self):
        Reply=reply_model([],[],3,wire=True);schema=Reply.model_json_schema()
        slots=schema['$defs']['SelectionUncertainties']
        self.assertFalse(slots['additionalProperties'])
        self.assertEqual(set(slots['required']),set(slots['properties']))
        for target in fixed_values():
            payload={'response':wire_assessment(self.assessment_question(target)['response'])}
            parsed=Reply.model_validate_json(json.dumps(payload)).model_dump(mode='json',by_alias=True)['response']
            self.assertEqual(select_question(internal_assessment(parsed))['fixed_target'],target)
            ref=slots['properties'][target]['anyOf'][0]['$ref'].split('/')[-1]
            self.assertEqual(set(schema['$defs'][ref]['properties']),{'explanation'})
            for value in (None,[{'label':'unapproved','description':'Never display this.'}]):
                invalid=deepcopy(payload);invalid['response']['ambiguities'][target]['options']=value
                with self.subTest(target=target,value=value),self.assertRaises(ValueError):
                    Reply.model_validate_json(json.dumps(invalid))
        payload=self.assessment_question('problem.type')['response']
        payload['ambiguities'][0]['options']=[{'label':'linear_elasticity','description':'Small strain.'},
            {'label':'hyperelasticity','description':'Finite strain.'}]
        parsed=Reply.model_validate_json(json.dumps({'response':wire_assessment(payload)})).model_dump(mode='json',by_alias=True)['response']
        self.assertEqual(select_question(internal_assessment(parsed))['options'],payload['ambiguities'][0]['options'])
        parsed['ambiguities']['unapproved.target']={'explanation':'No outside fields.'}
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps({'response':parsed}))

    def test_live_service_schema_uses_target_slots_and_preserves_internal_cards(self):
        state=self.start();request=self.client.chat.completions.create.call_args_list[0].kwargs
        self.assertIn('SelectionUncertainties',request['response_format']['json_schema']['schema']['$defs'])
        self.assertEqual(state['turns'][0]['assessment']['ambiguities'],[])
        self.assertEqual(state['turns'][0]['response']['spec'],self.elastic)
        self.assertIsNone(state['confirmed_selection'])

    def test_material_properties_are_derived_from_candidate_values_without_a_second_name_list(self):
        form,public=material_tests.MaterialSetSchemaTests.material_case(self)
        for candidate in public['material_sets']['volume_1']['options']:
            candidate['values']['reference_temperature']={'value':293.15,'unit':'K'}
        raw,proposal=materials.to_assessment(public,form,self.mesh['summary'])
        self.assertEqual({m['parameter'] for m in raw['ambiguities'][0]['members']},
            {p['name'] for p in form['constitutive_parameters']})
        self.assertEqual(len(raw['ambiguities'][0]['options'][0]['updates']),5)
        self.assertNotIn('parameters',proposal['material_sets']['volume_1'])
        invalid=deepcopy(public)
        invalid['material_sets']['volume_1']['options'][0]['values']['new_material_property']={'value':1,'unit':''}
        with self.assertRaises(ValueError):materials.to_assessment(invalid,form,self.mesh['summary'])
        invalid=deepcopy(public);invalid['card']['constitutive_parameters']['traction']=[{'regions':None,'value':None,'unit':None}]
        with self.assertRaises(ValueError):materials.to_assessment(invalid,form,self.mesh['summary'])
        invalid=deepcopy(public);invalid['material_sets']['volume_1']['parameters']=['invented_subset']
        with self.assertRaises(ValueError):materials.to_assessment(invalid,form,self.mesh['summary'])

    def test_legacy_material_proposal_is_replayed_without_obsolete_name_lists(self):
        form,public=material_tests.MaterialSetSchemaTests.material_case(self)
        raw,proposal=materials.to_assessment(public,form,self.mesh['summary'])
        old=deepcopy(proposal)
        old['material_sets']['volume_1']['parameters']=[p['name'] for p in form['constitutive_parameters']]
        turn={'assessment':raw,'proposal':old,'message':'Old material proposal.'}
        before=deepcopy(turn)
        from material_agent.recommendations import prompt_reply
        replay=prompt_reply(turn,form,self.mesh['summary'])
        materials.response_model(form,self.mesh['summary']).model_validate_json(json.dumps({'response':replay}))
        self.assertNotIn('parameters',replay['material_sets']['volume_1'])
        self.assertEqual(turn,before)

    def test_boundary_schema_uses_one_object_per_item_and_server_checks_usage_semantics(self):
        form=self.catalog.lookup(self.elastic)['formulation'];summary=self.mesh['summary']
        unknowns=[{'name':'displacement','quantity':'displacement','shape':[3]}]
        Reply=boundary.response_model(form,summary,unknowns);schema=Reply.model_json_schema()
        assessment=schema['$defs']['BoundarySourceParameterAssessment']['properties']
        for scope in boundary.SCOPES:self.assertIn('$ref',assessment[scope]['items'])
        reply={'explanation':'Review the unresolved application region.',
            'assessment':{scope:[{'name':p['name'],'requirement':'not_needed','regions':[],'reason':'Unused.'} for p in form[scope]]
                for scope in ('boundary_parameters','source_parameters')},'recommendations':[]}
        reply['assessment']['dirichlet_conditions']=[{'field':'displacement','requirement':'needed','regions':None,'components':[0],'reason':'Support region undecided.'}]
        Reply.model_validate_json(json.dumps(reply))
        self.assertEqual(boundary.check_reply(reply,form,summary,unknowns)['question_targets'],['dirichlet_conditions.displacement.regions'])
        for mutation in ('unused_with_region','foreign_name','missing_parameter'):
            invalid=deepcopy(reply)
            if mutation=='unused_with_region':invalid['assessment']['boundary_parameters'][0]['regions']=[{'name':'Grip_Right','dim':2,'tags':[3]}]
            elif mutation=='foreign_name':invalid['assessment']['source_parameters'][0]['name']='not_in_formulation'
            else:invalid['assessment']['boundary_parameters'].pop()
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(invalid))

    def test_generation_schema_removes_array_bounds_but_preserves_closed_fields_and_enums(self):
        Reply=reply_model([],[],3,wire=True);full=Reply.model_json_schema();before=deepcopy(full)
        projected=generation_schema(full)
        def check(original,value):
            if isinstance(original,dict):
                expected=set(original)-({'minItems','maxItems'} if original.get('type')=='array' else set())
                self.assertEqual(set(value),expected)
                for key,child in value.items():check(original[key],child)
            elif isinstance(original,list):
                self.assertEqual(len(original),len(value))
                for a,b in zip(original,value):check(a,b)
            else:self.assertEqual(original,value)
        check(full,projected);self.assertEqual(full,before)
        payload=wire_assessment(self.assessment_question('problem.type')['response'])
        payload['ambiguities']['problem.type']['options']=[{'label':'One candidate','description':'Insufficient alternatives.'}]
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps({'response':payload}))

    def test_boundary_provider_keys_are_fixed_and_decoded_without_changing_the_card(self):
        form=self.catalog.lookup(self.elastic)['formulation'];summary=self.mesh['summary']
        unknowns=[{'name':'displacement','quantity':'displacement','shape':[3]}]
        Reply=boundary.response_model(form,summary,unknowns,wire=True)
        raw={'explanation':'Resolve the support region.',
            'assessment':{scope:[{'name':p['name'],'requirement':'not_needed','regions':[],'reason':'Unused.'} for p in form[scope]]
                for scope in ('boundary_parameters','source_parameters')},'recommendations':[]}
        raw['assessment']['dirichlet_conditions']=[{'field':'displacement','requirement':'needed','regions':None,'components':[0],'reason':'The region is undecided.'}]
        wire=boundary.wire_reply(raw)
        self.assertEqual(boundary.wire_reply(wire),wire)
        parsed=Reply.model_validate_json(json.dumps(wire)).model_dump(mode='json',by_alias=True)
        self.assertEqual(boundary.internal_reply(parsed),raw)
        self.assertEqual(boundary.check_reply(boundary.internal_reply(parsed),form,summary,unknowns)['question_targets'],['dirichlet_conditions.displacement.regions'])
        for scope in ('boundary_parameters','source_parameters'):
            self.assertEqual(set(wire['assessment'][scope]),{p['name'] for p in form[scope]})
            extra=deepcopy(wire);extra['assessment'][scope]['foreign_parameter']={'requirement':'not_needed','regions':[],'reason':'No.'}
            with self.subTest(scope=scope),self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(extra))
            missing=deepcopy(wire);missing['assessment'][scope].pop(next(iter(missing['assessment'][scope])))
            with self.subTest(scope=scope),self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(missing))
        invalid=deepcopy(wire);invalid['assessment']['dirichlet_conditions']['foreign_field']=[]
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(invalid))
        inactive=deepcopy(wire)
        for item in inactive['assessment']['boundary_parameters'].values():item['regions']=None
        parsed=Reply.model_validate_json(json.dumps(inactive)).model_dump(mode='json',by_alias=True)
        canonical=boundary.check_reply(boundary.internal_reply(parsed),form,summary,unknowns)
        self.assertTrue(all(item['regions']==[] for item in canonical['assessment']['boundary_parameters']))
        # A real region on an unused condition is still a contradiction, never erased.
        item=next(iter(inactive['assessment']['boundary_parameters'].values()))
        item['regions']=[{'name':'Grip_Right','dim':2,'tags':[3]}]
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(inactive))

    def test_scalar_component_zero_normalizes_to_the_whole_field_without_changing_vectors(self):
        form={'boundary_parameters':[],'source_parameters':[]};summary=self.mesh['summary']
        unknowns=[{'name':'temperature','quantity':'temperature','shape':[]},
            {'name':'displacement','quantity':'displacement','shape':[3]}]
        assessment={'boundary_parameters':[],'source_parameters':[],
            'dirichlet_conditions':[{'field':u['name'],'requirement':'needed','regions':[{'name':'Grip_Left','dim':2,'tags':[2]}],
                'components':[0],'reason':'Prescribed field.'} for u in unknowns]}
        before=deepcopy(assessment)
        checked=boundary.check_assessment(assessment,form,summary,unknowns)
        self.assertEqual(checked['dirichlet_conditions'][0]['components'],[])
        self.assertEqual(checked['dirichlet_conditions'][1]['components'],[0])
        self.assertEqual(assessment,before)
        for components in ([1],[0,0]):
            invalid=deepcopy(assessment);invalid['dirichlet_conditions'][0]['components']=components
            with self.subTest(components=components),self.assertRaises(ValueError):
                boundary.check_assessment(invalid,form,summary,unknowns)
