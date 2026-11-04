"""English coupling schemas and lossless compatibility with approved old records."""
from copy import deepcopy
import json

from common.coupling import COUPLING, ALIASES, normalized_coupling
from functionspace_agent.agent import response_model, check_card
from functionspace_agent.schema import FunctionSpaceCard
from problem_selection_agent.spec import Coupling, Selection, normalized, canonical
from tests.fixtures import AuthoringFixture


class CouplingTests(AuthoringFixture):
    def test_selection_and_space_schemas_advertise_only_canonical_english_identifiers(self):
        expected=['single_physics','multi_physics_one_way','multi_physics_fully_coupled']
        self.assertEqual(list(COUPLING),expected)
        self.assertEqual(Coupling.model_json_schema()['properties']['type']['enum'],expected)
        self.assertEqual(FunctionSpaceCard.model_json_schema()['properties']['coupling_type']['enum'],expected)

    def test_legacy_selection_aliases_have_identical_lookup_keys_without_mutating_input(self):
        for alias,kind in ALIASES.items():
            with self.subTest(alias=alias):
                selection=self.thermo_spec()
                selection['problem']['coupling']['type']=alias
                if kind==COUPLING[2]:
                    selection['problem']['coupling']['dependencies'].append({'from':'displacement','to':'temperature'})
                before=deepcopy(selection)
                result=normalized(selection)
                direct=Selection.model_validate(selection).model_dump(by_alias=True)
                self.assertEqual(result['problem']['coupling']['type'],kind)
                self.assertEqual(direct,result)
                self.assertEqual(canonical(selection),canonical(result))
                self.assertEqual(selection,before)

    def test_legacy_approved_spaces_are_forwarded_with_the_same_english_coupling_as_selection(self):
        for alias,kind in ALIASES.items():
            with self.subTest(alias=alias):
                selection=self.thermo_spec()
                selection['problem']['coupling']['type']=alias
                card={'unknowns':[
                    {'name':name,'quantity':name,'shape':[] if name=='temperature' else [3],
                     'function_space':{'family':'Lagrange','degree':1}}
                    for name in selection['problem']['unknowns']],
                    'coupling_type':alias,'state_variables':[]}
                before=deepcopy(card)
                result=check_card(card,selection)
                self.assertEqual(result['coupling_type'],kind)
                self.assertEqual(result['unknowns'],card['unknowns'])
                self.assertEqual(card,before)
                reply=response_model(selection)
                schema=json.dumps(reply.model_json_schema(),ensure_ascii=False)
                self.assertNotIn('coupling_type',schema)
                for legacy in ALIASES:self.assertNotIn(legacy,schema)

    def test_invalid_identifiers_are_not_accepted_as_new_categories(self):
        self.assertEqual(normalized_coupling('invalid_coupling'),'invalid_coupling')
        with self.assertRaises(ValueError):
            Coupling.model_validate({'type':'invalid_coupling','dependencies':[{'from':None,'to':None}]})
