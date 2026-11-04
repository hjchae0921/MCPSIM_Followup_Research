"""Library reuse is grounded in the request, with server-owned constraints and IDs."""
from copy import deepcopy
import json
from pathlib import Path
import shutil

from common.coupling import COUPLING
from problem_selection_agent import library_matching
from problem_selection_agent.service import SelectionError
from problem_selection_agent.spec import canonical
from tests.fixtures import AuthoringFixture, response
from web.app import ROOT


class LibraryMatchingTests(AuthoringFixture):
    files=('thermoelasticity_field_aliases.json',
        'thermoelasticity_split_models.json',
        'thermoelasticity_joint_model.json')

    def add_thermo(self):
        joint=self.thermoelastic_fixture()
        joint['materials']=[{'constitutive_models':[{'model':'linear_thermoelasticity',
            'fields':['temperature','displacement'],'symmetry':'isotropic'}]}]
        split=deepcopy(joint)
        split['materials']=[{'constitutive_models':[
            {'model':'fourier','fields':['temperature'],'symmetry':'isotropic'},
            {'model':'linear_thermoelasticity','fields':['temperature','displacement'],'symmetry':'isotropic'}]}]
        aliased=deepcopy(joint);aliased['problem']['unknowns']=['t','u']
        aliased['problem']['coupling']['dependencies']=[{'from':'t','to':'u'}]
        aliased['materials'][0]['constitutive_models'][0]['fields']=['t','u']
        for item in aliased['formulation']['weak_form']:
            item['field']={'temperature':'t','displacement':'u'}[item['field']]
        records=[aliased,split,joint]
        for name,record in zip(self.files,records):
            (self.library/name).write_text(json.dumps(record))
        return records

    def full_spec(self,one_way):
        spec=deepcopy(one_way)
        spec['problem']['coupling']['type']=COUPLING[2]
        spec['problem']['coupling']['dependencies'].append({'from':'displacement','to':'temperature'})
        return spec

    def test_invalid_response_envelopes_are_validation_errors(self):
        for payload in (None,True,123,'text',[],{}, {'response':None}, {'response':123}, {'response':[]}):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError,'JSON object containing a response object'):
                    library_matching.enforce_answers(payload,{})

    def test_numeric_interpretation_response_can_be_repaired(self):
        name='linear_elasticity_isotropic_formulation.json'
        self.client.chat.completions.create.side_effect=[response(123456789),
            response(self.proposal(self.elastic)),response({'response':{'library_id':name}})]
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Analyze this elastic specimen.'})
        turn=state['turns'][0]
        self.assertEqual(turn['response']['kind'],'proposal')
        self.assertEqual(turn['validation_repairs'],1)
        self.assertEqual(turn['library_match'],name)
        self.assertIsNone(state['confirmed_selection'])

    def test_numeric_library_review_response_can_be_repaired(self):
        name='linear_elasticity_isotropic_formulation.json'
        self.client.chat.completions.create.side_effect=[response(self.proposal(self.elastic)),
            response(int('57360948921'+'73651928374'*20)),response({'response':{'library_id':name}})]
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Analyze this elastic specimen.'})
        turn=state['turns'][0]
        self.assertEqual(turn['response']['kind'],'proposal')
        self.assertEqual(turn['library_review']['validation_repairs'],1)
        self.assertIn('JSON object',turn['library_review']['validation_errors'][0])
        self.assertEqual(turn['library_match'],name)
        self.assertEqual(self.client.chat.completions.create.call_count,3)
        self.assertIsNone(state['confirmed_selection'])
        repair=self.client.chat.completions.create.call_args.kwargs['messages'][-1]['content']
        self.assertIn('The output failed card schema or consistency validation',repair)

    def test_repeated_numeric_review_responses_report_validation_error_and_preserve_retry(self):
        self.client.chat.completions.create.side_effect=[response(self.proposal(self.elastic)),
            response(123456789),response(987654321)]
        with self.assertRaisesRegex(SelectionError,'JSON object containing a response object') as caught:
            self.service.chat({'mesh_id':self.mesh['id'],'message':'Analyze this elastic specimen.'})
        state=self.service.load(caught.exception.session_id)
        self.assertTrue(state['can_continue'])
        self.assertEqual(state['turns'],[])
        self.assertIsNone(state['confirmed_selection'])
        self.assertEqual(self.client.chat.completions.create.call_count,3)

    def test_wrong_fully_coupled_draft_can_reuse_the_requested_one_way_entry(self):
        records=self.add_thermo();requested={k:records[1][k] for k in ('problem','materials')}
        wrong=self.full_spec(requested)
        self.client.chat.completions.create.return_value=response(self.proposal(wrong))
        self.library_answer={'response':{'library_id':self.files[1]}}
        before={p.name:p.read_bytes() for p in self.library.glob('*.json')}
        state=self.service.chat({'mesh_id':self.mesh['id'],
            'message':'Temperature affects displacement through thermal expansion. Neglect the effect of displacement on temperature.'})
        turn=state['turns'][0]
        self.assertEqual(turn['initial_assessment']['spec']['problem']['coupling']['type'],COUPLING[2])
        self.assertEqual(turn['response']['spec'],requested)
        self.assertEqual(turn['library_match'],self.files[1]);self.assertEqual(turn['response']['kind'],'proposal')
        self.assertIsNone(state['confirmed_selection']);self.assertIsNone(state['generation'])
        self.assertEqual(self.client.chat.completions.create.call_count,2)
        review=json.loads(self.client.chat.completions.create.call_args.kwargs['messages'][1]['content'])
        self.assertIn('Neglect the effect',review['initial_request'])
        self.assertIn(self.files[1],{item['id'] for item in review['library_candidates']})
        self.assertEqual({p.name:p.read_bytes() for p in self.library.glob('*.json')},before)

    def test_internally_inconsistent_draft_reaches_library_review(self):
        records=self.add_thermo();requested={k:records[1][k] for k in ('problem','materials')}
        inconsistent=deepcopy(requested)
        inconsistent['problem']['coupling']['type']=COUPLING[2]
        self.client.chat.completions.create.return_value=response(self.proposal(inconsistent))
        self.library_answer={'response':{'library_id':self.files[1]}}
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Heat the metal beam and calculate thermal deformation.'})
        self.assertEqual(state['turns'][0]['response']['spec'],requested)
        self.assertEqual(state['turns'][0]['response']['kind'],'proposal')
        self.assertEqual(self.client.chat.completions.create.call_count,2)
        review=json.loads(self.client.chat.completions.create.call_args.kwargs['messages'][1]['content'])
        self.assertEqual(review['initial_draft']['problem']['coupling'],inconsistent['problem']['coupling'])

    def test_unresolved_coupling_conflict_becomes_a_fixed_question(self):
        records=self.add_thermo();spec={k:records[1][k] for k in ('problem','materials')}
        spec['problem']['coupling']['type']=COUPLING[2]
        self.client.chat.completions.create.return_value=response(self.proposal(spec))
        self.library_answer=self.proposal(spec)
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Clarify the coupling of the thermal and mechanical fields.'})
        reply=state['turns'][0]['response']
        self.assertEqual(reply['kind'],'question')
        self.assertEqual(reply['fixed_target'],'problem.coupling.type')
        self.assertEqual([item['value'] for item in reply['options']],list(COUPLING))
        self.assertIsNone(state['selection_draft']['problem']['coupling']['type'])
        self.assertIsNone(state['confirmed_selection']);self.assertIsNone(state['generation'])
        self.assertEqual(self.client.chat.completions.create.call_count,2)

    def test_confirmed_coupling_is_preserved_and_only_directions_are_questioned(self):
        records=self.add_thermo();spec={k:records[1][k] for k in ('problem','materials')}
        spec['problem']['coupling']['type']=COUPLING[2]
        assessment,question,found=library_matching.resolve(self.proposal(spec)['response'],[],self.catalog,
            {'problem.coupling.type':COUPLING[2]})
        self.assertEqual(assessment['spec']['problem']['coupling']['type'],COUPLING[2])
        self.assertIsNone(assessment['spec']['problem']['coupling']['dependencies'])
        self.assertEqual(question['targets'],['problem.coupling.dependencies'])
        self.assertIsNone(found)

    def test_inconsistent_new_spec_is_questioned_even_without_candidates(self):
        (self.library/'linear_elasticity_isotropic_formulation.json').unlink()
        spec=self.thermo_spec();spec['problem']['coupling']['type']=COUPLING[2]
        self.client.chat.completions.create.return_value=response(self.proposal(spec))
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Determine the coupling for this thermoelastic model.'})
        self.assertEqual(state['turns'][0]['response']['targets'],['problem.coupling.type'])
        self.assertEqual(self.client.chat.completions.create.call_count,1)

    def test_field_aliases_and_model_decomposition_use_the_stored_spec_without_rewriting(self):
        records=self.add_thermo()
        target={k:records[1][k] for k in ('problem','materials')}
        for index in (0,2):
            draft={k:records[index][k] for k in ('problem','materials')}
            self.client.chat.completions.create.return_value=response(self.proposal(draft))
            self.library_answer={'response':{'library_id':self.files[1]}}
            state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Use steady isotropic linear thermoelasticity with one-way thermal expansion.'})
            self.assertNotEqual(canonical(draft),canonical(target))
            self.assertEqual(state['turns'][0]['response']['spec'],target)
            self.assertEqual(state['turns'][0]['response']['kind'],'proposal')

    def test_a_genuinely_missing_fully_coupled_problem_remains_fully_coupled(self):
        records=self.add_thermo();base={k:records[1][k] for k in ('problem','materials')}
        requested=self.full_spec(base)
        self.client.chat.completions.create.return_value=response(self.proposal(requested))
        self.library_answer=self.proposal(requested)
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Include mutual thermal-mechanical feedback as a fully coupled problem.'})
        reply=state['turns'][0]['response']
        self.assertEqual(reply['kind'],'registration_request')
        self.assertEqual(reply['spec'],requested)
        self.assertIsNone(state['generation']);self.assertIsNone(state['confirmed_selection'])

    def test_candidates_are_filtered_by_user_choices_and_mesh_not_the_draft(self):
        records=self.add_thermo();one_way={k:records[1][k] for k in ('problem','materials')}
        full=self.full_spec(one_way)
        full_file=self.catalog.register(full,records[1]['formulation'])['file']
        answers={'problem.coupling.type':COUPLING[1],'problem.time_dependence':'independent'}
        candidates=self.catalog.candidates(3,answers)
        self.assertIn(self.files[1],{item['id'] for item in candidates})
        self.assertNotIn(full_file,{item['id'] for item in candidates})
        self.assertFalse(self.catalog.candidates(2,answers))
        choices=self.catalog.choices()
        Reply=library_matching.response_model(choices['types'],choices['models'],3,answers,candidates)
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps({'response':{'library_id':full_file}}))

    def test_complete_exact_drafts_are_still_checked_against_the_request(self):
        records=self.add_thermo();one_way={k:records[1][k] for k in ('problem','materials')}
        full=self.full_spec(one_way)
        self.catalog.register(full,records[1]['formulation'])
        self.client.chat.completions.create.return_value=response(self.proposal(full))
        self.library_answer={'response':{'library_id':self.files[1]}}
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Use one-way thermoelasticity; ignore feedback from deformation to temperature.'})
        self.assertEqual(state['turns'][0]['response']['spec'],one_way)
        self.assertEqual(self.client.chat.completions.create.call_count,2)

    def test_a_corrected_review_spec_can_match_without_returning_an_id(self):
        records=self.add_thermo();one_way={k:records[2][k] for k in ('problem','materials')}
        self.client.chat.completions.create.return_value=response(self.proposal(self.full_spec(one_way)))
        self.library_answer=self.proposal(one_way)
        state=self.service.chat({'mesh_id':self.mesh['id'],'message':'Use one-way thermal expansion.'})
        self.assertEqual(state['turns'][0]['response']['kind'],'proposal')
        self.assertEqual(state['turns'][0]['library_match'],self.files[2])

    def test_selected_file_is_pinned_through_approval_and_formulation_handoff(self):
        form=deepcopy(self.catalog.lookup(self.elastic)['formulation'])
        form['weak_form'][0]['linear_form']+=' '
        chosen=self.catalog.register(self.elastic,form)['file']
        self.library_answer={'response':{'library_id':chosen}}
        state=self.start()
        final=self.service.confirm({'session_id':state['id'],'turn_index':0})
        self.assertEqual(final['lookup']['file'],chosen)
        self.assertEqual(final['formulation'],form)
        self.assertIsNone(final['generation'])

    def test_changed_library_entry_requires_review_again_instead_of_generating_silently(self):
        state=self.start();chosen=state['turns'][0]['library_match'];calls=self.client.chat.completions.create.call_count
        (self.library/chosen).unlink()
        with self.assertRaisesRegex(SelectionError,'changed'):
            self.service.confirm({'session_id':state['id'],'turn_index':0})
        self.assertEqual(self.client.chat.completions.create.call_count,calls)
        self.assertIsNone(self.service.load(state['id'])['confirmed_selection'])

    def test_missing_constraints_or_physics_are_questions_not_registration(self):
        self.library_answer=self.assessment_question('problem.linearity')
        state=self.start()
        reply=state['turns'][0]['response']
        self.assertEqual(reply['kind'],'question')
        self.assertEqual(reply['targets'],['problem.linearity'])
        self.assertIsNone(state['confirmed_selection'])

    def test_no_candidates_is_a_code_only_skip_of_semantic_review(self):
        (self.library/'linear_elasticity_isotropic_formulation.json').unlink()
        state=self.start()
        self.assertEqual(self.client.chat.completions.create.call_count,1)
        self.assertTrue(state['turns'][0]['library_review']['skipped'])
        self.assertEqual(state['turns'][0]['response']['kind'],'registration_request')

    def test_review_schema_is_strict_and_ids_cannot_reference_arbitrary_files(self):
        choices=self.catalog.choices();candidates=self.catalog.candidates(3)
        Reply=library_matching.response_model(choices['types'],choices['models'],3,{},candidates)
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps({'response':{'library_id':'../../arbitrary.json'}}))
        def strict(node):
            if isinstance(node,dict):
                if '$ref' in node:self.assertEqual(set(node),{'$ref'})
                if node.get('type')=='object':
                    self.assertFalse(node['additionalProperties']);self.assertEqual(set(node['required']),set(node['properties']))
                for value in node.values():strict(value)
            elif isinstance(node,list):
                for value in node:strict(value)
        strict(Reply.model_json_schema())

    def test_token_usage_combines_interpretation_and_review_without_an_explanation_call(self):
        usage=library_matching.total_usage({'prompt_tokens':3,'completion_tokens':2,'total_tokens':5,
            'completion_tokens_details':{'reasoning_tokens':1},'cost':0.1},
            {'prompt_tokens':7,'completion_tokens':4,'total_tokens':11,
            'completion_tokens_details':{'reasoning_tokens':2},'cost':0.2})
        self.assertEqual(usage['total_tokens'],16);self.assertEqual(usage['completion_tokens_details']['reasoning_tokens'],3)
        self.assertAlmostEqual(usage['cost'],0.3)

    def test_exact_duplicate_registration_reuses_content_but_preserves_distinct_formulations(self):
        existing=self.catalog.lookup(self.elastic);before={p.name:p.read_bytes() for p in self.library.glob('*.json')}
        self.assertEqual(self.catalog.register(self.elastic,existing['formulation']),{'file':existing['file']})
        self.assertEqual({p.name:p.read_bytes() for p in self.library.glob('*.json')},before)
        changed=deepcopy(existing['formulation']);changed['weak_form'][0]['linear_form']+=' '
        self.assertNotEqual(self.catalog.register(self.elastic,changed)['file'],existing['file'])
