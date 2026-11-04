"""Web promotion preserves contracts, strict one-hop expansion and uniform k=3."""

from copy import deepcopy
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import numpy as np

from codegen.cards import ROOT, templates
from codegen.runner import procedure
from codegen.service import CodegenService
from knowledge_graph.search import search_documents
from knowledge_graph.retrieval import GraphRetriever, configuration
from knowledge_graph.wire import decode
from tests.test_graph_wire import fixture


class RetrievalTests(unittest.TestCase):
    def test_all_actual_stage_procedures_use_three_seeds_and_cached_embeddings(self):
        retriever=GraphRetriever.load()
        client=SimpleNamespace(embeddings=SimpleNamespace(create=Mock(side_effect=AssertionError('Unexpected embedding call'))))
        checklist=json.loads((ROOT/'tests/data/required_apis.json').read_text())
        for stage,source in templates().items():
            with self.subTest(stage=stage):
                queries=procedure(source)
                result=retriever.retrieve(queries,client=client)
                self.assertEqual([r['query'] for r in result.rankings],queries)
                self.assertTrue(all(len(row['top_3'])==3 for row in result.rankings))
                self.assertEqual(decode(result.payload,original_ids=result.original_ids),result.fragment)
                present={n['id'] for n in result.fragment['nodes']}
                self.assertFalse(set(checklist.get(stage,[]))-present)
        client.embeddings.create.assert_not_called()

    def test_search_documents_preserve_function_purpose_without_port_duplication(self):
        retriever=GraphRetriever.load()
        documents={r['id']:r['text'] for r in search_documents(retriever.graph)}
        for node in retriever.graph['nodes']:
            if node['kind']!='function':continue
            expected=['API: '+node['id'],'Kind: function']
            if node.get('description'):expected.append('Purpose: '+node['description'].split('\n\n',1)[0])
            self.assertEqual(documents[node['id']],'\n'.join(expected))

    def test_members_keep_ports_and_owner_without_expanding_attached_owner(self):
        graph=fixture()
        graph['nodes'].append({'id':'example.Space::constructor_arg','kind':'argument','name':'mesh'})
        graph['edges'].append({'kind':'HAS_ARGUMENT','src':'example.Space','dst':'example.Space::constructor_arg'})
        ids=[row['id'] for row in search_documents(graph)]
        vectors=np.eye(len(ids));query=np.zeros(len(ids))
        for api in ['example.Space.sub','example.Space.values','example.solve']:
            query[ids.index(api)]=1
        result=GraphRetriever(graph,ids,vectors).retrieve(['Read tagged data.'],query_vectors={'Read tagged data.':query})
        present={n['id'] for n in result.fragment['nodes']}
        self.assertIn('example.Space.sub::i',present)
        self.assertIn('example.Space',present)
        self.assertNotIn('example.Space::constructor_arg',present)
        self.assertNotIn('example.BaseSpace',present)

    def test_uniform_settings_ignore_client_supplied_k_or_hops(self):
        config=CodegenService.settings({'retrieval':{'top_k':10,'hops':2}})['retrieval']
        self.assertEqual(config,configuration())
        self.assertEqual((config['top_k'],config['hops']),(3,1))

    def test_snapshot_asset_or_settings_mismatch_is_rejected(self):
        config=deepcopy(configuration());config['top_k']=2
        with self.assertRaisesRegex(ValueError,'changed after'):
            GraphRetriever.load(expected=config)

    def test_unknown_queries_are_embedded_once_and_checked_for_dimension(self):
        graph=fixture();ids=[r['id'] for r in search_documents(graph)]
        retriever=GraphRetriever(graph,ids,np.eye(len(ids)))
        client=SimpleNamespace(embeddings=SimpleNamespace(create=Mock(return_value=SimpleNamespace(
            data=[SimpleNamespace(index=0,embedding=np.ones(len(ids)))]))))
        retriever.retrieve(['New query.','New query.'],client=client)
        retriever.retrieve(['New query.'],client=client)
        client.embeddings.create.assert_called_once_with(model='text-embedding-3-large',input=['New query.'])
        with self.assertRaisesRegex(ValueError,'dimensions'):
            retriever.retrieve(['Invalid query.'],query_vectors={'Invalid query.':[1]})


if __name__=='__main__':unittest.main()
