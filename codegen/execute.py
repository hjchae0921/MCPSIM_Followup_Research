"""Run the unchanged generated source once and capture its computed unknown fields."""
import argparse
import json
from pathlib import Path
import sys

from codegen.results import export_unknowns,write_manifest


def execute(script,run_dir):
    script=Path(script).resolve();run_dir=Path(run_dir).resolve()
    namespace={'__name__':'__main__','__file__':str(script),'__package__':None,'__spec__':None}
    previous_argv=sys.argv;previous_path=list(sys.path)
    sys.path.insert(0,str(script.parent));sys.argv=[str(script)]
    try:
        try:exec(compile(script.read_text(),str(script),'exec'),namespace)
        except SystemExit as error:
            if error.code not in (0,None):raise
        # An export error must never trigger changes to an already successful FEM solve.
        try:export_unknowns(namespace,json.loads((run_dir/'input.json').read_text()),run_dir/'results')
        except Exception as error:write_manifest(run_dir/'results',{'status':'failed','error':str(error),'fields':[]})
    finally:
        sys.argv=previous_argv;sys.path[:]=previous_path


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--script',type=Path,required=True)
    parser.add_argument('--run-dir',type=Path,required=True);args=parser.parse_args();execute(args.script,args.run_dir)
