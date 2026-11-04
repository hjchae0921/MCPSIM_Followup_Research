"""Persisted HITL flow from model selection through approved solver settings."""
import sqlite3
from dataclasses import replace
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from common.authoring import progress
from common.provenance import sync as sync_field_status


def tracked(node):
    def invoke(state):
        result=node(state)
        updates=dict(result.update or {}) if isinstance(result,Command) else dict(result)
        updates['authoring_status']=progress({**state,**updates})
        updates['field_status']=sync_field_status({**state,**updates})
        return replace(result,update=updates) if isinstance(result,Command) else updates
    return invoke


class State(TypedDict):
    id: str
    created_at: str
    stage: str
    settings: dict
    initial_request: str
    user_message: str
    mesh: dict
    turns: list
    selection_answers: dict
    selection_draft: dict | None
    confirmed_selection: dict | None
    selection_library_file: str | None
    lookup: dict | None
    generation: dict | None
    formulation: dict | None
    saved_files: dict | None
    review_turns: list
    review_message: str
    review_input: dict | None
    functionspace_turns: list
    functionspace_message: str
    functionspace_card: dict | None
    functionspace_draft: dict | None
    material_turns: list
    material_message: str
    material_selection: list
    material_card: dict | None
    material_draft: dict | None
    retry_node: str
    boundary_parameter_turns: list
    boundary_parameter_message: str
    boundary_parameter_assessment: dict | None
    boundary_value_turns: list
    boundary_value_message: str
    boundary_value_requirements: list
    boundary_value_draft: list
    boundary_value_card: dict | None
    boundary_value_history: list
    solver_turns: list
    solver_message: str
    solver_card: dict | None
    solver_environment: dict
    solver_input_signature: str
    solver_history: list
    solver_refresh: bool
    authoring_status: dict
    field_status: dict


