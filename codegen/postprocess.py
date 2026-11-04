"""Create contours for saved runs, replaying old code only when no field data was saved."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from codegen.cards import ROOT
from codegen.contours import render
from codegen.runner import write_json


def run(folder):
    folder=Path(folder).resolve();results=folder/'results';results.mkdir(exist_ok=True)
    try:
        manifest=results/'manifest.json'
        saved=json.loads(manifest.read_text()) if manifest.is_file() else {}
        has_data=any((results/name).is_file() for f in saved.get('fields',[]) for name in f.get('files',[]))
        if not has_data:
            work=results/'replay_work';work.mkdir(exist_ok=True)
            env={**os.environ,'PYTHONPATH':str(ROOT)+os.pathsep+os.environ.get('PYTHONPATH',''),
                'XDG_CACHE_HOME':str(folder/'work/cache')}
            # Replaying an approved saved program requires no model or KG calls.
            for key in ('OPENAI_API_KEY','CODER_API_KEY','OPENROUTER_API_KEY'):env.pop(key,None)
            with (results/'replay.log').open('w') as log:
                result=subprocess.run([sys.executable,'-B','-m','codegen.execute','--script',str(folder/'accumulated.py'),
                    '--run-dir',str(folder)],cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
            if result.returncode:raise ValueError("Failed to rerun the saved code. Please check replay.log.")
            replayed=json.loads(manifest.read_text());replayed['source']='saved_code_replay'
            from codegen.results import write_manifest
            write_manifest(results,replayed)
        render(folder)
        value=json.loads((results/'manifest.json').read_text())
        write_json(results/'task.json',{'status':value['status'],'error':value.get('error')})
        return value['status'] in ('succeeded','partial')
    except Exception as error:
        write_json(results/'task.json',{'status':'failed','error':str(error)});return False


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-dir',type=Path,required=True)
    sys.exit(0 if run(parser.parse_args().run_dir) else 1)
