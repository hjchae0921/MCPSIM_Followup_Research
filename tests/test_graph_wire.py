"""Calling-contract preservation and actual API coder-prompt delivery."""

from copy import deepcopy
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import numpy as np

from codegen.cards import render, templates as web_templates
from codegen.runner import procedure
from knowledge_graph.signatures import type_expression
from knowledge_graph.retrieval import GraphRetriever
from codegen.cards import templates
from knowledge_graph.search import search_documents
from knowledge_graph.wire import dumps as dump
from knowledge_graph.wire import FORMAT, decode, encode, id_map


def fixture():
    nodes = [
        {"id": "example.solve", "kind": "function", "description": "Compute α and retain internal spaces.",
         "notes": "Keep the documented sign convention.", "extra": {"preserve": True}},
        {"id": "example.solve::x", "kind": "argument", "name": "x", "position": 0,
         "parameter_kind": "positional_only", "default": {"state": "absent"},
         "type": type_expression("tuple[example.Space, numpy.ndarray] | None")},
        {"id": "example.solve::alpha", "kind": "argument", "name": "alpha",
         "parameter_kind": "keyword_only", "default": {"state": "specified", "expression": "None"},
         "type": type_expression("float | None")},
        {"id": "example.solve::args", "kind": "argument", "name": "args", "parameter_kind": "var_positional",
         "default": {"state": "absent"}},
        {"id": "example.solve::kw", "kind": "argument", "name": "kw", "parameter_kind": "var_keyword",
         "default": {"state": "absent"}},
        {"id": "example.solve::V", "kind": "argument", "name": "V", "declaration": "documentation_only"},
        {"id": "example.solve::result", "kind": "return", "type": type_expression("tuple[example.Space, numpy.ndarray]")},
        {"id": "example.Space", "kind": "class", "description": "A space.\n\nInitialize a space."},
        {"id": "example.BaseSpace", "kind": "class", "description": "Base representation."},
        {"id": "example.Space.sub", "kind": "method", "receiver_name": "self", "description": "Read a subspace."},
        {"id": "example.Space.sub::i", "kind": "argument", "name": "i", "position": 0,
         "parameter_kind": "positional_or_keyword", "type": type_expression("int"), "default": {"state": "absent"}},
        {"id": "example.Space.values", "kind": "property", "type": type_expression("numpy.ndarray")},
    ]
    edges = [{"kind": "HAS_ARGUMENT", "src": "example.solve", "dst": "example.solve::" + name,
              "variants": [0, 1]} for name in ["x", "alpha", "args", "kw", "V"]]
    edges += [
        {"kind": "HAS_RETURN", "src": "example.solve", "dst": "example.solve::result", "variants": [1]},
        {"kind": "HAS_MEMBER", "src": "example.Space", "dst": "example.Space.sub"},
        {"kind": "HAS_ARGUMENT", "src": "example.Space.sub", "dst": "example.Space.sub::i"},
        {"kind": "HAS_MEMBER", "src": "example.Space", "dst": "example.Space.values"},
        {"kind": "INHERITS", "src": "example.Space", "dst": "example.BaseSpace"},
        {"kind": "FEEDS", "src": "example.solve::result", "dst": "example.solve::x",
         "role": "argument", "source_path": [0], "target_path": [1]},
    ]
    return {"nodes": nodes, "edges": edges}


