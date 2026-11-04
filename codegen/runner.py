"""Execute immutable web cards with compact API retrieval and stage-local repairs."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import subprocess

from codegen.cards import ROOT, STAGES, render


def write_json(path,value):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temporary.replace(path)


def procedure(source):
    import re
    text=source.split('Procedure:\n',1)[1].split('\nThe card is:',1)[0]
    result=[];current=None
    for line in text.splitlines():
        match=re.match(r'^(\d+)\.\s+(.*)',line)
        if match:
            if current:result.append(' '.join(current))
            current=[match[2].strip()]
        elif current and line.strip():current.append(line.strip())
        elif current:result.append(' '.join(current));current=None
    if current:result.append(' '.join(current))
    if not result:raise ValueError("Could not find the search item for the existing Procedure.")
    return result



def run(folder,backend=None):
    """A separate process owns coder globals, MPI child processes and this run's files."""
    folder=Path(folder);status=json.loads((folder/'status.json').read_text())
    snapshot=json.loads((folder/'input.json').read_text())
    config=snapshot['settings'];cards=snapshot['cards'];sources=snapshot['templates']
    stage_dir=None
    def update(**fields):
        status.update(fields,updated_at=time.time());write_json(folder/'status.json',status)
    try:
        update(status='running',message="Reading the API knowledge graph and saved embeddings.")
        if backend is None:
            from common.models import profile, credentials, OPENROUTER_URL
            selected=profile(config['model'])
            if selected['provider']=='openrouter':
                if not (key:=credentials('openrouter')):raise ValueError("Please set OPENROUTER_API_KEY or .openrouter_key.")
                os.environ['CODER_API_KEY']=key
                os.environ['CODER_BASE_URL']=OPENROUTER_URL
            else:
                os.environ.pop('CODER_API_KEY',None)
                os.environ.pop('CODER_BASE_URL',None)
            os.environ['CODER_MODEL']=config['model']
            if config['reasoning']=='default':os.environ.pop('CODER_REASONING',None)
            else:os.environ['CODER_REASONING']=config['reasoning']
            from coder import coder as C
            from common.client import client
            from knowledge_graph.retrieval import GraphRetriever
            retrieve=GraphRetriever.load(expected=config['retrieval'])
            backend=(retrieve,C,client)
        retrieve,C,client=backend
        C.EXECUTION_TIMEOUT=config['execution_timeout_seconds'];C.WORK=folder/'work'
        def trace(kind,**data):
            event={'kind':kind,'model':data.get('model'),'stage':status['current_stage']}
            if kind=='model_request':event.update(options=data.get('options'),extra_body=data.get('extra_body'))
            if kind=='model_response':event.update(usage=data.get('usage'),content_characters=len(data.get('content') or ''))
            with (folder/'model_usage.jsonl').open('a') as stream:stream.write(json.dumps(event)+'\n')
        C.TRACE=trace
        previous=''
        for number,(stage,filename) in enumerate(STAGES,1):
            stage_dir=folder/f'{number}_{stage}';stage_dir.mkdir(exist_ok=True)
            stage_status=status['stages'][number-1];stage_status.update(status='retrieving',attempt=0)
            update(current_stage=stage,message=f'{number}/5 {stage}: Searching the KG with Procedure.')
            source=sources[stage];queries=procedure(source)
            result=retrieve.retrieve(queries,client=client)
            graph,rankings=result.text,result.rankings
            node_count,edge_count=result.node_count,result.edge_count
            write_json(stage_dir/'graph_ids.json',result.original_ids)
            (stage_dir/'graph.json').write_text(graph+'\n')
            stage_status.update(node_count=node_count,edge_count=edge_count)
            write_json(stage_dir/'retrieval.json',{'queries':rankings,'node_count':node_count,
                'edge_count':edge_count,'settings':config.get('retrieval',{})})
            system,prompt,composed=render(source,cards[stage],graph,previous)
            (stage_dir/'prompt_used.txt').write_text(composed)
            C.PREFIX=previous+'\n' if previous else ''
            attempts=[];current_prompt=prompt
            for attempt in range(config['max_fixes']+1):
                stage_status.update(status='generating',attempt=attempt)
                update(message=f'{number}/5 {stage}: '+("Generating code" if not attempt else f'Error correction {attempt}times'))
                code=C.unfence(C.ask(current_prompt,system=system,max_tokens=32000))
                (stage_dir/f'attempt_{attempt}.py').write_text(code+'\n')
                stage_status['status']='executing';update(message=f'{number}/5 {stage}: Running the generated code.')
                def output(stdout,stderr):
                    (stage_dir/f'attempt_{attempt}.stdout.txt').write_text(stdout)
                    (stage_dir/f'attempt_{attempt}.stderr.txt').write_text(stderr)
                kwargs={'result_dir':folder} if stage=='solve' else {}
                passed,error=C.run_code(code,stage,output=output,**kwargs)
                (stage_dir/f'attempt_{attempt}.error.txt').write_text(error)
                attempts.append({'attempt':attempt,'passed':passed,'error':error})
                write_json(stage_dir/'attempts.json',attempts)
                if passed or attempt==config['max_fixes']:break
                current_prompt=prompt+'\n\n## Last attempt\n```python\n'+code+'\n```\n\n## Runtime error\n```text\n'+error+'\n```\nReturn complete corrected Python source for this stage only.'
                (stage_dir/f'repair_{attempt+1}_prompt.txt').write_text(current_prompt)
            (stage_dir/'final.py').write_text(code+'\n')
            stage_status.update(status='passed' if passed else 'failed',attempts=len(attempts))
            if not passed:
                update(status='failed',message=f'{stage} Could not resolve the execution error at the step.',error=error)
                return False
            previous=(previous+'\n'+code).strip();(folder/'accumulated.py').write_text(previous+'\n')
            update(message=f'{number}/5 {stage}: Execution succeeded')
        update(message="The analysis is complete. Generating the unknown field contour.")
        from codegen.results import write_manifest
        if (folder/'results/manifest.json').is_file():
            try:
                env={**os.environ,'PYTHONPATH':str(ROOT)+os.pathsep+os.environ.get('PYTHONPATH','')}
                with (folder/'results/render.log').open('w') as log:
                    result=subprocess.run([sys.executable,'-B','-m','codegen.contours','--run-dir',str(folder)],
                        cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
                if result.returncode:raise ValueError(f'Contour rendering process exit code: {result.returncode}')
            except Exception as error:
                manifest=json.loads((folder/'results/manifest.json').read_text())
                manifest.update(status='failed',error=str(error));write_manifest(folder/'results',manifest)
        else:write_manifest(folder/'results',{'status':'failed','error':"The computed unknown field data was not saved.",'fields':[]})
        update(status='succeeded',message="Completed step 5 code generation and the final solve execution.",error=None)
        return True
    except Exception as error:
        message=str(error)
        for key in ('OPENAI_API_KEY','CODER_API_KEY','OPENROUTER_API_KEY'):
            if os.environ.get(key):message=message.replace(os.environ[key],'[REDACTED]')
        if status.get('current_stage'):
            for item in status['stages']:
                if item['name']==status['current_stage']:item['status']='failed'
        update(status='failed',error=message,message="Failed to request coding and execution. You can check the logs and start a new run.")
        return False


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-dir',type=Path,required=True)
    args=parser.parse_args()
    sys.exit(0 if run(args.run_dir.resolve()) else 1)


if __name__=='__main__':main()
