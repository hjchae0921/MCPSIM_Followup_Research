"""Web run lifecycle and artifact access, independent of authoring checkpoints."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid

from codegen.cards import ROOT, STAGES, split, templates, source_signature
from codegen.runner import write_json
from solver_agent.agent import signature as solver_signature
from web.host import credentials
from common.models import MODEL_PROFILES, profile, reasoning_mode
from knowledge_graph.retrieval import configuration as retrieval_configuration

ACTIVE={'queued','running'}


class CodegenError(Exception):
    def __init__(self,message,status=400):super().__init__(message);self.status=status


class CodegenService:
    def __init__(self,folder,selection,launcher=None):
        self.folder=Path(folder).resolve();self.folder.mkdir(parents=True,exist_ok=True)
        self.selection=selection;self._guard=threading.RLock();self._processes={};self._renders={};self._cancelled=set();self._launcher=launcher or subprocess.Popen
        # A normal server shutdown stops its workers. If the server was killed, do not
        # claim an abandoned run is still being monitored or silently rerun paid calls.
        for path in self.folder.glob('*/*/status.json'):
            value=json.loads(path.read_text())
            if value.get('status') in ACTIVE:
                value.update(status='interrupted',message="The server restarted, and execution monitoring was interrupted. Please check the logs and start a new run.")
                write_json(path,value)
            task=path.parent/'results/task.json'
            if task.is_file() and json.loads(task.read_text()).get('status')=='running':
                write_json(task,{'status':'interrupted','error':"The server restarted. Please restart contour generation."})

    @staticmethod
    def valid_id(value):
        if not isinstance(value,str) or not re.fullmatch(r'[0-9a-f]{32}',value):raise CodegenError("Please check the run or conversation ID.")
        return value

    def path(self,session_id,run_id):
        return self.folder/self.valid_id(session_id)/self.valid_id(run_id)

    def prepare(self,session_id):
        session_id=self.valid_id(session_id)
        lock=self.selection.lock(session_id)
        if not lock.acquire(blocking=False):raise CodegenError("Please start coding after the specification request is complete.",409)
        try:
            state=self.selection.load(session_id)
            environment=self.selection.host.solver_environment()
            if not state.get('solver_card') or not state.get('solver_input_signature'):
                raise CodegenError("Please finalize the solver settings as well.",409)
            if state['solver_input_signature']!=solver_signature(state,environment):
                raise CodegenError("The finalized specification or execution environment has changed. Please review and finalize the solver again.",409)
            mesh_path=self.selection.host.mesh_path(state['mesh']['id'])/'model.msh'
            try:cards=split(state,mesh_path)
            except ValueError as error:raise CodegenError(str(error),409) from None
            return state,cards,mesh_path
        finally:lock.release()

    def preview(self,data):
        state,cards,_=self.prepare(data.get('session_id'))
        return {'cards':cards,'source_signature':source_signature(state),'stage_order':[n for n,_ in STAGES],
            'retrieval':retrieval_configuration()}

    @staticmethod
    def settings(data):
        model=data.get('model','gpt-5.4-mini')
        if model not in [p['id'] for p in MODEL_PROFILES]:raise CodegenError("Please choose the coder from the specified six models.")
        selected=profile(model)
        try:reasoning=reasoning_mode(model,data.get('reasoning'))
        except ValueError as error:raise CodegenError(str(error)) from None
        return {'model':model,'reasoning':reasoning,'provider':selected['provider'],
            'max_fixes':5,'execution_timeout_seconds':1200,
            'retrieval':retrieval_configuration()}

    def start(self,data):
        settings=self.settings(data);state,cards,mesh_path=self.prepare(data.get('session_id'))
        session_id=state['id'];run_id=uuid.uuid4().hex;folder=self.path(session_id,run_id)
        with self._guard:
            if any(process.poll() is None for process in [*self._processes.values(),*self._renders.values()]):
                raise CodegenError("There is an ongoing coding or analysis task. Please complete or stop it before running.",409)
            folder.mkdir(parents=True)
            (folder/'input').mkdir();shutil.copy2(mesh_path,folder/'input/mesh.msh')
            cards['mesh']['mesh']['path']=str(folder/'input/mesh.msh')
            sources=templates()
            for stage,_ in STAGES:
                (folder/'cards').mkdir(exist_ok=True);(folder/'templates').mkdir(exist_ok=True)
                write_json(folder/'cards'/f'{stage}.json',cards[stage])
                (folder/'templates'/f'{stage}.txt').write_text(sources[stage])
            write_json(folder/'input.json',{'cards':cards,'templates':sources,'settings':settings})
            status={'id':run_id,'session_id':session_id,'status':'queued','created_at':time.time(),'updated_at':time.time(),
                'source_signature':source_signature(state),'settings':settings,'current_stage':None,'error':None,
                'message':"Preparing to run coding.",
                'template_sha256':{name:hashlib.sha256(source.encode()).hexdigest() for name,source in sources.items()},
                'stages':[{'name':name,'status':'pending','attempt':0} for name,_ in STAGES]}
            write_json(folder/'status.json',status)
            executable=os.environ.get('FENICSX_SOLVER_PYTHON') or sys.executable
            env={**os.environ,'PYTHONUNBUFFERED':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
            if key:=credentials():env['OPENAI_API_KEY']=key
            if key:=credentials('openrouter'):env['OPENROUTER_API_KEY']=key
            log=(folder/'runner.log').open('w')
            try:
                process=self._launcher([executable,'-B','-m','codegen.runner','--run-dir',str(folder)],
                    cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            except OSError as error:
                status.update(status='failed',message="Could not start the coder execution process.",error=str(error))
                write_json(folder/'status.json',status)
                raise CodegenError(status['message'],503) from None
            finally:log.close()
            self._processes[(session_id,run_id)]=process
            thread=threading.Thread(target=self._monitor,args=(session_id,run_id,process),daemon=True)
            thread.start()
        return {'run':self.get(session_id,run_id)}

    def _monitor(self,session_id,run_id,process):
        code=process.wait()
        with self._guard:
            path=self.path(session_id,run_id)/'status.json'
            value=json.loads(path.read_text())
            if (session_id,run_id) in self._cancelled:
                value.update(status='cancelled',message="The user stopped the coding and analysis execution.")
                write_json(path,value)
            elif value['status'] in ACTIVE:
                value.update(status='failed',error=f'Coder process exit code: {code}',message="The execution process was interrupted. Please check runner.log.")
                write_json(path,value)

    def get(self,session_id,run_id):
        folder=self.path(session_id,run_id)
        with self._guard:
            if not (folder/'status.json').is_file():raise CodegenError("Could not find the coding execution.",404)
            value=json.loads((folder/'status.json').read_text())
        current=self.selection.load(session_id)
        value['stale']=value['source_signature']!=source_signature(current)
        value['artifacts']=[{'path':str(p.relative_to(folder)),'size':p.stat().st_size}
            for p in sorted(folder.rglob('*')) if p.is_file() and not p.is_symlink()
            and 'cache' not in p.relative_to(folder).parts and p.suffix!='.tmp']
        manifest=folder/'results/manifest.json';task=folder/'results/task.json'
        value['contours']=json.loads(manifest.read_text()) if manifest.is_file() else None
        value['contour_task']=json.loads(task.read_text()) if task.is_file() else None
        value['can_render_contours']=(folder/'accumulated.py').is_file() and all(s['status']=='passed' for s in value['stages']) and value['status'] not in ACTIVE
        return value

    def contours(self,data):
        session_id=data.get('session_id');run_id=data.get('run_id');folder=self.path(session_id,run_id)
        with self._guard:
            value=self.get(session_id,run_id)
            if not value['can_render_contours']:raise CodegenError("A code with the final analysis execution completed is required.",409)
            previous=self._renders.get((session_id,run_id))
            if previous is not None and previous.poll() is None:raise CodegenError("Generating contour.",409)
            if any(p.poll() is None for p in self._processes.values()):raise CodegenError("Please generate the contour after the ongoing analysis finishes.",409)
            results=folder/'results';results.mkdir(exist_ok=True)
            write_json(results/'task.json',{'status':'running','error':None})
            executable=os.environ.get('FENICSX_SOLVER_PYTHON') or sys.executable
            log=(results/'postprocess.log').open('w')
            env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
            for key in ('OPENAI_API_KEY','CODER_API_KEY','OPENROUTER_API_KEY'):env.pop(key,None)
            try:process=self._launcher([executable,'-B','-m','codegen.postprocess','--run-dir',str(folder)],
                cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            except OSError as error:
                write_json(results/'task.json',{'status':'failed','error':str(error)});raise CodegenError("Could not start the contour execution.",503) from None
            finally:log.close()
            self._renders[(session_id,run_id)]=process
            threading.Thread(target=self._monitor_render,args=(process,results),daemon=True).start()
        return {'run':self.get(session_id,run_id)}

    def _monitor_render(self,process,folder):
        code=process.wait()
        with self._guard:
            value=json.loads((folder/'task.json').read_text())
            if value['status']=='running':
                write_json(folder/'task.json',{'status':'failed','error':f'The contour process has ended ({code}). Please check postprocess.log.'})

    def latest(self,session_id):
        self.valid_id(session_id);self.selection.load(session_id)
        paths=list((self.folder/session_id).glob('*/status.json'))
        if not paths:return {'run':None}
        path=max(paths,key=lambda p:json.loads(p.read_text())['created_at'])
        return {'run':self.get(session_id,path.parent.name)}

    def cancel(self,data):
        session_id=data.get('session_id');run_id=data.get('run_id');folder=self.path(session_id,run_id)
        with self._guard:
            process=self._processes.get((session_id,run_id))
            if process is None or process.poll() is not None:raise CodegenError("There is no execution that can currently be stopped.",409)
            # Mark first; the process monitor must not replace cancellation with failure.
            self._cancelled.add((session_id,run_id))
            value=json.loads((folder/'status.json').read_text())
            value.update(status='cancelled',message="The user stopped the coding and analysis execution.",updated_at=time.time())
            write_json(folder/'status.json',value)
            try:os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            threading.Thread(target=self._kill_later,args=(process,),daemon=True).start()
        return {'run':self.get(session_id,run_id)}

    @staticmethod
    def _kill_later(process):
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass

    def artifact(self,session_id,run_id,name):
        folder=self.path(session_id,run_id).resolve();path=(folder/name).resolve()
        if not path.is_relative_to(folder) or path==folder or not path.is_file() or path.is_symlink():
            raise CodegenError("Could not find the execution result file.",404)
        if 'cache' in path.relative_to(folder).parts:raise CodegenError("This file is not eligible for result download.",404)
        return path

    def close(self):
        with self._guard:
            for (session_id,run_id),process in list(self._processes.items()):
                if process.poll() is None:
                    try:self.cancel({'session_id':session_id,'run_id':run_id})
                    except (CodegenError,ProcessLookupError):pass
            for (_, _),process in list(self._renders.items()):
                if process.poll() is None:
                    try:os.killpg(process.pid,signal.SIGTERM)
                    except ProcessLookupError:pass
                    threading.Thread(target=self._kill_later,args=(process,),daemon=True).start()
