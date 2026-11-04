"""Local HITL app: model, formulation, spaces, materials, boundary values and solver."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from urllib.parse import urlparse, unquote, quote
from openai import OpenAIError

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from web.host import HostService, UserError
from problem_selection_agent.service import ProblemSelectionService, SelectionError
from codegen.service import CodegenService, CodegenError

POST_ROUTES={
    '/api/selection/chat':'chat',
    '/api/selection/choose':'choose_selection',
    '/api/selection/confirm':'confirm',
    '/api/selection/approve':'approve',
    '/api/selection/continue':'continue_session',
    '/api/selection/confirm-functionspace':'confirm_spaces',
    '/api/selection/start-functionspace':'start_spaces',
    '/api/selection/confirm-materials':'confirm_materials',
    '/api/selection/choose-material':'choose_material',
    '/api/selection/update-materials':'update_materials',
    '/api/selection/start-materials':'start_materials',
    '/api/selection/start-boundary-parameter-selection':'start_boundary_parameter_selection',
    '/api/selection/confirm-boundary-parameter-selection':'confirm_boundary_parameter_selection',
    '/api/selection/choose-boundary-parameter-combination':'choose_boundary_parameter_combination',
    '/api/selection/confirm-boundary-values':'confirm_boundary_values',
    '/api/selection/start-boundary-values':'start_boundary_values',
    '/api/selection/update-boundary-values':'update_boundary_values',
    '/api/selection/start-solver':'start_solver',
    '/api/selection/choose-solver':'choose_solver',
    '/api/selection/update-solver':'update_solver',
    '/api/selection/confirm-solver':'confirm_solver',
    '/api/selection/refresh-solver':'refresh_solver',
}

class Handler(BaseHTTPRequestHandler):
    def send(self,status,value,content_type='application/json; charset=utf-8',filename=None):
        body=json.dumps(value,ensure_ascii=False).encode() if isinstance(value,dict) else value
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        if filename:self.send_header('Content-Disposition',"attachment; filename*=UTF-8''"+quote(filename))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path=urlparse(self.path).path
        static={'/':('index.html','text/html; charset=utf-8'),
                '/selection.js':('app.js','text/javascript; charset=utf-8'),
                '/selection.css':('style.css','text/css; charset=utf-8'),
                '/mesh-viewer.js':('mesh-viewer.js','text/javascript; charset=utf-8')}
        try:
            if path in static:
                name,mime=static[path]
                self.send(200,(HERE/'static'/name).read_bytes(),mime)
            elif path.startswith('/selection/vendor/'):
                base=HERE/'static/vendor';target=(base/path.removeprefix('/selection/vendor/')).resolve()
                types={'.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.woff2':'font/woff2'}
                if not target.is_relative_to(base) or not target.is_file() or target.suffix not in types:raise UserError("File not found.",404)
                self.send(200,target.read_bytes(),types[target.suffix])
            elif path=='/api/selection/config':
                value=self.server.selection.config()
                from knowledge_graph.retrieval import configuration
                value['codegen_retrieval']=configuration()
                self.send(200,value)
            elif path.startswith('/api/selection/session/'):
                self.send(200,self.server.selection.load(path.removeprefix('/api/selection/session/')))
            elif path.startswith('/api/mesh/'):
                mesh_id=path.removeprefix('/api/mesh/')
                self.server.host_service.mesh_info(mesh_id)
                self.send(200,(self.server.host_service.mesh_path(mesh_id)/'preview.json').read_bytes())
            elif path.startswith('/api/codegen/latest/'):
                self.send(200,self.server.codegen.latest(path.removeprefix('/api/codegen/latest/')))
            elif path.startswith('/api/codegen/run/'):
                parts=path.removeprefix('/api/codegen/run/').split('/')
                if len(parts)!=2:raise CodegenError("Please check the execution path.",404)
                self.send(200,{'run':self.server.codegen.get(*parts)})
            elif path.startswith('/api/codegen/artifact/'):
                parts=path.removeprefix('/api/codegen/artifact/').split('/',2)
                if len(parts)!=3:raise CodegenError("Please check the file path.",404)
                target=self.server.codegen.artifact(parts[0],parts[1],unquote(parts[2]))
                self.send(200,target.read_bytes(),'application/octet-stream',target.name)
            elif path.startswith('/api/codegen/image/'):
                parts=path.removeprefix('/api/codegen/image/').split('/',2)
                if len(parts)!=3:raise CodegenError("Please check the image path.",404)
                target=self.server.codegen.artifact(parts[0],parts[1],unquote(parts[2]))
                if target.suffix.lower()!='.png':raise CodegenError("A PNG image is required.",404)
                self.send(200,target.read_bytes(),'image/png')
            else:raise UserError("Page not found.",404)
        except (UserError,SelectionError,CodegenError) as error:self.send(error.status,{'error':str(error)})

    def do_POST(self):
        try:
            origin=self.headers.get('Origin')
            if origin and urlparse(origin).netloc!=self.headers.get('Host'):raise UserError("Please make the request from the current page.",403)
            if self.headers.get_content_type()!='application/json':raise UserError("A JSON request is required.",415)
            path=urlparse(self.path).path
            length=int(self.headers.get('Content-Length','0'))
            limit=56*1024*1024 if path=='/api/mesh' else 2*1024*1024
            if not 0<length<=limit:raise UserError("Please check the request size.",413)
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict):raise UserError("A JSON object is required.")
            if path=='/api/mesh':result=self.server.host_service.upload_mesh(data)
            elif path=='/api/codegen/preview':result=self.server.codegen.preview(data)
            elif path=='/api/codegen/start':result=self.server.codegen.start(data)
            elif path=='/api/codegen/cancel':result=self.server.codegen.cancel(data)
            elif path=='/api/codegen/contours':result=self.server.codegen.contours(data)
            elif path in POST_ROUTES:result=getattr(self.server.selection,POST_ROUTES[path])(data)
            else:raise UserError("Cannot find the request path.",404)
            self.send(200,result)
        except (UserError,SelectionError,CodegenError) as error:self.send(error.status,{'error':str(error),'session_id':getattr(error,'session_id',None)})
        except (ValueError,UnicodeDecodeError):self.send(400,{'error':"Please check the request format."})
        except OpenAIError as error:
            self.send(502,{'error':"Model API request failed: "+self.server.host_service.redact_error(error)})
        except Exception:self.send(500,{'error':"Server processing failed. Please check the save path and prompt file."})


class AppServer(ThreadingHTTPServer):
    def server_close(self):
        if hasattr(self,'codegen'):self.codegen.close()
        super().server_close()


def make_server(host='127.0.0.1',port=7861,data_dir=None,client=None,library_dir=None):
    server=AppServer((host,port),Handler)
    server.host_service=HostService(data_dir or ROOT/'data/authoring',client)
    server.selection=ProblemSelectionService(server.host_service.data_dir/'sessions',library_dir or ROOT/'library',server.host_service)
    server.codegen=CodegenService(server.host_service.data_dir.parent/'codegen/web',server.selection)
    return server


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=7861)
    parser.add_argument('--data-dir',type=Path)
    args=parser.parse_args()
    server=make_server(args.host,args.port,args.data_dir)
    print(f'Write physical specifications: http://{args.host}:{server.server_port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        server.server_close();server.selection.close();server.host_service.close()

if __name__=='__main__':main()
