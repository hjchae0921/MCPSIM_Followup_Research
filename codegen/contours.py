"""Render persisted finite-element unknowns to standalone coolwarm PNG figures."""
import argparse
import json
from math import prod
from pathlib import Path
import re

import numpy as np

from codegen.results import write_manifest


def render(run_dir):
    folder=Path(run_dir)/'results';path=folder/'manifest.json'
    if not path.is_file():
        write_manifest(folder,{'status':'failed','error':"There is no saved unknown field data.",'fields':[]});return
    report=json.loads(path.read_text())
    try:import pyvista as pv
    except ImportError:
        report.update(status='failed',error="Please install pyvista and matplotlib in the execution environment.");write_manifest(folder,report);return
    report['status']='rendering';write_manifest(folder,report)
    for i,item in enumerate(report['fields']):
        if not item.get('files'):continue
        try:
            grids=[];association=None
            for filename in item['files']:
                file=(folder/filename).resolve()
                if not file.is_relative_to(folder.resolve()):raise ValueError("Invalid result data path.")
                with np.load(file,allow_pickle=False) as data:
                    grid=pv.UnstructuredGrid(data['topology'],data['cell_types'],data['points'])
                    association=str(data['association']);values=data['values']
                    attributes=grid.point_data if association=='point' else grid.cell_data
                    if prod(item['shape'] or [1])>1:
                        attributes['magnitude']=np.linalg.norm(values,axis=1)
                        for component in range(prod(item['shape'])):attributes[f'component_{component}']=values[:,component]
                    else:attributes['value']=values[:,0]
                    grids.append(grid)
            grid=grids[0] if len(grids)==1 else grids[0].merge(grids[1:],merge_points=False)
            surface=grid.extract_surface(algorithm='dataset_surface')
            modes=[('magnitude','Magnitude')]+[(f'component_{j}',f'Component {j}') for j in range(prod(item['shape']))] if prod(item['shape'] or [1])>1 else [('value','Value')]
            images=[]
            for mode,label in modes:
                data=np.asarray((grid.point_data if association=='point' else grid.cell_data)[mode])
                low,high=float(data.min()),float(data.max());limits=(low,high)
                if low==high:
                    delta=max(abs(low),1.)*1e-6;limits=(low-delta,high+delta)
                plotter=pv.Plotter(off_screen=True,window_size=(1400,900))
                try:
                    plotter.set_background('white')
                    title=item['name'] if re.fullmatch(r'[\x20-\x7E]+',item['name']) else f'Field {i+1}'
                    plotter.add_text(title+' - '+label,font_size=15,color='#263750')
                    plotter.add_mesh(surface,scalars=mode,preference=association,cmap='coolwarm',clim=limits,
                        lighting=False,show_edges=False,interpolate_before_map=association=='point',
                        scalar_bar_args={'title':label+((' ('+item['unit']+')') if item.get('unit') else ' (solver values)'),
                            'fmt':'%.4g','color':'#263750','vertical':False,'position_x':.2,'width':.6})
                    plotter.add_axes();plotter.camera_position='iso';plotter.enable_parallel_projection();plotter.reset_camera()
                    filename=f'field_{i}_{mode}.png';plotter.screenshot(str(folder/filename))
                finally:plotter.close()
                images.append({'mode':mode,'label':label,'path':'results/'+filename,'min':low,'max':high})
            item.update(status='succeeded',images=images);item.pop('error',None)
        except Exception as error:item.update(status='failed',error=str(error))
        write_manifest(folder,report)
    count=sum(f['status']=='succeeded' for f in report['fields'])
    report['status']='succeeded' if count and count==len(report['fields']) else 'partial' if count else 'failed'
    write_manifest(folder,report)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-dir',type=Path,required=True)
    render(parser.parse_args().run_dir)
