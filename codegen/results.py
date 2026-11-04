"""Save computed primary fields without changing coder prompts or solver values."""
import json
from math import prod
from pathlib import Path

import numpy as np
from common.coupling import normalized_coupling


def write_manifest(folder,value):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    path=folder/'manifest.json';temporary=folder/'manifest.tmp'
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temporary.replace(path)


def resolve_fields(namespace,unknowns,coupling_type):
    from dolfinx import fem
    from dolfinx.fem.petsc import LinearProblem,NonlinearProblem
    candidates={};seen=set()
    def add(function,path,solved=False,bound=None):
        key=id(function._cpp_object)
        item=candidates.setdefault(key,{'function':function,'paths':set(),'solved':False,'bound':set()})
        item['paths'].add(path);item['solved']|=solved
        if bound:item['bound'].add(bound)
    def walk(value,path=(),depth=0,solved=False):
        if isinstance(value,fem.Function):add(value,path,solved);return
        if id(value) in seen or depth>4:return
        seen.add(id(value))
        if isinstance(value,(LinearProblem,NonlinearProblem)):walk(value.u,path+('solution',),depth+1,True)
        elif isinstance(value,dict):
            for key,item in value.items():
                if isinstance(key,str) and not key.startswith('__'):walk(item,path+(key,),depth+1,solved)
        elif isinstance(value,(list,tuple)) and len(value)<=100:
            for i,item in enumerate(value):walk(item,path+(str(i),),depth+1,solved)
    walk(namespace,depth=-1)
    # The approved fully coupled space orders components in the declared unknown order.
    if normalized_coupling(coupling_type)=='multi_physics_fully_coupled':
        for item in list(candidates.values()):
            function=item['function'];space=function.function_space
            if not space.ufl_element().is_mixed or space.num_sub_spaces!=len(unknowns):continue
            parts=[function.sub(i).collapse() for i in range(len(unknowns))]
            if any(tuple(p.ufl_shape)!=tuple(u['shape']) for p,u in zip(parts,unknowns)):continue
            for part,unknown in zip(parts,unknowns):add(part,('mixed_solution',unknown['name']),item['solved'],unknown['name'])
    result={};errors={}
    for unknown in unknowns:
        name=unknown['name'];labels={name,str(unknown.get('quantity',name))};ranked=[]
        for item in candidates.values():
            function=item['function']
            if tuple(function.ufl_shape)!=tuple(unknown['shape']):continue
            specific=1000 if name in item['bound'] else 0
            if function.name in labels:specific+=100
            for path in item['paths']:
                if path and path[-1] in labels:specific=max(specific,180)
                if any(part in labels or any(part.startswith(label+'_') for label in labels) for part in path):specific=max(specific,130)
            solution_path=any(any('solution' in part or 'solved' in part for part in path) for path in item['paths'])
            score=specific+(400 if item['solved'] else 0)+(60 if solution_path else 0)
            if score:ranked.append((score,item))
        ranked.sort(key=lambda pair:pair[0],reverse=True)
        if not ranked:errors[name]="Could not find the correspondence between the computed unknown field and the result Function."
        elif len(ranked)>1 and ranked[0][0]==ranked[1][0]:errors[name]="There are multiple result fields with the same priority, so no automatic selection was made."
        else:result[name]=ranked[0][1]['function']
    return result,errors


def extract_field(function,shape):
    from dolfinx.plot import vtk_mesh
    if function.function_space.component():function=function.collapse()
    function.x.scatter_forward();space=function.function_space;mesh=space.mesh
    width=prod(shape or [1]);element=space.ufl_element()
    if element.degree==0:
        topology,cell_types,points=vtk_mesh(mesh)
        bs=space.dofmap.index_map_bs;rows=[]
        for cell in range(mesh.topology.index_map(mesh.topology.dim).size_local):
            indices=(space.dofmap.cell_dofs(cell)[:,None]*bs+np.arange(bs)).reshape(-1)
            rows.append(function.x.array[indices])
        values=np.asarray(rows).reshape(-1,width);association='cell'
    else:
        topology,cell_types,points=vtk_mesh(space)
        values=np.asarray(function.x.array).reshape(-1,width);association='point'
        if len(values)!=len(points):raise ValueError("The number of display nodes does not match the number of unknown field values.")
    if np.iscomplexobj(values):
        if np.any(values.imag!=0):raise ValueError("Real and imaginary display rules are required for complex unknown fields.")
        values=values.real
    if not np.isfinite(values).all():raise ValueError("The unknown field result contains NaN or infinity.")
    return {'topology':np.asarray(topology),'cell_types':np.asarray(cell_types),
        'points':np.asarray(points),'values':np.asarray(values),'association':association}


def export_unknowns(namespace,snapshot,folder):
    from mpi4py import MPI
    comm=MPI.COMM_WORLD;cards=snapshot['cards'];fs=cards['function_space']
    unknowns=fs['unknowns'];resolved,errors=resolve_fields(namespace,unknowns,fs['coupling_type'])
    folder=Path(folder)
    if comm.rank==0:(folder/'data').mkdir(parents=True,exist_ok=True)
    comm.barrier()
    report={'status':'exported','colormap':'coolwarm','geometry':'undeformed',
        'source':'solve_execution',
        'coordinate_unit':cards['mesh']['mesh'].get('target_coordinate_unit'),
        'value_units':'solver_values_without_conversion','fields':[]}
    for i,unknown in enumerate(unknowns):
        name=unknown['name'];local=None;error=errors.get(name)
        if error is None:
            try:local=extract_field(resolved[name],unknown['shape'])
            except Exception as exc:error=str(exc)
        pieces=comm.gather((local,error),root=0)
        if comm.rank!=0:continue
        item={'name':name,'quantity':unknown.get('quantity',name),'shape':unknown['shape'],
            'unit':unknown.get('unit'),'status':'exported','files':[],'images':[]}
        failures=[message for _,message in pieces if message]
        if failures:item.update(status='failed',error='; '.join(sorted(set(failures))))
        else:
            for rank,(data,_) in enumerate(pieces):
                path=folder/'data'/f'field_{i}_rank_{rank}.npz'
                np.savez_compressed(path,**data);item['files'].append(str(path.relative_to(folder)))
        report['fields'].append(item)
    if comm.rank==0:
        good=sum(f['status']=='exported' for f in report['fields'])
        report['status']='exported' if good==len(unknowns) else 'partial' if good else 'failed'
        write_manifest(folder,report)
