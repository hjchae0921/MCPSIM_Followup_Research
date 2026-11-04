"""Check the six supplied meshes against their physical-group metadata."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from boundary_condition_agent.mesh import read_mesh

def main():
    folders=sorted(p for p in (ROOT/'benchmarks').glob('[0-9][0-9]_*') if p.is_dir())
    if len(folders)!=6:raise ValueError('Exactly six benchmark geometries are required.')
    rows=[]
    for folder in folders:
        for name in ['request.txt','model.msh','geometry.py','geometry.json','geometry.brep']:
            if not (folder/name).is_file():raise FileNotFoundError(folder/name)
        summary,_=read_mesh(folder/'model.msh','model.msh','mm')
        metadata=json.loads((folder/'geometry.json').read_text())
        for group in [*summary['volume_groups'],*summary['boundary_groups']]:
            if group['tags']!=metadata['groups'][group['name']]['tags']:
                raise ValueError('Physical-group mismatch: '+folder.name+'/'+group['name'])
        rows.append({'benchmark':folder.name,'nodes':summary['nodes'],'cells':summary['cells'],
            'volume_groups':len(summary['volume_groups']),'boundary_groups':len(summary['boundary_groups'])})
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
