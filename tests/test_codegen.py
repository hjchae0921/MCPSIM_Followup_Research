"""Approved cards, stage prompts, KG retrieval, repair and durable web jobs."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests import test_values as value_tests
from codegen.cards import STAGES, split, templates, render
from codegen.runner import run, write_json, procedure
from codegen.service import CodegenService, CodegenError


class CodegenTests(unittest.TestCase):
    def setUp(self):
        self.case=value_tests.BoundaryValuesTests();self.case.setUp();self.addCleanup(self.case.doCleanups)
        self.f=self.case.f;self.authoring=self.f.service
        state=self.case.start();rows=state['boundary_value_requirements'];sid=state['id']
        draft=[{'id':r['id'],'value':[0,0,0] if r['shape'] else 0.1,'unit':'mm'} for r in rows]
        state=self.authoring.update_boundary_values({'session_id':sid,'boundary_value_turn_index':0,'draft':draft})
        state=self.authoring.confirm_boundary_values({'session_id':sid,'boundary_value_turn_index':1})
        state=self.authoring.choose_solver({'session_id':sid,'solver_turn_index':0,'recommendation_index':0})
        self.state=self.authoring.confirm_solver({'session_id':sid,'solver_turn_index':1})
        self.root=Path(self.f.temp.name)/'codegen';self.mesh_folder=Path(self.f.temp.name)/'meshes'/self.f.mesh['id']
        self.mesh_folder.mkdir(parents=True);self.mesh=self.mesh_folder/'model.msh';self.mesh.write_text('fixture mesh')
        self.f.host.mesh_path=lambda _:self.mesh_folder
        self.service=CodegenService(self.root,self.authoring);self.addCleanup(self.service.close)

    def test_projection_preserves_values_formulas_regions_and_stage_scope(self):
        before=deepcopy(self.state);cards=split(self.state,self.mesh)
        self.assertEqual(self.state,before);self.assertEqual(list(cards),[n for n,_ in STAGES])
        self.assertEqual(cards['mesh']['mesh']['coordinate_unit'],'mm');self.assertEqual(cards['mesh']['mesh']['target_coordinate_unit'],'mm')
        self.assertEqual(cards['mesh']['mesh']['regions']['Grip_Right'],{'dim':2,'tags':[3]})
        self.assertEqual(cards['function_space'],self.state['functionspace_card'])
        weak=cards['weak_form'];self.assertEqual(weak['formulation'],self.state['formulation'])
        self.assertEqual(weak['constitutive_parameters'][0]['value'],210.0)
        self.assertIn('symbol',weak['constitutive_parameters'][0])
        self.assertFalse(weak['boundary_parameters']);self.assertTrue(weak['parameter_usage']['boundary_parameters'])
        for rows in weak['parameter_usage'].values():
            for item in rows:self.assertEqual(set(item),{'name','requirement','regions'})
        self.assertNotIn('dirichlet_conditions',weak);self.assertNotIn('solver',weak)
        bc=cards['boundary_conditions'];self.assertEqual(len(bc['boundary_conditions']),4)
        self.assertEqual([p['components'] for p in bc['boundary_conditions']],[[0],[1],[2],[0]])
        self.assertEqual(bc['boundary_conditions'][-1]['parameters']['value'],{'value':0.1,'unit':'mm'})
        self.assertEqual(cards['solve']['solver'],self.state['solver_card']['solver'])
        for card in cards.values():
            for key in ('settings','usage','turns','solver_turns','boundary_value_turns','sha256'):
                self.assertNotIn(key,card)

    def test_missing_approvals_and_computation_settings_block_incomplete_runs(self):
        for edit in ({'stage':'solver_review'},{'solver_input_signature':''},{'solver_card':None}):
            with self.subTest(edit=edit),self.assertRaises(ValueError):split(dict(self.state,**edit),self.mesh)
        for key,value in [('time_dependence','dependent'),('history_dependence',True)]:
            state=deepcopy(self.state);state['confirmed_selection']['problem'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):split(state,self.mesh)
        state=deepcopy(self.state);state['boundary_value_card']['dirichlet_conditions'][0]['region']['tags']=[999]
        with self.assertRaises(ValueError):split(state,self.mesh)
        state=deepcopy(self.state);state['mesh']['summary']['coordinate_unit']=None
        with self.assertRaises(ValueError):split(state,self.mesh)

    def test_render_changes_only_existing_slots_and_procedure_queries_are_original(self):
        cards=split(self.state,self.mesh)
        for stage,source in templates().items():
            system,user,composed=render(source,cards[stage],'{"nodes":[],"edges":[]}','previous_code=1')
            expected=source.replace('{{CARD_JSON}}',json.dumps(cards[stage],ensure_ascii=False,indent=2))
            expected=expected.replace('{{API_KNOWLEDGE_GRAPH}}','{"nodes":[],"edges":[]}')
            expected=expected.replace('{{PREVIOUS_STAGE_CODE}}','```python\nprevious_code=1\n```').replace('{{FORMULATION}}','')
            self.assertEqual(composed,expected)
            self.assertEqual(system,source.partition('=== USER MESSAGE ===\n')[0].removeprefix('=== SYSTEM MESSAGE ===\n').strip())
            self.assertEqual(procedure(source),procedure(composed));self.assertNotIn('{{',user)

    def test_preview_has_no_model_calls_and_start_uses_an_immutable_mesh_and_cards(self):
        before=self.f.client.chat.completions.create.call_count
        preview=self.service.preview({'session_id':self.state['id']})
        self.assertEqual(self.f.client.chat.completions.create.call_count,before)
        with patch.object(self.service,'_launcher',side_effect=OSError('fixture process error')):
            with self.assertRaises(CodegenError):self.service.start({'session_id':self.state['id'],'model':'gpt-5.4-mini','reasoning':'low'})
        latest=self.service.latest(self.state['id'])['run'];self.assertEqual(latest['status'],'failed')
        saved=json.loads(self.service.path(self.state['id'],latest['id']).joinpath('input.json').read_text())
        copied=Path(saved['cards']['mesh']['mesh']['path']);self.assertEqual(copied.read_text(),'fixture mesh')
        self.mesh.write_text('modified original');self.assertEqual(copied.read_text(),'fixture mesh')
        self.assertEqual(saved['cards']['weak_form'],preview['cards']['weak_form'])
        self.assertEqual(saved['settings']['retrieval'],preview['retrieval'])
        self.assertEqual(preview['retrieval']['payload_format'],'normalized-api')
        self.assertEqual(preview['retrieval']['top_k'],3)
        self.assertEqual(preview['retrieval']['hops'],1)

    def test_artifacts_are_run_local_and_old_outputs_are_marked_stale(self):
        with patch.object(self.service,'_launcher',side_effect=OSError()):
            with self.assertRaises(CodegenError):self.service.start({'session_id':self.state['id']})
        result=self.service.latest(self.state['id'])['run'];sid=self.state['id'];rid=result['id']
        self.assertFalse(result['stale']);self.assertEqual(self.service.artifact(sid,rid,'cards/solve.json').name,'solve.json')
        for path in ('../../../../.openai_key','/etc/passwd','missing.py'):
            with self.subTest(path=path),self.assertRaises(CodegenError):self.service.artifact(sid,rid,path)
        self.authoring.start_boundary_values({'session_id':sid})
        self.assertTrue(self.service.latest(sid)['run']['stale'])
        with self.assertRaises(CodegenError):self.service.preview({'session_id':sid})

    def test_status_reads_do_not_cancel_a_completed_run(self):
        with patch.object(self.service,'_launcher',side_effect=OSError()):
            with self.assertRaises(CodegenError):self.service.start({'session_id':self.state['id']})
        status=self.service.latest(self.state['id'])['run'];sid=self.state['id'];rid=status['id']
        path=self.service.path(sid,rid)/'status.json'
        saved=json.loads(path.read_text());saved['status']='succeeded';write_json(path,saved)
        self.service.get(sid,rid);self.service.latest(sid)
        self.assertNotIn((sid,rid),self.service._cancelled)
        self.service._monitor(sid,rid,SimpleNamespace(wait=lambda:0))
        self.assertEqual(self.service.get(sid,rid)['status'],'succeeded')

    def fake_backend(self,folder,fail=False):
        from knowledge_graph.retrieval import GraphRetriever
        queries=[];calls=[];stage_counts={}
        base=GraphRetriever.load()
        def ranked(items,**kwargs):
            queries.extend(items)
            return base.retrieve(items,**kwargs)
        retrieve=SimpleNamespace(retrieve=ranked)
        coder=SimpleNamespace(unfence=lambda value:value)
        def ask(prompt,system,max_tokens):
            stage=next(name for name,label in [('mesh','mesh'),('function_space','function space'),('weak_form','weak form'),('boundary_conditions','boundary condition'),('solve','solve')] if label+' stage coder' in system)
            calls.append((stage,prompt,system));stage_counts[stage]=stage_counts.get(stage,0)+1
            if stage=='weak_form' and (fail or stage_counts[stage]==1):return "raise RuntimeError('fixture repair')"
            number=[n for n,_ in STAGES].index(stage)
            return (f'assert marker_{number-1} == {number-1}\n' if number else '')+f'marker_{number}={number}\n'+("print('SOLVE_COMPLETED')" if stage=='solve' else '')
        def execute(code,stage,output,**kwargs):
            path=folder/f'exec_{stage}.py';path.write_text(coder.PREFIX+code)
            process=subprocess.run([sys.executable,'-B',str(path)],capture_output=True,text=True)
            output(process.stdout,process.stderr);return process.returncode==0,process.stderr
        coder.ask=ask;coder.run_code=execute
        return (retrieve,coder,None),queries,calls

    def runner_folder(self):
        folder=Path(self.f.temp.name)/'runner';folder.mkdir()
        write_json(folder/'input.json',{'cards':split(self.state,self.mesh),'templates':templates(),
            'settings':{'model':'fixture','reasoning':'low','max_fixes':1,'execution_timeout_seconds':60}})
        write_json(folder/'status.json',{'current_stage':None,'stages':[{'name':n,'status':'pending','attempt':0} for n,_ in STAGES]})
        return folder

    def test_runner_uses_one_hop_repairs_only_failed_stage_and_executes_solve(self):
        folder=self.runner_folder();backend,queries,calls=self.fake_backend(folder)
        self.assertTrue(run(folder,backend))
        status=json.loads((folder/'status.json').read_text());self.assertEqual(status['status'],'succeeded')
        self.assertTrue(all(s['status']=='passed' for s in status['stages']))
        self.assertEqual([stage for stage,_,_ in calls].count('weak_form'),2)
        self.assertIn('Runtime error',next(prompt for stage,prompt,_ in reversed(calls) if stage=='weak_form'))
        self.assertEqual(len(queries),sum(len(procedure(s)) for s in templates().values()))
        fragment=json.loads((folder/'1_mesh/graph.json').read_text());self.assertEqual(fragment['format'],'normalized-api')
        self.assertIn('SOLVE_COMPLETED',(folder/'5_solve/attempt_0.stdout.txt').read_text())
        self.assertIn('marker_4',(folder/'accumulated.py').read_text())
        self.assertEqual(json.loads((folder/'results/manifest.json').read_text())['status'],'failed')
        # No FE functions exist in this test backend: result export failure must not retry or fail solve.
        self.assertEqual([stage for stage,_,_ in calls].count('solve'),1)

    def test_runner_stops_after_unrepaired_error_and_persists_failure(self):
        folder=self.runner_folder();backend,_,calls=self.fake_backend(folder,fail=True)
        self.assertFalse(run(folder,backend));status=json.loads((folder/'status.json').read_text())
        self.assertEqual(status['status'],'failed');self.assertIn('fixture repair',status['error'])
        self.assertNotIn('solve',[stage for stage,_,_ in calls]);self.assertFalse((folder/'5_solve').exists())

    def test_runner_delivers_real_compact_API_for_all_five_stages(self):
        from knowledge_graph.retrieval import GraphRetriever,configuration
        from knowledge_graph.wire import decode
        folder=self.runner_folder();backend,_,_=self.fake_backend(folder)
        snapshot=json.loads((folder/'input.json').read_text())
        snapshot['settings']['retrieval']=configuration();write_json(folder/'input.json',snapshot)
        self.assertTrue(run(folder,(GraphRetriever.load(),backend[1],None)))
        status=json.loads((folder/'status.json').read_text())
        for number,(stage,_) in enumerate(STAGES,1):
            path=folder/f'{number}_{stage}'
            graph=json.loads((path/'graph.json').read_text())
            ids=json.loads((path/'graph_ids.json').read_text())
            normalized=decode(graph,original_ids=ids)
            retrieval=json.loads((path/'retrieval.json').read_text())
            self.assertEqual(retrieval['settings'],configuration())
            self.assertTrue(all(len(row['top_3'])==3 for row in retrieval['queries']))
            self.assertEqual(retrieval['node_count'],len(normalized['nodes']))
            self.assertEqual(status['stages'][number-1]['node_count'],len(normalized['nodes']))
            self.assertIn('local references',(path/'prompt_used.txt').read_text())


if __name__=='__main__':unittest.main()
