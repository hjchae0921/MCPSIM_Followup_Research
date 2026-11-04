"""Probe the configured execution interpreter without importing MPI in the web server."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

_lock=threading.Lock()
MARKER='SOLVER_CAPABILITIES_JSON='


def discover(folder,refresh=False):
    executable=Path(os.environ.get('FENICSX_SOLVER_PYTHON') or sys.executable).absolute()
    script=Path(__file__).with_name('probe.py')
    key=hashlib.sha256(json.dumps([str(executable),executable.stat().st_mtime_ns,
        script.read_text(),os.environ.get('PETSC_DIR'),os.environ.get('PETSC_ARCH')]).encode()).hexdigest()
    path=Path(folder)/'solver_environment.json'
    with _lock:
        if path.is_file() and not refresh:
            try:
                saved=json.loads(path.read_text())
                if saved['cache_key']==key and time.time()-saved['checked_at']<3600:return saved['capabilities']
            except (ValueError,KeyError):pass
        try:
            result=subprocess.run([str(executable),'-B',str(script)],capture_output=True,text=True,
                timeout=120,check=False)
        except (OSError,subprocess.TimeoutExpired) as error:
            raise ValueError("Could not check the solver support information in the execution environment. Please check FENICSX_SOLVER_PYTHON and the PETSc installation.") from error
        lines=[line[len(MARKER):] for line in result.stdout.splitlines() if line.startswith(MARKER)]
        if result.returncode or not lines:
            raise ValueError("Failed to verify PETSc in the execution environment. Please check FENICSX_SOLVER_PYTHON and the PETSc installation, then try again.")
        value=json.loads(lines[-1])
        if not all(value.get(k) for k in ('ksp_types','pc_types','snes_types','line_search_types')):
            raise ValueError("Could not complete the list of solver types in the execution environment.")
        value['environment_id']=key
        path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_suffix('.tmp')
        temporary.write_text(json.dumps({'cache_key':key,'checked_at':time.time(),'capabilities':value},indent=2)+'\n')
        temporary.replace(path)
        return value
