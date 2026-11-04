"""Service for the persisted physical-specification authoring workflow."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import threading
import time
import uuid

from langgraph.types import Command
from openai import OpenAIError
from functionspace_agent import agent as space_agent
from material_agent import agent as material_agent
from boundary_condition_agent import parameter_selection
from boundary_condition_agent import values as boundary_values
from solver_agent import agent as solver_agent

from .catalog import Catalog, check_formulation
from .formulation import Formulation, FormulationReview
from .spec import normalized, reply_model
from .explanation import describe_selection
from .questions import fixed_values, present_question, provider_reply, select_question, wire_assessment, internal_assessment
from .workflow import Workflow
from . import library_matching
from common.units import normalize_boundary_reply, normalize_items
from common.models import MODEL_PROFILES, FORMULATION_PROFILE, profile, completion_options, reasoning_mode
from common.authoring import progress
from common.contracts import generation_schema
from common.provenance import sync as sync_field_status
from web.host import UserError

HERE = Path(__file__).resolve().parent
DEFAULT_SETTINGS = {'classifier_model':'gpt-5.4-mini','classifier_reasoning':'low',
                    'formulation_model':'gpt-5.5','formulation_reasoning':'medium',
                    'functionspace_model':'gpt-5.4-mini','functionspace_reasoning':'low',
                    'material_model':'gpt-5.4-mini','material_reasoning':'low',
                    'boundary_model':'gpt-5.4-mini','boundary_reasoning':'low',
                    'solver_model':'gpt-5.4-mini','solver_reasoning':'low'}


class SelectionError(Exception):
    def __init__(self, message, status=400, session_id=None):
        super().__init__(message)
        self.status, self.session_id = status, session_id


class ProblemSelectionService:
    def __init__(self, folder, library, host):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.catalog = Catalog(library)
        self.host = host
        self._guard = threading.Lock()
        self._locks = {}
        self.workflow = Workflow(self.folder, self.classify, self.catalog.lookup, self.generate,
            self.catalog.register,self.review,self.propose_spaces,self.propose_materials,self.select_boundary_parameters,self.collect_boundary_values,self.propose_solvers)

    def close(self):
        self.workflow.close()

    def config(self):
        available = self.host.config()
        return {**available,**DEFAULT_SETTINGS,'warning':available.get('warning',''),
                'workflow':'langgraph'}

    def settings(self,data,previous=None):
        overrides = data.get('settings',{})
        if not isinstance(overrides,dict):
            raise SelectionError('Model settings must be a JSON object.')
        value = {**DEFAULT_SETTINGS,**{k:v for k,v in (previous or {}).items() if k in DEFAULT_SETTINGS},**overrides}
        if set(value)!=set(DEFAULT_SETTINGS):
            raise SelectionError('Check the model setting keys.')
        for stage in ('classifier','formulation','functionspace','material','boundary','solver'):
            if stage=='formulation':selected=FORMULATION_PROFILE
            else:
                model=value[stage+'_model']
                allowed=[p['id'] for p in MODEL_PROFILES]
                if model not in allowed:
                    if stage+'_model' in overrides:raise SelectionError('Select one of the six supported models.')
                    model=DEFAULT_SETTINGS[stage+'_model']
                selected=profile(model)
            value[stage+'_model']=selected['id']
            key=stage+'_reasoning'
            if stage=='formulation':value[key]=selected['reasoning']
            else:
                supplied=key in overrides
                same_model=(previous or {}).get(stage+'_model')==selected['id']
                requested=overrides[key] if supplied else (previous or {}).get(key) if same_model else None
                try:value[key]=reasoning_mode(selected['id'],requested,strict=supplied)
                except ValueError as error:raise SelectionError(str(error)) from None
        return value

    @staticmethod
    def model_settings(state,stage):
        value = {**DEFAULT_SETTINGS,**state.get('settings',{})}
        model=value[stage+'_model']
        if stage=='formulation':selected=FORMULATION_PROFILE
        else:selected=profile(model if model in [p['id'] for p in MODEL_PROFILES] else DEFAULT_SETTINGS[stage+'_model'])
        mode=selected['reasoning'] if stage=='formulation' else reasoning_mode(selected['id'],value.get(stage+'_reasoning'),strict=False)
        return selected['id'],mode

    def lock(self, session_id):
        if not isinstance(session_id,str) or not re.fullmatch(r'[a-f0-9]{32}',session_id):
            raise SelectionError('Check the session ID.')
        with self._guard:
            lock = self._locks.setdefault(session_id,threading.Lock())
        return lock

    def snapshot(self, session_id):
        self.lock(session_id)
        return self.workflow.graph.get_state(self.workflow.config(session_id))

    def load(self, session_id):
        snapshot = self.snapshot(session_id)
        if not snapshot.values:
            raise SelectionError('The selection session was not found.',404)
        state = dict(snapshot.values)
        turns = []
        for turn in state.get('turns', []):
            reply = turn['response']
            if reply.get('kind') in ('proposal', 'registration_request') and 'spec' in reply:
                try:
                    explanation = describe_selection(reply['spec'])
                except (ValueError, KeyError, TypeError):
                    explanation = 'This stored selection requires validation before a review summary can be shown.'
                turn = {**turn, 'response': {**reply, 'explanation': explanation}}
            turns.append(turn)
        state['turns'] = turns
        boundary_unknowns=(state.get('functionspace_card') or {}).get('unknowns',())
        state['boundary_parameter_turns']=[{**turn,'response':parameter_selection.present_review(turn['response'],boundary_unknowns)}
            for turn in state.get('boundary_parameter_turns',[])]
        if state.get('boundary_parameter_assessment') is not None:
            state['boundary_parameter_assessment']=parameter_selection.canonical_assessment(state['boundary_parameter_assessment'],boundary_unknowns)
        if state.get('solver_card') and not state.get('solver_input_signature'):
            # Saved checkpoints may contain solver settings awaiting validation.
            state['solver_card']=None
        state['can_continue'] = bool(snapshot.next and not any(t.interrupts for t in snapshot.tasks))
        state['authoring_status']=progress(state)
        state['field_status']=sync_field_status(state)
        return state

    def _run(self, session_id, value):
        try:
            self.workflow.graph.invoke(value,self.workflow.config(session_id))
        except SelectionError as error:
            error.session_id = session_id
            raise
        except UserError as error:
            raise SelectionError(str(error),error.status,session_id) from None
        except OpenAIError as error:
            message = self.host.redact_error(error)
            raise SelectionError('Model API request failed: '+message,502,session_id) from None
        except ValueError as error:
            raise SelectionError(str(error),502,session_id) from None
        except Exception:
            raise SelectionError('The saved stage could not be completed. You can retry it.',500,session_id) from None
        finally:
            if self.snapshot(session_id).values:
                path = self.folder/session_id/'session.json'
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps(self.load(session_id),ensure_ascii=False,indent=2)+'\n')
        return self.load(session_id)

    def _ask(self, state, stage, model, messages, schema, sources, reasoning=None):
        mode=reasoning_mode(model,reasoning)
        request = {'model':model, 'messages':messages, **completion_options(model,reasoning=mode),
                   'response_format':{'type':'json_schema','json_schema':{'name':'selection_reply' if stage=='selection' else stage,
                                      'strict':True,'schema':generation_schema(schema)}}}
        folder = self.folder/state['id']/stage/uuid.uuid4().hex
        folder.mkdir(parents=True)
        (folder/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
        for name,source in sources.items():
            (folder/name).write_text(source)
        started = time.monotonic()
        response = self.host.client(model).chat.completions.create(**request)
        (folder/'response.json').write_text(response.model_dump_json(indent=2)+'\n')
        choice = response.choices[0]
        if choice.message.refusal:
            raise SelectionError('The model refused the request: '+choice.message.refusal,422)
        if choice.finish_reason != 'stop':
            raise SelectionError('The model response is incomplete. You can retry the saved stage.',502)
        meta = {'requested_model':model, 'served_model':response.model,
                'reasoning_effort':mode,
                'provider':profile(model)['provider'],
                'reasoning_request':request.get('extra_body',{}).get('reasoning'),
                'usage':response.usage.model_dump() if response.usage else None,
                'elapsed_seconds':round(time.monotonic()-started,2)}
        return choice.message.content or '',meta

    def _ask_validated(self,state,stage,model,messages,schema,sources,validate,reasoning=None):
        """Give one invalid model answer back for repair; only validated answers reach review."""
        errors=[]
        for attempt in range(2):
            raw,meta=self._ask(state,stage,model,messages,schema,sources,reasoning=reasoning)
            try:
                value=validate(raw)
            except ValueError as error:
                if attempt:raise
                errors.append(str(error))
                messages=[*messages,{'role':'assistant','content':raw},
                    {'role':'user','content':'The output failed card schema or consistency validation. Error: '+str(error)+
                     '\nPreserve the user request and approved inputs. Correct the error and return the full response using the same output schema. '
                     'Do not review, select, or approve on behalf of the user.'}]
            else:
                if errors:meta.update(validation_repairs=attempt,validation_errors=errors)
                return value,meta

    def classify(self,state):
        choices = self.catalog.choices()
        dimension = state['mesh']['summary']['dimension']
        answers = state.get('selection_answers', {})
        candidates = self.catalog.candidates(dimension,answers)
        Reply = reply_model(choices['types'],choices['models'],dimension,answers,wire=True)
        source = (HERE/'selection_prompt.txt').read_text()
        header,marker,user = source.partition('=== USER MESSAGE ===')
        if not marker:
            raise ValueError('The selection prompt is missing its USER MESSAGE delimiter.')
        catalog = {'types':choices['types'],'models':choices['models']}
        substitutions = {'INITIAL_REQUEST':state['initial_request'],'MESH_DIMENSION':str(dimension),
                         'LIBRARY_CATALOG':json.dumps(catalog,ensure_ascii=False)}
        for name in substitutions:
            if user.count('{{'+name+'}}') != 1:
                raise ValueError('Check the selection prompt placeholder: '+name)
        user = re.sub(r'\{\{([A-Z_]+)\}\}',lambda match:substitutions[match[1]],user).strip()
        messages = [{'role':'system','content':header.removeprefix('=== SYSTEM MESSAGE ===').strip()},
                    {'role':'user','content':user}]
        for i,turn in enumerate(state['turns']):
            if i:
                messages.append({'role':'user','content':turn['message']})
            messages.append({'role':'assistant','content':json.dumps({'response':wire_assessment(provider_reply(turn,dimension))},ensure_ascii=False)})
        if state['turns']:
            messages.append({'role':'user','content':state['user_message']})
        if answers:
            messages.append({'role':'user','content':'[User-selected values]\n'+json.dumps(answers,ensure_ascii=False)})
        model,reasoning = self.model_settings(state,'classifier')
        def validate(raw):
            payload=library_matching.enforce_answers(json.loads(raw),answers)
            assessment=internal_assessment(Reply.model_validate_json(json.dumps(payload)).model_dump(mode='json',by_alias=True)['response'])
            coupling=assessment['spec']['problem']['coupling']
            if coupling['type']=='single_physics' and coupling['dependencies'] is None:
                coupling['dependencies']=[{'from':None,'to':None}]
            value=select_question(assessment)
            if value is None:
                if assessment['spec']['problem']['dimension'] != dimension:
                    raise ValueError('The selection dimension does not match the mesh dimension.')
            return value,assessment
        (value,assessment),meta=self._ask_validated(state,'selection',model,messages,Reply.model_json_schema(),
            {'selection_prompt.txt':source},validate,reasoning=reasoning)
        if value is None:
            initial=assessment
            if candidates:
                Review=library_matching.response_model(choices['types'],choices['models'],dimension,answers,candidates,wire=True)
                review_messages,review_sources=library_matching.messages(state,assessment,candidates)
                def validate_review(raw):
                    payload=library_matching.enforce_answers(json.loads(raw),answers)
                    reviewed=internal_assessment(Review.model_validate_json(json.dumps(payload)).model_dump(mode='json',by_alias=True)['response'])
                    return library_matching.resolve(reviewed,candidates,self.catalog,answers)
                (assessment,value,found),review_meta=self._ask_validated(state,'selection_library_review',model,
                    review_messages,Review.model_json_schema(),review_sources,validate_review,reasoning=reasoning)
                meta={**meta,'initial_assessment':initial,'draft_usage':meta.get('usage'),'library_review':review_meta,
                    'usage':library_matching.total_usage(meta.get('usage'),review_meta.get('usage')),
                    'elapsed_seconds':round(meta.get('elapsed_seconds',0)+review_meta.get('elapsed_seconds',0),2)}
            else:
                assessment,value,found=library_matching.resolve(assessment,[],self.catalog,answers)
                meta['library_review']={'skipped':True,'reason':'no_candidates_for_confirmed_constraints'}
            if value is None:
                value={'kind':'proposal','spec':assessment['spec'],'explanation':describe_selection(assessment['spec'])}
                if found['status']=='ready':
                    meta['library_match']=found['file']
                else:
                    value.update(kind='registration_request',reason='No formulation in the library matches the reviewed user requirements.')
        return {'message':state['user_message'],'response':value,'assessment':assessment,**meta}

    def generate(self,state):
        source = (HERE/'formulation_prompt.txt').read_text()
        # This is the entire user payload. Do not include raw chat, geometry, or runtime metadata.
        user = json.dumps(state['confirmed_selection'],ensure_ascii=False)
        messages = [{'role':'system','content':source}, {'role':'user','content':user}]
        model,reasoning = self.model_settings(state,'formulation')
        raw,meta = self._ask(state,'formulation',model,messages,Formulation.model_json_schema(),
                            {'formulation_prompt.txt':source},reasoning=reasoning)
        value = Formulation.model_validate_json(raw).model_dump()
        return {'formulation':value,**meta}

    def review(self,state):
        source = (HERE/'formulation_prompt.txt').read_text()
        review_source = (HERE/'formulation_review_prompt.txt').read_text()
        messages = [{'role':'system','content':source+'\n\n'+review_source},
            {'role':'user','content':json.dumps({'selection':state['confirmed_selection']},ensure_ascii=False)}]
        for turn in state.get('review_turns',[]):
            messages.append({'role':'user','content':json.dumps({'formulation':turn['input_formulation'],
                'feedback':turn['message']},ensure_ascii=False)})
            messages.append({'role':'assistant','content':json.dumps({'explanation':turn['explanation'],
                'formulation':turn['formulation']},ensure_ascii=False)})
        messages.append({'role':'user','content':json.dumps({'formulation':state['review_input'],
            'feedback':state['review_message']},ensure_ascii=False)})
        model,reasoning = self.model_settings(state,'formulation')
        raw,meta = self._ask(state,'formulation_review',model,messages,FormulationReview.model_json_schema(),
            {'formulation_prompt.txt':source,'formulation_review_prompt.txt':review_source},reasoning=reasoning)
        value = FormulationReview.model_validate_json(raw).model_dump()
        if value['formulation'] is not None:
            value['formulation'] = check_formulation(value['formulation'],state['confirmed_selection'])
        return {'message':state['review_message'],'input_formulation':state['review_input'],**value,**meta}

    def propose_spaces(self,state):
        messages,sources = space_agent.messages(state['initial_request'],state['confirmed_selection'],
            state['formulation'],state.get('functionspace_turns',[]),state.get('functionspace_message',''))
        Reply = space_agent.response_model(state['confirmed_selection'])
        model,reasoning = self.model_settings(state,'functionspace')
        def validate(raw):
            assessment=Reply.model_validate_json(raw).model_dump(mode='json',by_alias=True)['response']
            draft=space_agent.assemble_draft(assessment,state['confirmed_selection'])
            value=space_agent.select_question(assessment,draft)
            if value is None:
                value={'explanation':assessment['explanation'],
                    'proposed_card':space_agent.check_card(draft,state['confirmed_selection'])}
            else:
                value.update(explanation=assessment['explanation'],draft_card=draft)
            return value,assessment,draft
        (value,assessment,draft),meta=self._ask_validated(state,'function_space',model,messages,Reply.model_json_schema(),sources,validate,reasoning=reasoning)
        return {'message':state.get('functionspace_message',''),'response':value,
            'assessment':assessment,'draft_card':draft,**meta}

    def propose_materials(self,state):
        mesh=self.host.mesh_info(state['mesh']['id'])
        selected=material_agent.validate_selection(state.get('material_selection',[]),mesh['summary'])
        messages,sources=material_agent.messages(state['initial_request'],state['confirmed_selection'],
            state['formulation'],mesh['summary'],selected,state.get('material_turns',[]),state.get('material_message',''))
        Reply=material_agent.response_model(state['formulation'],mesh['summary'])
        model,reasoning=self.model_settings(state,'material')
        previous=(state.get('field_status') or {}).get('material',{})
        texts=[state['initial_request'],state.get('material_message','')]+[
            turn['message'] for turn in state.get('material_turns',[]) if turn.get('message') and not turn.get('origin')]
        def validate(raw):
            value=Reply.model_validate_json(raw).model_dump(mode='json',by_alias=True)['response']
            assessment,proposal=material_agent.to_assessment(value,state['formulation'],mesh['summary'])
            fields=material_agent.field_provenance(assessment,previous,texts,state.get('material_message',''))
            assessment['user_inputs']=material_agent.verified_user_inputs(assessment,fields)
            return (*material_agent.evaluate(assessment,state['formulation'],mesh['summary'],field_status=fields),fields,proposal)
        if not state['formulation']['constitutive_parameters']:
            value,assessment,draft,notes=material_agent.evaluate(material_agent.empty_assessment(state['formulation']),state['formulation'],mesh['summary'])
            fields={}
            proposal=None
            meta={'served_model':'server','origin':'empty_parameters'}
        else:
            (value,assessment,draft,notes,fields,proposal),meta=self._ask_validated(state,'material_parameters',model,messages,Reply.model_json_schema(),sources,validate,reasoning=reasoning)
        turn={'message':state.get('material_message',''),'selection':selected,'response':value,
            'assessment':assessment,'proposal':proposal,'draft_card':draft,'unit_normalizations':notes,'field_status':fields,**meta}
        return {'mesh':mesh,'turn':turn}

    def select_boundary_parameters(self,state):
        mesh=self.host.mesh_info(state['mesh']['id'])
        messages,sources=parameter_selection.messages(state,mesh['summary'])
        unknowns=state['functionspace_card']['unknowns']
        Reply=parameter_selection.response_model(state['formulation'],mesh['summary'],unknowns,wire=True)
        model,reasoning=self.model_settings(state,'boundary')
        def validate(raw):
            return parameter_selection.check_reply(parameter_selection.internal_reply(Reply.model_validate_json(raw).model_dump(mode='json',by_alias=True),unknowns),
                state['formulation'],mesh['summary'],unknowns)
        value,meta=self._ask_validated(state,'boundary_parameter_selection',model,messages,
            Reply.model_json_schema(),sources,validate,reasoning=reasoning)
        return {'mesh':mesh,'turn':{'message':state.get('boundary_parameter_message',''),'response':value,**meta}}

    def collect_boundary_values(self,state):
        mesh=self.host.mesh_info(state['mesh']['id'])
        rows=boundary_values.requirements(state['boundary_parameter_assessment'],state['formulation'],
            mesh['summary'],state['functionspace_card']['unknowns'])
        if rows!=state['boundary_value_requirements']:
            raise ValueError('The approved conditions do not match the numerical input requirements. Review the condition assessment.')
        if not rows:
            return {'mesh':mesh,'turn':{'message':'','origin':'empty_values',
                'response':{'explanation':'No boundary, source, or Dirichlet values require input.','draft':[],'question':None}}}
        messages,sources=boundary_values.messages(state,mesh['summary'],rows)
        Reply=boundary_values.response_model(rows);model,reasoning=self.model_settings(state,'boundary')
        def validate(raw):
            value=Reply.model_validate_json(raw).model_dump(mode='json')
            notes=normalize_boundary_reply(value,mesh['summary'])
            return boundary_values.check_reply(value,rows),notes
        (value,notes),meta=self._ask_validated(state,'boundary_values',model,messages,Reply.model_json_schema(),sources,validate,reasoning=reasoning)
        return {'mesh':mesh,'turn':{'message':state.get('boundary_value_message',''),'response':value,'unit_normalizations':notes,**meta}}

    def propose_solvers(self,state):
        environment=self.host.solver_environment(refresh=state.get('solver_refresh',False))
        messages,sources=solver_agent.messages(state,environment)
        Reply=solver_agent.response_model(state['confirmed_selection'],environment)
        model,reasoning=self.model_settings(state,'solver')
        def validate(raw):
            return solver_agent.check_reply(Reply.model_validate_json(raw).model_dump(mode='json')['response'],
                state['confirmed_selection'],environment)
        value,meta=self._ask_validated(state,'solver_parameters',model,messages,Reply.model_json_schema(),sources,validate,reasoning=reasoning)
        return {'environment':environment,'signature':solver_agent.signature(state,environment),
            'turn':{'message':state.get('solver_message',''),'response':value,**meta}}




    @staticmethod
    def check_review_index(data,state):
        index = data.get('review_turn_index',0)
        if type(index) is not int or index!=len(state.get('review_turns',[])):
            raise SelectionError('Review the latest draft before proceeding.',409)

    def chat(self,data):
        message = data.get('message')
        if not isinstance(message,str) or not message.strip() or len(message)>12000:
            raise SelectionError('Enter a request between 1 and 12,000 characters.')
        session_id = data.get('session_id') or uuid.uuid4().hex
        lock = self.lock(session_id)
        if not lock.acquire(blocking=False):
            raise SelectionError('A response is being prepared.',409)
        try:
            if not data.get('session_id'):
                if not data.get('mesh_id'):
                    raise SelectionError('Load a .msh file first so its dimension can be verified.')
                mesh = self.host.mesh_info(data['mesh_id'])
                state = {'id':session_id,'created_at':datetime.now(timezone.utc).isoformat(),'stage':'selection',
                         'settings':self.settings(data),
                         'initial_request':message.strip(),'user_message':message.strip(),'mesh':mesh,'turns':[],
                         'selection_answers':{},
                         'selection_draft':None,
                         'confirmed_selection':None,'lookup':None,'generation':None,'formulation':None,'saved_files':None,
                         'review_turns':[],'review_message':'','review_input':None,
                         'functionspace_turns':[],'functionspace_message':'','functionspace_card':None,'functionspace_draft':None,
                         'material_turns':[],'material_message':'','material_selection':[],'material_card':None,'material_draft':None}
                state.update(boundary_parameter_turns=[],
                    boundary_parameter_message='',boundary_parameter_assessment=None)
                return self._run(session_id,state)
            state = self.load(session_id)
            if state['can_continue']:
                raise SelectionError('Retry the failed stage first.',409)
            if state['stage']=='boundary_parameter_review':
                self.check_boundary_parameter_index(data,state)
                return self._run(session_id,Command(resume={'action':'message','message':message.strip(),
                    'settings':self.settings(data,state.get('settings'))}))
            if state['stage']=='boundary_value_review':
                self.check_boundary_value_index(data,state)
                return self._run(session_id,Command(resume={'action':'message','message':message.strip(),
                    'settings':self.settings(data,state.get('settings'))}))
            if state['stage']=='solver_review':
                self.check_solver_index(data,state)
                return self._run(session_id,Command(resume={'action':'message','message':message.strip(),
                    'settings':self.settings(data,state.get('settings'))}))
            if state['stage']=='boundary_review':
                raise SelectionError('Start the boundary and source parameter assessment first.',409)
            if state['stage']=='material_review':
                self.check_material_index(data,state)
                mesh=self.host.mesh_info(state['mesh']['id'])
                try:
                    selected=material_agent.validate_selection(data.get('material_selection',[]),mesh['summary'])
                except ValueError as error:
                    raise SelectionError(str(error)) from None
                return self._run(session_id,Command(resume={'action':'message','message':message.strip(),
                    'selection':selected,'settings':self.settings(data,state.get('settings'))}))
            if state['stage']=='function_space_review':
                self.check_space_index(data,state)
                return self._run(session_id,Command(resume={'action':'message','message':message.strip(),
                    'settings':self.settings(data,state.get('settings'))}))
            if state['stage']=='expert_review':
                self.check_review_index(data,state)
                try:
                    formulation = Formulation.model_validate(data.get('formulation',state['formulation'])).model_dump()
                except ValueError as error:
                    raise SelectionError('Check the formulation JSON to review: '+str(error)) from None
                return self._run(session_id,Command(resume={'action':'message','message':message.strip(),
                    'formulation':formulation,'settings':self.settings(data,state.get('settings'))}))
            if state['stage'] != 'selection_review':
                raise SelectionError('Conversation is available during selection, formulation review, function-space, and material setup.',409)
            return self._run(session_id,Command(resume={'action':'message','message':message.strip(),
                'settings':self.settings(data,state.get('settings'))}))
        finally:
            lock.release()

    def choose_selection(self,data):
        """Record an actual enum value; a choice does not approve the complete spec."""
        session_id = data.get('session_id')
        lock = self.lock(session_id)
        if not lock.acquire(blocking=False):
            raise SelectionError('Wait for the response to finish before selecting.',409)
        try:
            state = self.load(session_id)
            if state['stage'] != 'selection_review' or state['can_continue']:
                raise SelectionError('No question is currently available for selection.',409)
            index = data.get('turn_index')
            if type(index) is not int or index != len(state['turns']) - 1:
                raise SelectionError('Select an option from the latest question.',409)
            reply = state['turns'][-1]['response']
            target = reply.get('fixed_target')
            if reply.get('kind') != 'question' or target not in fixed_values():
                raise SelectionError('This is not a server-generated fixed-choice question.',409)
            choice = data.get('choice_index')
            options = present_question({'target':target,'explanation':reply['explanation']})['options']
            if type(choice) is not int or not 0 <= choice < len(options):
                raise SelectionError('Select one of the options provided for this question.')
            option = options[choice]
            answers = {**state.get('selection_answers',{}), target:option['value']}
            return self._run(session_id,Command(resume={'action':'message',
                'message':option['label']+': '+option['description'],'selection_answers':answers,
                'settings':self.settings(data,state.get('settings'))}))
        finally:
            lock.release()

    def confirm(self,data):
        session_id = data.get('session_id')
        lock = self.lock(session_id)
        if not lock.acquire(blocking=False):
            raise SelectionError('Wait for the response to finish before confirming.',409)
        try:
            state = self.load(session_id)
            if state['stage'] != 'selection_review' or state['can_continue']:
                raise SelectionError('No selection specification is currently available for confirmation.',409)
            index = data.get('turn_index')
            if type(index) is not int or index != len(state['turns'])-1:
                raise SelectionError('Confirm the latest proposed selection specification.',409)
            response = state['turns'][-1]['response']
            if response['kind']=='question':
                raise SelectionError('Answer the clarification question first.',409)
            spec = normalized(response['spec'])
            library_file=state['turns'][-1].get('library_match')
            if library_file and self.catalog.lookup(spec,preferred_file=library_file)['status']!='ready':
                raise SelectionError('The selected library entry has changed. Review the selection again.',409)
            return self._run(session_id,Command(resume={'action':'confirm','spec':spec,
                'library_file':library_file,'settings':self.settings(data,state.get('settings'))}))
        finally:
            lock.release()

    def approve(self,data):
        session_id = data.get('session_id')
        lock = self.lock(session_id)
        if not lock.acquire(blocking=False):
            raise SelectionError('A request is currently being processed.',409)
        try:
            state = self.load(session_id)
            if state['stage']!='expert_review' or state['can_continue']:
                raise SelectionError('No new formulation is available for review.',409)
            if data.get('expert_approved') is not True:
                raise SelectionError('Explicit expert review approval is required.')
            self.check_review_index(data,state)
            try:
                formulation = check_formulation(data.get('formulation'),state['confirmed_selection'])
            except ValueError as error:
                raise SelectionError(str(error)) from None
            return self._run(session_id,Command(resume={'action':'approve','formulation':formulation,
                'settings':self.settings(data,state.get('settings'))}))
        finally:
            lock.release()

    @staticmethod
    def check_space_index(data,state):
        index = data.get('functionspace_turn_index')
        if type(index) is not int or index!=len(state.get('functionspace_turns',[]))-1:
            raise SelectionError('Review the latest function-space proposal.',409)

    def confirm_spaces(self,data):
        session_id = data.get('session_id')
        lock = self.lock(session_id)
        if not lock.acquire(blocking=False):
            raise SelectionError('A function-space response is being prepared.',409)
        try:
            state = self.load(session_id)
            if state['stage']!='function_space_review' or state['can_continue']:
                raise SelectionError('No function-space specification is currently available for confirmation.',409)
            self.check_space_index(data,state)
            response = state['functionspace_turns'][-1]['response']
            if 'proposed_card' not in response:
                raise SelectionError('Answer the function-space clarification question first.',409)
            card = space_agent.check_card(response['proposed_card'],state['confirmed_selection'])
            return self._run(session_id,Command(resume={'action':'confirm','card':card,
                'settings':self.settings(data,state.get('settings')),'selection':data.get('material_selection',[])}))
        finally:
            lock.release()

    def start_spaces(self,data):
        session_id = data.get('session_id')
        lock = self.lock(session_id)
        if not lock.acquire(blocking=False):
            raise SelectionError('A request is currently being processed.',409)
        try:
            state = self.load(session_id)
            if state['stage']!='complete' or state.get('functionspace_card') or self.snapshot(session_id).next:
                raise SelectionError('Start from an existing session that has completed formulation approval only.',409)
            check_formulation(state['formulation'],state['confirmed_selection'])
            return self._run(session_id,Command(update={'stage':'function_space',
                'settings':self.settings(data,state.get('settings')),'functionspace_turns':[],
                'functionspace_message':'','functionspace_card':None,'functionspace_draft':None},goto='function_space'))
        finally:
            lock.release()

    def continue_session(self,data):
        session_id = data.get('session_id')
        lock = self.lock(session_id)
        if not lock.acquire(blocking=False):
            raise SelectionError('A request is currently being processed.',409)
        try:
            snapshot = self.snapshot(session_id)
            if not snapshot.next or any(t.interrupts for t in snapshot.tasks):
                raise SelectionError('This stage is waiting for user confirmation.',409)
            settings = self.settings(data,snapshot.values.get('settings'))
            retry_node=snapshot.next[0]
            update={'settings':settings,'retry_node':retry_node}
            if retry_node in ('boundary_plan','boundary_conditions'):
                update.update(stage='boundary_parameter_selection',retry_node='boundary_parameter_selection')
            self.workflow.graph.update_state(self.workflow.config(session_id),
                update,as_node='retry_checkpoint')
            return self._run(session_id,None)
        finally:
            lock.release()

    @staticmethod
    def check_material_index(data,state):
        index=data.get('material_turn_index')
        if type(index) is not int or index!=len(state.get('material_turns',[]))-1:
            raise SelectionError('Review the latest material parameter proposal.',409)

    def confirm_materials(self,data):
        session_id=data.get('session_id');lock=self.lock(session_id)
        if not lock.acquire(blocking=False):
            raise SelectionError('A material parameter response is being prepared.',409)
        try:
            state=self.load(session_id)
            if state['stage']!='material_review' or state['can_continue']:
                raise SelectionError('No material parameter specification is currently available for confirmation.',409)
            self.check_material_index(data,state)
            response=state['material_turns'][-1]['response']
            if 'proposed_card' not in response:
                raise SelectionError('Answer the clarification questions about material values, units, and regions first.',409)
            card=material_agent.check_card(response['proposed_card'],state['formulation'],
                self.host.mesh_info(state['mesh']['id'])['summary'])
            return self._run(session_id,Command(resume={'action':'confirm','card':card,
                'settings':self.settings(data,state.get('settings'))}))
        finally:
            lock.release()

    def choose_material(self,data):
        session_id=data.get('session_id');lock=self.lock(session_id)
        if not lock.acquire(blocking=False):
            raise SelectionError('Wait for the material response before selecting a candidate.',409)
        try:
            state=self.load(session_id)
            if state['stage']!='material_review' or state['can_continue']:
                raise SelectionError('No material candidate is available for selection.',409)
            self.check_material_index(data,state)
            previous=state['material_turns'][-1];reply=previous['response']
            choice=data.get('option_index')
            options=reply.get('options',[])
            if reply.get('question_type') not in ('choice','recommendation') or type(choice) is not int or not 0<=choice<len(options):
                raise SelectionError('Select a candidate from the latest material question.')
            mesh=self.host.mesh_info(state['mesh']['id'])
            assessment=material_agent.provider_reply(previous,state['formulation'],mesh['summary'])
            index=reply.get('ambiguity_index',0)
            if type(index) is not int or not 0<=index<len(assessment['ambiguities']):
                raise SelectionError('The material question is no longer available.',409)
            candidates=assessment['ambiguities'][index]['options'] or []
            candidate_index=options[choice].get('candidate_index',choice)
            if type(candidate_index) is not int or not 0<=candidate_index<len(candidates):
                raise SelectionError('The material candidate is no longer available.',409)
            fields=previous.get('field_status',(state.get('field_status') or {}).get('material',{}))
            updated=material_agent.apply_candidate(assessment,candidates[candidate_index],fields)
            fields=material_agent.selection_status(updated,candidates[candidate_index],fields)
            value,updated,draft,notes=material_agent.evaluate(updated,state['formulation'],mesh['summary'],allow_generic=True,field_status=fields)
            turn={'message':'Selected material candidate: '+candidates[candidate_index]['label'],
                'origin':'recommendation_choice','served_model':'server','selection':previous.get('selection',[]),
                'response':value,'assessment':updated,'proposal':previous.get('proposal'),'draft_card':draft,'unit_normalizations':notes,'field_status':fields}
            return self._run(session_id,Command(resume={'action':'choose','turn':turn,
                'settings':self.settings(data,state.get('settings'))}))
        except ValueError as error:
            raise SelectionError(str(error)) from None
        finally:
            lock.release()

    def update_materials(self,data):
        from material_agent.schema import MaterialValueInput
        session_id=data.get('session_id');lock=self.lock(session_id)
        if not lock.acquire(blocking=False):
            raise SelectionError('Wait for the material response before editing values.',409)
        try:
            state=self.load(session_id)
            if state['stage']!='material_review' or state['can_continue']:
                raise SelectionError('No material draft is currently available for editing.',409)
            self.check_material_index(data,state)
            item=MaterialValueInput.model_validate(data.get('input')).model_dump()
            previous=state['material_turns'][-1]
            mesh=self.host.mesh_info(state['mesh']['id'])
            raw=material_agent.provider_reply(previous,state['formulation'],mesh['summary'])
            candidate={'updates':[{**item,'regions':None}]}
            fields=previous.get('field_status',(state.get('field_status') or {}).get('material',{}))
            updated=material_agent.apply_candidate(raw,candidate,fields,user_edit=True)
            fields=material_agent.selection_status(updated,candidate,fields,source='user_input')
            value,updated,draft,notes=material_agent.evaluate(updated,state['formulation'],mesh['summary'],allow_generic=True,field_status=fields)
            turn={'message':'Updated '+item['parameter']+' value and unit.','origin':'value_input','served_model':'server',
                'selection':previous.get('selection',[]),'response':value,'assessment':updated,'proposal':previous.get('proposal'),
                'draft_card':draft,'unit_normalizations':notes,'field_status':fields}
            return self._run(session_id,Command(resume={'action':'choose','turn':turn,
                'settings':self.settings(data,state.get('settings'))}))
        except ValueError as error:
            raise SelectionError(str(error)) from None
        finally:
            lock.release()

    def start_materials(self,data):
        session_id=data.get('session_id');lock=self.lock(session_id)
        if not lock.acquire(blocking=False):
            raise SelectionError('A request is currently being processed.',409)
        try:
            state=self.load(session_id)
            if state['stage']!='complete' or not state.get('functionspace_card') or state.get('material_card') or self.snapshot(session_id).next:
                raise SelectionError('Start from an existing session that has completed function-space approval only.',409)
            return self._run(session_id,Command(update={'stage':'material_parameters','material_turns':[],
                'material_message':'','material_selection':data.get('material_selection',[]),'material_card':None,'material_draft':None,
                'settings':self.settings(data,state.get('settings'))},goto='material_parameters'))
        finally:
            lock.release()


    @staticmethod
    def check_boundary_parameter_index(data,state):
        index=data.get('boundary_parameter_turn_index')
        if type(index) is not int or index!=len(state.get('boundary_parameter_turns',[]))-1:
            raise SelectionError('Review the latest parameter requirements assessment.',409)

    def start_boundary_parameter_selection(self,data):
        session_id=data.get('session_id');lock=self.lock(session_id)
        if not lock.acquire(blocking=False):raise SelectionError('A request is currently being processed.',409)
        try:
            state=self.load(session_id)
            if not state.get('material_card') or state['stage'] not in ('complete','boundary_review','solver_review','boundary_parameter_review','boundary_value_review') or state['can_continue']:
                raise SelectionError('Confirm material parameters before assessing required boundary and source parameters.',409)
            # Store this runtime check separately from approved cards and dialogue.
            self.workflow.graph.update_state(self.workflow.config(session_id),{
                **self.clear_solver(state),
                'stage':'boundary_parameter_selection',
                'boundary_parameter_message':'','boundary_parameter_assessment':None,
                'boundary_value_history':state.get('boundary_value_history',[])+([{'assessment':state.get('boundary_parameter_assessment'),
                    'card':state['boundary_value_card']}] if state.get('boundary_value_card') else []),
                'boundary_value_turns':[],'boundary_value_draft':[],'boundary_value_requirements':[],'boundary_value_card':None,
                'retry_node':'boundary_parameter_selection','settings':self.settings(data,state.get('settings'))},as_node='retry_checkpoint')
            return self._run(session_id,None)
        finally:lock.release()

    def confirm_boundary_parameter_selection(self,data):
        session_id=data.get('session_id');lock=self.lock(session_id)
        if not lock.acquire(blocking=False):raise SelectionError('A request is currently being processed.',409)
        try:
            state=self.load(session_id)
            if state['stage']!='boundary_parameter_review' or state['can_continue']:
                raise SelectionError('No parameter requirements assessment is available for review.',409)
            self.check_boundary_parameter_index(data,state)
            reply=state['boundary_parameter_turns'][-1]['response']
            if 'dirichlet_conditions' not in reply['assessment']:
                raise SelectionError('Review the condition assessment again, including Dirichlet conditions.',409)
            assessment=parameter_selection.check_assessment(reply['assessment'],state['formulation'],
                self.host.mesh_info(state['mesh']['id'])['summary'],state['functionspace_card']['unknowns'])
            if not parameter_selection.ready(assessment) or reply['question']:
                raise SelectionError('Resolve questions about required conditions and their regions first.',409)
            rows=boundary_values.requirements(assessment,state['formulation'],self.host.mesh_info(state['mesh']['id'])['summary'],state['functionspace_card']['unknowns'])
            return self._run(session_id,Command(resume={'action':'confirm','assessment':assessment,'requirements':rows,
                'settings':self.settings(data,state.get('settings'))}))
        finally:lock.release()

    def choose_boundary_parameter_combination(self,data):
        session_id=data.get('session_id');lock=self.lock(session_id)
        if not lock.acquire(blocking=False):raise SelectionError('A request is currently being processed.',409)
        try:
            state=self.load(session_id)
            if state['stage']!='boundary_parameter_review' or state['can_continue']:
                raise SelectionError('No recommended combination is currently available for selection.',409)
            self.check_boundary_parameter_index(data,state)
            previous=state['boundary_parameter_turns'][-1]
            recommendations=previous['response'].get('recommendations',[])
            index=data.get('recommendation_index')
            if type(index) is not int or not 0<=index<len(recommendations):
                raise SelectionError('Select one of the displayed recommended combinations.')
            proposal=recommendations[index]
            if 'dirichlet_conditions' not in proposal['assessment']:
                raise SelectionError('Request a new recommended combination that includes Dirichlet conditions first.',409)
            assessment=parameter_selection.check_assessment(proposal['assessment'],state['formulation'],
                self.host.mesh_info(state['mesh']['id'])['summary'],state['functionspace_card']['unknowns'])
            if not parameter_selection.ready(assessment):
                raise SelectionError('Select a recommended combination with resolved requirements and regions.',409)
            turn={'message':'Selected recommended combination: '+proposal['label'],'origin':'recommendation_choice',
                'response':parameter_selection.present_review({'explanation':proposal['description'],
                    'assessment':assessment,'recommendations':[]})}
            return self._run(session_id,Command(resume={'action':'choose','turn':turn,
                'settings':self.settings(data,state.get('settings'))}))
        finally:lock.release()

    @staticmethod
    def check_boundary_value_index(data,state):
        index=data.get('boundary_value_turn_index')
        if type(index) is not int or index!=len(state.get('boundary_value_turns',[]))-1:
            raise SelectionError('Review the latest value and unit proposal.',409)

    def confirm_boundary_values(self,data):
        session_id=data.get('session_id');lock=self.lock(session_id)
        if not lock.acquire(blocking=False):raise SelectionError('A request is currently being processed.',409)
        try:
            state=self.load(session_id)
            if state['stage']!='boundary_value_review' or state['can_continue']:
                raise SelectionError('No boundary, source, or Dirichlet values are currently available for confirmation.',409)
            self.check_boundary_value_index(data,state)
            reply=state['boundary_value_turns'][-1]['response']
            if reply['question'] is not None:raise SelectionError('Resolve clarification questions about values and units first.',409)
            rows=boundary_values.requirements(state['boundary_parameter_assessment'],state['formulation'],
                self.host.mesh_info(state['mesh']['id'])['summary'],state['functionspace_card']['unknowns'])
            card=boundary_values.card(reply['draft'],rows)
            return self._run(session_id,Command(resume={'action':'confirm','card':card,
                'settings':self.settings(data,state.get('settings'))}))
        finally:lock.release()

    def update_boundary_values(self,data):
        session_id=data.get('session_id');lock=self.lock(session_id)
        if not lock.acquire(blocking=False):raise SelectionError('A request is currently being processed.',409)
        try:
            state=self.load(session_id)
            if state['stage']!='boundary_value_review' or state['can_continue']:
                raise SelectionError('No value and unit draft is currently available for input.',409)
            self.check_boundary_value_index(data,state)
            try:draft=boundary_values.check_draft(data.get('draft',[]),state['boundary_value_requirements'])
            except ValueError as error:raise SelectionError(str(error)) from None
            notes=normalize_items(draft,self.host.mesh_info(state['mesh']['id'])['summary'],'id')
            missing=[item['id'] for item in draft if item['value'] is None or item['unit'] is None]
            question={'question_type':'input','question':'Enter the values and units of unresolved items.','options':[]} if missing else None
            turn={'message':'Applied table values and units','origin':'value_input','unit_normalizations':notes,'response':{
                'explanation':'The entered values and units have been applied. Review them, then confirm or revise.',
                'draft':draft,'question':question}}
            return self._run(session_id,Command(resume={'action':'update','turn':turn,
                'settings':self.settings(data,state.get('settings'))}))
        finally:lock.release()

    def start_boundary_values(self,data):
        session_id=data.get('session_id');lock=self.lock(session_id)
        if not lock.acquire(blocking=False):raise SelectionError('A request is currently being processed.',409)
        try:
            state=self.load(session_id)
            if state['stage'] not in ('complete','solver_review') or not state.get('boundary_parameter_assessment') or state['can_continue']:
                raise SelectionError('Confirm the required conditions and their regions first.',409)
            if 'dirichlet_conditions' not in state['boundary_parameter_assessment']:
                raise SelectionError('Review the condition assessment again, including Dirichlet conditions.',409)
            rows=boundary_values.requirements(state['boundary_parameter_assessment'],state['formulation'],
                self.host.mesh_info(state['mesh']['id'])['summary'],state['functionspace_card']['unknowns'])
            self.workflow.graph.update_state(self.workflow.config(session_id),{'stage':'boundary_values',
                **self.clear_solver(state),
                'boundary_value_requirements':rows,'boundary_value_message':'','boundary_value_turns':[],
                'boundary_value_history':state.get('boundary_value_history',[])+([{'assessment':state['boundary_parameter_assessment'],
                    'card':state['boundary_value_card']}] if state.get('boundary_value_card') else []),
                'boundary_value_card':None,'settings':self.settings(data,state.get('settings')),'retry_node':'boundary_values'},as_node='retry_checkpoint')
            return self._run(session_id,None)
        finally:lock.release()

    @staticmethod
    def clear_solver(state):
        history=state.get('solver_history',[])
        if state.get('solver_turns') or state.get('solver_card'):
            history=history+[{'card':state.get('solver_card'),'turns':state.get('solver_turns',[]),
                'environment':state.get('solver_environment'),'signature':state.get('solver_input_signature')}]
        return {'solver_card':None,'solver_turns':[],'solver_message':'','solver_input_signature':'',
            'solver_environment':{},'solver_history':history,'solver_refresh':False}

    @staticmethod
    def check_solver_index(data,state):
        index=data.get('solver_turn_index')
        if type(index) is not int or index!=len(state.get('solver_turns',[]))-1 or index<0:
            raise SelectionError('Review the latest solver proposal.',409)

    def start_solver(self,data):
        session_id=data.get('session_id');lock=self.lock(session_id)
        if not lock.acquire(blocking=False):raise SelectionError('A request is currently being processed.',409)
        try:
            state=self.load(session_id)
            if state['stage']!='complete' or not state.get('boundary_value_card') or state['can_continue']:
                raise SelectionError('Confirm boundary, source, and Dirichlet values before configuring the solver.',409)
            self.workflow.graph.update_state(self.workflow.config(session_id),{
                **self.clear_solver(state),'stage':'solver_parameters','retry_node':'solver_parameters',
                'settings':self.settings(data,state.get('settings'))},as_node='retry_checkpoint')
            return self._run(session_id,None)
        finally:lock.release()

    def solver_action(self,data,action):
        session_id=data.get('session_id');lock=self.lock(session_id)
        if not lock.acquire(blocking=False):raise SelectionError('A request is currently being processed.',409)
        try:
            state=self.load(session_id)
            if state['stage']!='solver_review' or state['can_continue']:
                raise SelectionError('No solver settings are currently available for review.',409)
            self.check_solver_index(data,state)
            settings=self.settings(data,state.get('settings'))
            if action=='refresh':
                return self._run(session_id,Command(resume={'action':'refresh','settings':settings}))
            environment=self.host.solver_environment()
            if state.get('solver_input_signature')!=solver_agent.signature(state,environment):
                raise SelectionError('The approved cards or runtime environment have changed. Refresh the environment and request solver recommendations.',409)
            reply=state['solver_turns'][-1]['response']
            if action=='choose':
                index=data.get('recommendation_index');items=reply.get('recommendations',[])
                if type(index) is not int or not 0<=index<len(items):raise SelectionError('Select one of the displayed solver recommendations.')
                item=items[index];card=item['card'];message='Selected solver recommendation: '+item['label'];explanation=item['description']
            elif action=='manual':
                card=data.get('card');message='Applied solver JSON edits';explanation='The entered solver settings have been applied. Review them before confirming.'
            else:
                if 'proposed_card' not in reply:raise SelectionError('Select a recommended configuration or answer the solver clarification question first.',409)
                card=reply['proposed_card']
            try:card=solver_agent.check_card(card,state['confirmed_selection'],environment)
            except ValueError as error:raise SelectionError(str(error)) from None
            if action=='confirm':
                return self._run(session_id,Command(resume={'action':'confirm','card':card,'settings':settings}))
            turn={'message':message,'origin':action,'response':{'explanation':explanation,'proposed_card':card}}
            return self._run(session_id,Command(resume={'action':'update','turn':turn,'settings':settings}))
        finally:lock.release()

    def choose_solver(self,data):return self.solver_action(data,'choose')
    def update_solver(self,data):return self.solver_action(data,'manual')
    def confirm_solver(self,data):return self.solver_action(data,'confirm')
    def refresh_solver(self,data):return self.solver_action(data,'refresh')








