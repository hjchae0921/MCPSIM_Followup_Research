"""Isolated PETSc type initialization checks; never solve the user's PDE."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import petsc4py
from petsc4py import PETSc

VERSION=3


def names(kind):
    return sorted({v for k,v in vars(kind).items() if not k.startswith('_') and isinstance(v,str)})


def search_names():
    config=petsc4py.get_config()
    root=Path(config.get('PETSC_DIR') or sys.prefix)
    paths=[root/'include/petscsnes.h',Path(sys.prefix)/'include/petscsnes.h']
    if config.get('PETSC_ARCH'):paths.insert(0,root/config['PETSC_ARCH']/'include/petscsnes.h')
    header=next((p for p in paths if p.is_file()),None)
    if header is None:raise RuntimeError("Could not find the installed PETSc petscsnes.h.")
    return sorted(set(re.findall(r'^#define\s+SNESLINESEARCH\w+\s+"([^"]+)"',header.read_text(),re.M)))


def worker(kind,candidates):
    for name in candidates:
        print('START='+name,flush=True)
        obj=None;matrix=None;key=None
        try:
            if kind=='line_search':
                obj=PETSc.SNES().create(comm=PETSc.COMM_SELF)
                obj.setType('newtonls');obj.setOptionsPrefix('authoring_probe_')
                key='authoring_probe_snes_linesearch_type'
                PETSc.Options()[key]=name;obj.setFromOptions()
            elif kind.startswith('factor_'):
                _,method,storage=kind.split('_')
                matrix=(PETSc.Mat().createAIJ if storage=='aij' else PETSc.Mat().createDense)([1,1],comm=PETSc.COMM_SELF)
                matrix[0,0]=1.;matrix.assemble()
                matrix.setOption(PETSc.Mat.Option.SYMMETRIC,True)
                matrix.setOption(PETSc.Mat.Option.SPD,True)
                obj=PETSc.PC().create(comm=PETSc.COMM_SELF)
                obj.setType(method);obj.setFactorSolverType(name)
                obj.setOperators(matrix);obj.setUp()
            else:
                obj={'ksp':PETSc.KSP,'pc':PETSc.PC,'snes':PETSc.SNES}[kind]().create(comm=PETSc.COMM_SELF)
                obj.setType(name)
            obj.destroy();obj=None
            if matrix is not None:matrix.destroy();matrix=None
            if key is not None:del PETSc.Options()[key];key=None
            print('OK='+name,flush=True)
        except PETSc.Error:
            # Some unsupported/partly initialized implementations cannot be safely destroyed.
            # Exit this disposable process and resume the remaining names in a fresh worker.
            os._exit(1)


def initialize(kind,candidates):
    accepted=[];remaining=list(candidates)
    while remaining:
        result=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--worker',kind,
            json.dumps(remaining)],capture_output=True,text=True,timeout=20)
        lines=result.stdout.splitlines()
        accepted.extend(line[3:] for line in lines if line.startswith('OK='))
        started=[line[6:] for line in lines if line.startswith('START=')]
        if result.returncode==0:break
        if not started:raise RuntimeError("Could not initialize the PETSc solver verification process.")
        remaining=remaining[remaining.index(started[-1])+1:]
    return accepted


def main():
    import dolfinx
    groups={'ksp':names(PETSc.KSP.Type),'pc':names(PETSc.PC.Type),'snes':names(PETSc.SNES.Type),
        'line_search':search_names()}
    factors=[name for name in names(PETSc.Mat.SolverType) if name=='petsc' or PETSc.Sys.hasExternalPackage(name)]
    for method in ('lu','cholesky','qr'):
        for storage in ('aij','dense'):groups[f'factor_{method}_{storage}']=factors
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures={kind:executor.submit(initialize,kind,values) for kind,values in groups.items()}
        supported={kind:future.result() for kind,future in futures.items()}
    packages=sorted({name for values in groups.values() for name in values if PETSc.Sys.hasExternalPackage(name)})
    result={'probe_version':VERSION,'dolfinx_version':dolfinx.__version__,
        'petsc_version':'.'.join(map(str,PETSc.Sys.getVersion())),
        'scalar_type':str(PETSc.ScalarType.__name__),'probe_mpi_size':PETSc.COMM_WORLD.size,
        'execution_mpi_size':None,'ksp_types':supported['ksp'],'pc_types':supported['pc'],
        'snes_types':supported['snes'],'line_search_types':supported['line_search'],
        'factor_solvers':sorted({name for key,values in supported.items() if key.startswith('factor_') for name in values}),
        'factor_support':{name:sorted(key.removeprefix('factor_') for key,values in supported.items()
            if key.startswith('factor_') and name in values) for name in factors
            if any(name in values for key,values in supported.items() if key.startswith('factor_'))},
        'external_packages':packages,
        'validation_scope':{'types':'creation_setType_and_cleanup_on_COMM_SELF',
            'factor_solvers':'factor_support_records_PC_setup_on_1x1_serial_CPU_AIJ_or_dense',
            'problem_matrix_compatibility':'not_checked','parallel_compatibility':'not_checked'}}
    print('SOLVER_CAPABILITIES_JSON='+json.dumps(result),flush=True)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':worker(sys.argv[2],json.loads(sys.argv[3]))
    else:main()