class Workflow:
    def __init__(self, folder, classify, lookup, generate, save, review, propose_spaces, propose_materials, select_boundary_parameters, collect_boundary_values, propose_solvers):
        self.connection = sqlite3.connect(str(folder / 'selection.sqlite'), check_same_thread=False)
        self.checkpointer = SqliteSaver(self.connection)
        self.classify, self.lookup, self.generate, self.save = classify, lookup, generate, save
        self.review, self.propose_spaces, self.propose_materials = review, propose_spaces, propose_materials
        self.select_boundary_parameters, self.collect_boundary_values = select_boundary_parameters, collect_boundary_values
        self.propose_solvers=propose_solvers
        graph = StateGraph(State)
        graph.add_node('retry_checkpoint',tracked(lambda state: {}))
        graph.add_node('selection',tracked(self.selection))
        graph.add_node('selection_review',tracked(self.selection_review),destinations=('selection','library_lookup'))
        graph.add_node('library_lookup',tracked(self.library_lookup),destinations=('generate_formulation','function_space'))
        graph.add_node('generate_formulation',tracked(self.generate_formulation))
        graph.add_node('expert_review',tracked(self.expert_review),destinations=('revise_formulation','function_space'))
        graph.add_node('revise_formulation',tracked(self.revise_formulation))
        graph.add_node('function_space',tracked(self.function_space))
        graph.add_node('function_space_review',tracked(self.function_space_review),destinations=('function_space','material_parameters'))
        graph.add_node('material_parameters',tracked(self.material_parameters))
        graph.add_node('material_review',tracked(self.material_review),destinations=('material_review','material_parameters','boundary_parameter_selection'))
        graph.add_node('boundary_parameter_selection',tracked(self.boundary_parameter_selection))
        graph.add_node('boundary_parameter_review',tracked(self.boundary_parameter_review),destinations=('boundary_parameter_selection','boundary_parameter_review','boundary_values'))
        graph.add_node('boundary_values',tracked(self.boundary_values))
        graph.add_node('boundary_value_review',tracked(self.boundary_value_review),destinations=('boundary_values','boundary_value_review','solver_parameters'))
        graph.add_node('solver_parameters',tracked(self.solver_parameters))
        graph.add_node('solver_review',tracked(self.solver_review),destinations=('solver_parameters','solver_review',END))
        graph.add_edge(START,'selection')
        for start,end in [('selection','selection_review'),('generate_formulation','expert_review'),
                          ('revise_formulation','expert_review'),('function_space','function_space_review'),
                          ('material_parameters','material_review'),('boundary_parameter_selection','boundary_parameter_review'),
                          ('boundary_values','boundary_value_review'),('solver_parameters','solver_review')]:
            graph.add_edge(start,end)
        retry_nodes=('selection','library_lookup','generate_formulation','revise_formulation','function_space',
                     'material_parameters','boundary_parameter_selection','boundary_values','solver_parameters')
        graph.add_conditional_edges('retry_checkpoint',lambda state: state['retry_node'],{name:name for name in retry_nodes})
        self.graph=graph.compile(checkpointer=self.checkpointer)

    @staticmethod
    def config(session_id):
        return {'configurable': {'thread_id': session_id}}

    def selection(self, state):
        turn = self.classify(state)
        return {'turns': state['turns'] + [turn], 'selection_draft': turn['assessment']['spec'], 'stage': 'selection_review'}

    def selection_review(self, state):
        decision = interrupt({'stage': 'selection_review', 'turn_index': len(state['turns']) - 1})
        if decision['action'] == 'message':
            return Command(update={'user_message':decision['message'],'settings':decision['settings'],
                'selection_answers':decision.get('selection_answers',state.get('selection_answers',{}))},goto='selection')
        return Command(update={'confirmed_selection':decision['spec'],'settings':decision['settings'],
            'selection_library_file':decision.get('library_file'),
            'stage':'library_lookup'},goto='library_lookup')

    def library_lookup(self, state):
        preferred=state.get('selection_library_file')
        result = self.lookup(state['confirmed_selection'],preferred_file=preferred) if preferred else self.lookup(state['confirmed_selection'])
        if result['status'] == 'ready':
            return Command(update={'lookup':result, 'formulation':result['formulation'],
                'stage':'function_space','functionspace_turns':[],'functionspace_message':'','functionspace_card':None,
                'functionspace_draft':None},goto='function_space')
        return Command(update={'lookup':result, 'stage':'generate_formulation'}, goto='generate_formulation')

    def generate_formulation(self, state):
        result = self.generate(state)
        return {'generation':result, 'formulation':result['formulation'], 'stage':'expert_review'}

    def expert_review(self, state):
        decision = interrupt({'stage':'expert_review'})
        if decision['action']=='message':
            return Command(update={'stage':'revise_formulation','review_message':decision['message'],
                'review_input':decision['formulation'],'settings':decision['settings']},goto='revise_formulation')
        # The approval endpoint has validated this exact edited object.
        files = self.save(state['confirmed_selection'], decision['formulation'])
        return Command(update={'formulation':decision['formulation'],'saved_files':files,'settings':decision['settings'],
            'stage':'function_space','functionspace_turns':[],'functionspace_message':'','functionspace_card':None,
            'functionspace_draft':None},goto='function_space')

    def revise_formulation(self, state):
        result = self.review(state)
        return {'review_turns':state.get('review_turns',[])+[result],
            'formulation':result['formulation'] if result['formulation'] is not None else state['review_input'],
            'stage':'expert_review'}

    def function_space(self,state):
        turn=self.propose_spaces(state)
        return {'functionspace_turns':state.get('functionspace_turns',[])+[turn],
            'functionspace_draft':turn['draft_card'],'stage':'function_space_review'}

    def function_space_review(self,state):
        decision = interrupt({'stage':'function_space_review','turn_index':len(state['functionspace_turns'])-1})
        if decision['action']=='message':
            return Command(update={'functionspace_message':decision['message'],'settings':decision['settings'],
                'stage':'function_space'},goto='function_space')
        return Command(update={'functionspace_card':decision['card'],'stage':'material_parameters',
            'settings':decision['settings'],'material_turns':[],'material_message':'',
            'material_selection':decision.get('selection',[]),'material_card':None,'material_draft':None},goto='material_parameters')

    def material_parameters(self,state):
        result=self.propose_materials(state)
        return {'mesh':result['mesh'],'material_turns':state.get('material_turns',[])+[result['turn']],
            'material_draft':result['turn']['draft_card'],'stage':'material_review'}

    def material_review(self,state):
        decision=interrupt({'stage':'material_review','turn_index':len(state['material_turns'])-1})
        if decision['action']=='message':
            return Command(update={'material_message':decision['message'],'material_selection':decision['selection'],
                'settings':decision['settings'],'stage':'material_parameters'},goto='material_parameters')
        if decision['action']=='choose':
            return Command(update={'material_turns':state.get('material_turns',[])+[decision['turn']],
                'material_draft':decision['turn']['draft_card'],'settings':decision['settings'],'stage':'material_review'},goto='material_review')
        return Command(update={'material_card':decision['card'],'stage':'boundary_parameter_selection',
            'settings':decision['settings'],'boundary_parameter_turns':[],
            'boundary_parameter_message':'','boundary_parameter_assessment':None},goto='boundary_parameter_selection')

    def boundary_parameter_selection(self,state):
        result=self.select_boundary_parameters(state)
        return {'mesh':result['mesh'],
            'boundary_parameter_turns':state.get('boundary_parameter_turns',[])+[result['turn']],
            'stage':'boundary_parameter_review'}

    def boundary_parameter_review(self,state):
        decision=interrupt({'stage':'boundary_parameter_review','turn_index':len(state['boundary_parameter_turns'])-1})
        if decision['action']=='choose':
            return Command(update={'boundary_parameter_turns':state['boundary_parameter_turns']+[decision['turn']],
                'boundary_parameter_message':'','settings':decision['settings'],'stage':'boundary_parameter_review'},goto='boundary_parameter_review')
        if decision['action']=='message':
            return Command(update={'boundary_parameter_message':decision['message'],'settings':decision['settings'],
                'stage':'boundary_parameter_selection'},goto='boundary_parameter_selection')
        return Command(update={'boundary_parameter_assessment':decision['assessment'],'stage':'boundary_values',
            'boundary_value_requirements':decision['requirements'],'boundary_value_draft':[],
            'boundary_value_turns':[],'boundary_value_message':'','boundary_value_card':None,
            'settings':decision['settings']},goto='boundary_values')

    def boundary_values(self,state):
        result=self.collect_boundary_values(state)
        return {'mesh':result['mesh'],'boundary_value_draft':result['turn']['response']['draft'],
            'boundary_value_turns':state.get('boundary_value_turns',[])+[result['turn']],
            'stage':'boundary_value_review'}

    def boundary_value_review(self,state):
        decision=interrupt({'stage':'boundary_value_review','turn_index':len(state['boundary_value_turns'])-1})
        if decision['action']=='update':
            return Command(update={'boundary_value_turns':state['boundary_value_turns']+[decision['turn']],
                'boundary_value_draft':decision['turn']['response']['draft'],'boundary_value_message':'',
                'settings':decision['settings'],'stage':'boundary_value_review'},goto='boundary_value_review')
        if decision['action']=='message':
            return Command(update={'boundary_value_message':decision['message'],'settings':decision['settings'],
                'stage':'boundary_values'},goto='boundary_values')
        return Command(update={'boundary_value_card':decision['card'],'stage':'solver_parameters',
            'solver_turns':[],'solver_message':'','solver_card':None,'solver_refresh':False,
            'settings':decision['settings']},goto='solver_parameters')

    def solver_parameters(self,state):
        result=self.propose_solvers(state)
        return {'solver_turns':state.get('solver_turns',[])+[result['turn']],
            'solver_environment':result['environment'],'solver_input_signature':result['signature'],
            'solver_refresh':False,'stage':'solver_review'}

    def solver_review(self,state):
        decision=interrupt({'stage':'solver_review','turn_index':len(state['solver_turns'])-1})
        if decision['action']=='update':
            return Command(update={'solver_turns':state['solver_turns']+[decision['turn']],
                'solver_message':'','settings':decision['settings'],'stage':'solver_review'},goto='solver_review')
        if decision['action'] in ('message','refresh'):
            return Command(update={'solver_message':decision.get('message',''),
                'solver_refresh':decision['action']=='refresh','solver_card':None,
                'solver_turns':[] if decision['action']=='refresh' else state['solver_turns'],
                'settings':decision['settings'],'stage':'solver_parameters'},goto='solver_parameters')
        return Command(update={'solver_card':decision['card'],'settings':decision['settings'],
            'stage':'complete'},goto=END)






    def close(self):
        self.connection.close()
