"""Solver proposals use measured capabilities and require explicit, current approval."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.fixtures import AuthoringFixture
from solver_agent import agent, environment
from problem_selection_agent.service import ProblemSelectionService, SelectionError


class SolverTests(unittest.TestCase):
    def setUp(self):
        self.f=AuthoringFixture();self.f.setUp();self.addCleanup(self.f.tearDown)
        self.service=self.f.service

    def start(self):
        state=self.f.start_source_boundaries();sid=state['id']
        self.service.confirm_boundary_parameter_selection({'session_id':sid,'boundary_parameter_turn_index':0})
        return self.service.confirm_boundary_values({'session_id':sid,'boundary_value_turn_index':0})

    def choose(self,state):
        return self.service.choose_solver({'session_id':state['id'],
            'solver_turn_index':len(state['solver_turns'])-1,'recommendation_index':0})

    def approve(self,state):
        return self.service.confirm_solver({'session_id':state['id'],'solver_turn_index':len(state['solver_turns'])-1})

    def test_recommendation_exact_choice_manual_edit_and_approval(self):
        state=self.start();sid=state['id'];self.assertEqual(state['stage'],'solver_review')
        self.assertFalse(state['solver_card'])
        request=self.f.client.chat.completions.create.call_args.kwargs
        self.assertEqual(request['reasoning_effort'],'low')
        before=self.f.client.chat.completions.create.call_count
        with self.assertRaises(SelectionError):self.approve(state)
        state=self.choose(state)
        proposed=state['solver_turns'][-1]['response']['proposed_card']
        self.assertEqual(proposed,self.f.solver_recommendation()['response']['recommendations'][0]['card'])
        edit=deepcopy(proposed);edit['solver']['linear'].update(type='iterative',ksp_type='gmres',pc_type='jacobi',factor_solver=None,rtol=1e-8,max_iterations=1000)
        state=self.service.update_solver({'session_id':sid,'solver_turn_index':1,'card':edit})
        self.assertFalse(state['solver_card'])
        with self.assertRaises(SelectionError):self.service.confirm_solver({'session_id':sid,'solver_turn_index':1})
        state=self.approve(state)
        self.assertEqual(state['solver_card'],edit);self.assertEqual(state['stage'],'complete')
        self.assertFalse(self.service.snapshot(sid).next)
        self.assertEqual(self.f.client.chat.completions.create.call_count,before)

    def test_context_only_approved_inputs_and_solver_own_dialogue(self):
        state=self.start();request=self.f.client.chat.completions.create.call_args.kwargs
        context=json.loads(request['messages'][1]['content'].split('\n',1)[1])
        self.assertEqual(context['initial_request'],state['initial_request'])
        self.assertEqual(context['boundary_value_card'],state['boundary_value_card'])
        self.assertEqual(context['execution_environment']['execution_mpi_size'],None)
        for key in ('turns','material_turns','boundary_value_turns','settings','id','review_turns'):
            self.assertNotIn(key,context)
        self.assertEqual(len(request['messages']),2)
        self.f.solver_answer={'response':{'explanation':"Modified to iterative method.",'proposed_card':{
            'solver':{'linear':dict(self.f.solver_linear(),type='iterative',ksp_type='gmres',pc_type='jacobi',factor_solver=None),
                      'nonlinear':None}}}}
        state=self.service.chat({'session_id':state['id'],'solver_turn_index':0,'message':"Please change it to iterative method."})
        self.assertEqual(len(self.f.client.chat.completions.create.call_args.kwargs['messages']),4)
        self.assertEqual(state['solver_turns'][-1]['response']['proposed_card']['solver']['linear']['ksp_type'],'gmres')

    def test_restart_old_session_entry_and_upstream_invalidation(self):
        state=self.approve(self.choose(self.start()));sid=state['id'];card=state['solver_card']
        other=ProblemSelectionService(self.service.folder,self.f.library,self.f.host)
        try:self.assertEqual(other.load(sid)['solver_card'],card)
        finally:other.close()
        state=self.service.start_boundary_values({'session_id':sid})
        self.assertIsNone(state['solver_card']);self.assertEqual(state['solver_history'][-1]['card'],card)
        state=self.service.confirm_boundary_values({'session_id':sid,'boundary_value_turn_index':0})
        self.assertEqual(state['stage'],'solver_review')
        # A boundary-only checkpoint from the previous application can enter the new stage.
        self.service.workflow.graph.update_state(self.service.workflow.config(sid),{
            'stage':'complete','solver_turns':[],'solver_card':{'legacy':True},'solver_input_signature':''},as_node='solver_review')
        self.assertIsNone(self.service.load(sid)['solver_card'])
        state=self.service.start_solver({'session_id':sid})
        self.assertEqual(state['stage'],'solver_review')
        state=self.service.start_boundary_parameter_selection({'session_id':sid})
        self.assertEqual(state['solver_turns'],[]);self.assertFalse(state['solver_card'])

    def test_changed_environment_requires_refresh_and_failed_request_retries(self):
        state=self.choose(self.start());sid=state['id']
        self.f.environment['environment_id']='new-runtime'
        with self.assertRaises(SelectionError):self.approve(state)
        state=self.service.refresh_solver({'session_id':sid,'solver_turn_index':1})
        self.assertEqual(state['solver_environment']['environment_id'],'new-runtime')
        self.f.solver_answer=ValueError('temporary API error')
        with self.assertRaises(SelectionError):self.service.chat({'session_id':sid,'solver_turn_index':0,'message':"Please change the tolerance."})
        state=self.service.load(sid);self.assertTrue(state['can_continue']);self.assertTrue(state['boundary_value_card'])
        self.f.solver_answer=None
        state=self.service.continue_session({'session_id':sid})
        self.assertEqual(state['stage'],'solver_review');self.assertEqual(len(state['solver_turns']),2)

    def test_schema_nonlinear_card_and_runtime_validation(self):
        env=self.f.environment;spec=deepcopy(self.f.elastic);spec['problem']['linearity']='nonlinear'
        card={'solver':{'linear':None,'nonlinear':{'method':'newtonls','line_search':'bt',
            'rtol':1e-8,'atol':1e-10,'stol':1e-10,'max_iterations':50,
            'linear_solver':self.f.solver_linear(),'options':[{'name':'snes_linesearch_damping','value':0.9}]}}}
        agent.check_card(card,spec,env)
        Reply=agent.response_model(spec,env)
        Reply.model_validate_json(json.dumps({'response':{'explanation':"Nonlinear analysis",'proposed_card':card}}))
        def strict(node):
            if isinstance(node,dict):
                if '$ref' in node:self.assertEqual(set(node),{'$ref'})
                if node.get('type')=='object':
                    self.assertFalse(node['additionalProperties']);self.assertEqual(set(node['required']),set(node['properties']))
                for child in node.values():strict(child)
            elif isinstance(node,list):
                for child in node:strict(child)
        strict(Reply.model_json_schema());strict(agent.response_model(self.f.elastic,env).model_json_schema())
        # PETSc integer options must not become strings such as '50.0'.
        option=agent.Option.model_validate({'name':'ksp_gmres_restart','value':50}).model_dump()
        self.assertIs(type(option['value']),int)
        mutations=[('method','invented'),('line_search','invented'),('rtol',-1),('rtol',1),('atol',float('nan')),
            ('max_iterations',0),('max_iterations',True),('options',[{'name':'snes_type','value':'newtontr'}]),
            ('options',[{'name':'ksp_type','value':'cg'}])]
        for key,value in mutations:
            bad=deepcopy(card);bad['solver']['nonlinear'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):agent.check_card(bad,spec,env)
        with self.assertRaises(ValueError):agent.check_card(card,self.f.elastic,env)
        for key,value in [('ksp_type','not_installed'),('pc_type','not_installed'),('factor_solver','not_installed'),
            ('options',[{'name':'-ksp_monitor','value':True}]),('options',[{'name':'sub_pc_type','value':'invented'}]),
            ('options',[{'name':'ksp_monitor','value':True}]*2)]:
            bad=deepcopy(card);bad['solver']['nonlinear']['linear_solver'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):agent.check_card(bad,spec,env)

    def test_nonlinear_proposal_round_trip_and_latest_question_cannot_approve(self):
        state=self.start();sid=state['id'];spec=deepcopy(state['confirmed_selection']);spec['problem']['linearity']='nonlinear'
        self.service.workflow.graph.update_state(self.service.workflow.config(sid),{'confirmed_selection':spec},as_node='solver_parameters')
        self.service._run(sid,None)
        card={'solver':{'linear':None,'nonlinear':{'method':'newtontr','line_search':None,
            'rtol':1e-8,'atol':1e-10,'stol':None,'max_iterations':40,'linear_solver':self.f.solver_linear(),'options':[]}}}
        self.f.solver_answer={'response':{'explanation':"This is a nonlinear solver.",'proposed_card':card}}
        state=self.service.chat({'session_id':sid,'solver_turn_index':0,'message':"Please suggest a nonlinear setting."})
        self.assertEqual(self.approve(state)['solver_card'],card)

    def test_full_petsc_option_names_are_enforced_by_schema_and_validation(self):
        card={'solver':{'linear':dict(self.f.solver_linear(),type='iterative',ksp_type='cg',pc_type='hypre',
            factor_solver=None,options=[{'name':'pc_hypre_type','value':'boomeramg'},
                {'name':'pc_hypre_boomeramg_max_iter','value':1}]),'nonlinear':None}}
        validated=agent.check_card(card,self.f.elastic,self.f.environment)
        self.assertEqual(validated,card)
        Reply=agent.response_model(self.f.elastic,self.f.environment)
        Reply.model_validate_json(json.dumps({'response':{'explanation':"Uses the preprocessor in the installed environment.",'proposed_card':card}}))
        for name in ('hypre_type','hypre_boomeramg_max_iter','-pc_hypre_type','run_prefix_pc_hypre_type'):
            bad=deepcopy(card);bad['solver']['linear']['options'][0]['name']=name
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError,"full official PETSc option name"):agent.check_card(bad,self.f.elastic,self.f.environment)
                with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps({'response':{'explanation':"Review draft",'proposed_card':bad}}))

    def test_invalid_option_response_can_retry_with_the_same_approved_physics(self):
        self.f.solver_answer=self.f.solver_recommendation()
        bad=self.f.solver_answer['response']['recommendations'][0]['card']['solver']['linear']
        bad.update(type='iterative',ksp_type='cg',pc_type='hypre',factor_solver=None,
            options=[{'name':'hypre_type','value':'boomeramg'}])
        with self.assertRaises(SelectionError):self.start()
        sid=next(p.name for p in self.service.folder.iterdir() if p.is_dir())
        waiting=self.service.load(sid)
        self.assertTrue(waiting['can_continue']);self.assertEqual(waiting['stage'],'solver_parameters')
        bad['options'][0]['name']='pc_hypre_type'
        result=self.service.continue_session({'session_id':sid})
        self.assertEqual(result['stage'],'solver_review');self.assertIsNone(result['solver_card'])
        self.assertEqual(result['boundary_value_card'],waiting['boundary_value_card'])

    def test_redundant_core_options_are_removed_and_conflicts_are_rejected(self):
        card={'solver':{'linear':dict(self.f.solver_linear(),options=[
            {'name':'pc_factor_mat_solver_type','value':'mumps'},{'name':'pc_type','value':'lu'},
            {'name':'ksp_type','value':'preonly'},{'name':'ksp_monitor','value':False}]),'nonlinear':None}}
        before=deepcopy(card);validated=agent.check_card(card,self.f.elastic,self.f.environment)
        self.assertEqual(card,before)
        self.assertEqual(validated['solver']['linear']['options'],[{'name':'ksp_monitor','value':False}])
        for name,value in [('pc_factor_mat_solver_type','petsc'),('pc_type','hypre'),('ksp_rtol',1e-8)]:
            bad=deepcopy(card);bad['solver']['linear']['options']=[{'name':name,'value':value}]
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,"conflict"):agent.check_card(bad,self.f.elastic,self.f.environment)

    def test_question_waits_and_changed_approved_cards_require_new_proposal(self):
        state=self.start();sid=state['id']
        self.f.solver_answer={'response':{'question_type':'input','question':"Please tell me the expected number of parallel processes.",'options':[],'targets':['solver.linear.pc_type']}}
        state=self.service.chat({'session_id':sid,'solver_turn_index':0,'message':"Please also consider parallel execution."})
        with self.assertRaises(SelectionError):self.approve(state)
        self.f.solver_answer=None
        state=self.service.chat({'session_id':sid,'solver_turn_index':1,'message':"The number of processes has not been decided yet."})
        state=self.choose(state)
        changed=deepcopy(state['material_card']);changed['constitutive_parameters'][0]['value']=300000.0
        self.service.workflow.graph.update_state(self.service.workflow.config(sid),{'material_card':changed},as_node='solver_parameters')
        self.service._run(sid,None)
        with self.assertRaises(SelectionError):self.approve(state)


class EnvironmentTests(unittest.TestCase):
    def test_probe_cache_refresh_and_failures_never_invent_capabilities(self):
        import tempfile
        f=AuthoringFixture();f.setUp();self.addCleanup(f.tearDown)
        report=deepcopy(f.environment)
        completed=SimpleNamespace(returncode=0,stdout='native log\n'+environment.MARKER+json.dumps(report)+'\n',stderr='')
        with tempfile.TemporaryDirectory() as folder,patch.object(environment.subprocess,'run',return_value=completed) as run:
            first=environment.discover(folder);second=environment.discover(folder)
            self.assertEqual(first,second);self.assertEqual(run.call_count,1)
            environment.discover(folder,refresh=True);self.assertEqual(run.call_count,2)
            run.return_value=SimpleNamespace(returncode=59,stdout='',stderr='native crash')
            with self.assertRaises(ValueError):environment.discover(folder,refresh=True)
            self.assertEqual(json.loads((Path(folder)/'solver_environment.json').read_text())['capabilities'],first)


if __name__=='__main__':unittest.main()
