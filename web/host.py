"""API credentials, model catalog and uploaded mesh storage for the web app."""
import base64
import binascii
import json
from pathlib import Path
import re
import threading
import uuid
from openai import OpenAI
from boundary_condition_agent.mesh import read_mesh
from common.models import credentials, profile, MODEL_PROFILES, FORMULATION_PROFILE, OPENROUTER_URL

ROOT=Path(__file__).resolve().parent.parent
DEFAULT_MODEL='gpt-5.4-mini'
DEFAULT_REASONING='low'

class UserError(Exception):
    def __init__(self, message, status=400, session_id=None):
        super().__init__(message)
        self.status = status
        self.session_id = session_id

class HostService:
    def __init__(self,data_dir,client=None,router_client=None):
        self.data_dir=Path(data_dir)
        self.data_dir.mkdir(parents=True,exist_ok=True)
        self._client=client
        self._router_client=router_client
        self._guard=threading.Lock()

    def close(self):
        if self._client is not None:self._client.close()
        if self._router_client is not None:self._router_client.close()

    def solver_environment(self,refresh=False):
        from solver_agent.environment import discover
        return discover(self.data_dir/'runtime',refresh)

    def client(self,model=DEFAULT_MODEL):
        provider=profile(model)['provider']
        attr='_router_client' if provider=='openrouter' else '_client'
        with self._guard:
            if getattr(self,attr) is None:
                key=credentials(provider)
                if not key:
                    setting="OPENROUTER_API_KEY or .openrouter_key" if provider=='openrouter' else "OPENAI_API_KEY or .openai_key"
                    raise UserError("Set "+setting+" on the server.",503)
                options={'api_key':key,'timeout':180,'max_retries':0}
                if provider=='openrouter':options['base_url']=OPENROUTER_URL
                setattr(self,attr,OpenAI(**options))
            return getattr(self,attr)

    def redact_error(self,error):
        message=str(error)
        for key in (credentials('openai'),credentials('openrouter'),
                    getattr(self._client,'api_key',None),getattr(self._router_client,'api_key',None)):
            if isinstance(key,str) and key:message=message.replace(key,'[REDACTED]')
        return message


    def config(self):
        configured={'openai':bool(self._client is not None or credentials()),
                    'openrouter':bool(self._router_client is not None or credentials('openrouter'))}
        return {"models": [p['id'] for p in MODEL_PROFILES], 'model_profiles':list(MODEL_PROFILES),
                'formulation_profile':FORMULATION_PROFILE,
                "default_model": DEFAULT_MODEL, "default_reasoning": DEFAULT_REASONING,
                "credential_configured": configured['openai'], 'provider_credentials':configured, "warning": "",
                "workflow": "langgraph"}


    def mesh_path(self, mesh_id):
        if not isinstance(mesh_id, str) or not re.fullmatch(r'[a-f0-9]{32}', mesh_id):
            raise UserError("Invalid mesh ID.")
        return self.data_dir / 'meshes' / mesh_id


    def mesh_info(self, mesh_id):
        path = self.mesh_path(mesh_id) / 'summary.json'
        with self._guard:
            if not path.is_file():
                raise UserError("Could not find the uploaded mesh.", 404)
            summary = json.loads(path.read_text())
            if summary.get('region_measures_version') != 1:
                summary,preview = read_mesh(self.mesh_path(mesh_id)/'model.msh',summary['filename'],summary.get('coordinate_unit') or '')
                path.write_text(json.dumps(summary,ensure_ascii=False))
                (self.mesh_path(mesh_id)/'preview.json').write_text(json.dumps(preview,separators=(',',':')))
        return {'id':mesh_id,'summary':summary}


    def upload_mesh(self, data):
        filename = data.get('filename', '')
        if not isinstance(filename, str) or not filename.lower().endswith('.msh'):
            raise UserError("Please select a .msh file.")
        unit = data.get('coordinate_unit', '')
        if unit not in ('', 'm', 'mm', 'cm', 'um'):
            raise UserError("Please check the length unit of the mesh coordinates.")
        try:
            content = base64.b64decode(data.get('content', ''), validate=True)
        except (ValueError, TypeError, binascii.Error):
            raise UserError("The mesh file data is invalid.") from None
        if not content or len(content) > 40 * 1024 * 1024:
            raise UserError("The mesh file must be within 40 MB.", 413)
        mesh_id = uuid.uuid4().hex
        folder = self.mesh_path(mesh_id)
        folder.mkdir(parents=True)
        path = folder / 'model.msh'
        path.write_bytes(content)
        try:
            summary, preview = read_mesh(path, Path(filename.replace('\\', '/')).name, unit)
        except Exception as error:
            raise UserError("Cannot read mesh: " + str(error)) from None
        (folder / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False))
        (folder / 'preview.json').write_text(json.dumps(preview, separators=(',', ':')))
        return {'id': mesh_id, 'summary': summary}