class WireTests(unittest.TestCase):
    def test_complete_calling_contract_and_every_relationship_roundtrip(self):
        original = fixture(); before = deepcopy(original)
        payload = encode(original)
        self.assertEqual(decode(payload, original_ids=id_map(original)), original)
        self.assertEqual(original, before)
        self.assertEqual(json.loads(dump(original)), payload)

    def test_no_default_python_none_and_undocumented_are_distinct(self):
        original = fixture(); payload = encode(original)
        args = {n['name']: n for n in payload['nodes']['argument']}
        self.assertIsNone(args['x']['default'])
        self.assertEqual(args['alpha']['default'], 'None')
        self.assertNotIn('default', args['V'])
        self.assertEqual(args['alpha']['parameter_kind'], 'keyword_only')
        self.assertEqual(args['x']['parameter_kind'], 'positional_only')
        self.assertEqual(args['args']['parameter_kind'], 'var_positional')
        self.assertEqual(args['kw']['parameter_kind'], 'var_keyword')

    def test_api_identities_survive_shortening_declaration_references(self):
        original = fixture(); payload = encode(original)
        apis = [n['api'] for group in payload['nodes'].values() for n in group if 'api' in n]
        self.assertEqual(set(apis), {n['id'] for n in original['nodes'] if n['kind'] not in {'argument','return'}})
        self.assertTrue(all(n['id'].startswith('n') and '::' not in n['id']
                            for group in payload['nodes'].values() for n in group))
        ids = {n['id'] for group in payload['nodes'].values() for n in group}
        self.assertTrue(all(e[1] in ids and e[2] in ids for e in payload['edges']))

    def test_unrecognized_types_and_default_metadata_are_not_discarded(self):
        original = fixture()
        original['nodes'][1]['type'] = {'kind': 'future_annotation', 'shape': [2, 2]}
        original['nodes'][1]['default'] = {'state': 'unknown', 'source_note': 'Wrapper declaration.'}
        payload = encode(original)
        self.assertEqual(decode(payload, original_ids=id_map(original)), original)

    def test_method_property_and_overload_membership_survive(self):
        original = fixture(); result = decode(encode(original), original_ids=id_map(original))
        by_id = {n['id']: n for n in result['nodes']}
        self.assertEqual(by_id['example.Space.sub']['kind'], 'method')
        self.assertEqual(by_id['example.Space.values']['kind'], 'property')
        self.assertEqual(by_id['example.Space.sub']['receiver_name'], 'self')
        self.assertEqual([e['variants'] for e in result['edges'] if e['kind']=='HAS_RETURN'], [[1]])

    def test_dangling_references_and_duplicate_nodes_cannot_be_silently_lost(self):
        for corrupt in ['duplicate', 'dangling']:
            graph = fixture()
            if corrupt == 'duplicate': graph['nodes'].append(deepcopy(graph['nodes'][0]))
            else: graph['edges'].append({'kind':'FEEDS','src':'missing','dst':'example.solve'})
            with self.subTest(corrupt=corrupt), self.assertRaises(ValueError): encode(graph)

    def test_empty_fragment_has_valid_reversible_format(self):
        original = {'nodes': [], 'edges': []}
        self.assertEqual(decode(encode(original), original_ids={}), original)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.graph = fixture()
        self.ids = [r['id'] for r in search_documents(self.graph)]
        self.retriever = GraphRetriever(self.graph, self.ids, np.eye(len(self.ids)))
        self.query = np.ones(len(self.ids))

    def test_retrieval_delivers_compact_payload_with_correct_counts_and_no_loss(self):
        result = self.retriever.retrieve(['Prepare the field.'], query_vectors={'Prepare the field.': self.query})
        self.assertEqual(result.payload['format'], FORMAT)
        self.assertEqual(result.node_count, len(result.fragment['nodes']))
        self.assertNotEqual(result.node_count, len(result.payload['nodes']))
        self.assertEqual(decode(result.payload, original_ids=result.original_ids), result.fragment)
        self.assertEqual(result.edge_count, len(result.payload['edges']))

    def test_missing_query_vectors_are_batched_and_duplicate_queries_reused(self):
        client = SimpleNamespace(embeddings=SimpleNamespace(create=Mock(return_value=SimpleNamespace(
            data=[SimpleNamespace(index=0, embedding=self.query)]))))
        self.retriever.retrieve(['Prepare the field.', 'Prepare the field.'], client=client)
        client.embeddings.create.assert_called_once_with(model='text-embedding-3-large', input=['Prepare the field.'])

    def test_prompt_rendering_uses_compact_reference_without_changing_procedure(self):
        result = self.retriever.retrieve(['Prepare the field.'], query_vectors={'Prepare the field.': self.query})
        source = templates()['function_space']
        _, user, composed = render(source, {'unknowns': []}, result.text, 'V = ready_space')
        self.assertEqual(procedure(source), procedure(composed))
        self.assertIn(FORMAT, user)
        self.assertIn('example.solve', user)
        self.assertIn('local references', user)
        self.assertIn('V = ready_space', user)

    def test_function_space_bundle_preserves_selected_actions_and_state_rules(self):
        for variant in ['no_card_descriptions','top_level_card_descriptions']:
            source = templates(variant)['function_space']; queries = procedure(source)
            self.assertEqual(len(queries), 6)
            self.assertIn('combine the component finite elements into a mixed element', queries[1])
            self.assertTrue(queries[3].startswith('Initialize persistent finite element functions'))
            self.assertIn('one trial argument and one test argument', queries[4])
            self.assertIn('unpack them into the components', queries[5])
            self.assertIn('Components of one monolithic form must share the same parent space.', source)
            self.assertIn('Leave physical initialization and state-value updates to the solve stage.', source)
        self.assertEqual(procedure(templates()['function_space']),
                         procedure(templates('top_level_card_descriptions')['function_space']))
        self.assertIn('local references', web_templates()['function_space'])
        self.assertEqual(web_templates(), templates())
        self.assertEqual(len(procedure(web_templates()['function_space'])), 6)


if __name__ == '__main__':
    unittest.main()
