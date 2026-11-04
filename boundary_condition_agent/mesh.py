"""Read uploaded Gmsh meshes and extract actual tagged boundary triangles."""
from collections import Counter
import threading

import gmsh
import numpy as np

_lock = threading.Lock()

def element_measures(kind, entity):
    _, _, order, _, _, _ = gmsh.model.mesh.getElementProperties(int(kind))
    points, weights = gmsh.model.mesh.getIntegrationPoints(int(kind), 'Gauss'+str(2*order+2))
    _, determinants, _ = gmsh.model.mesh.getJacobians(int(kind), points, int(entity))
    return np.abs(np.asarray(determinants).reshape(-1,len(weights))) @ np.asarray(weights)

_faces = {
    4: [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)],
    8: [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
    6: [(0, 1, 2), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)],
    5: [(0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)],
}


def read_mesh(path, filename, coordinate_unit=''):
    with _lock:
        gmsh.initialize(interruptible=False)
        try:
            gmsh.option.setNumber('General.Terminal', 0)
            gmsh.open(str(path))
            if gmsh.model.getDimension() != 3:
                raise ValueError('The boundary viewer supports three-dimensional volume meshes.')
            tags, coords, _ = gmsh.model.mesh.getNodes()
            xyz = np.asarray(coords).reshape(-1, 3)
            if not len(tags) or not np.isfinite(xyz).all():
                raise ValueError('The mesh has no valid finite coordinates.')
            node_index = {int(tag): i for i, tag in enumerate(tags)}
            volume_groups, cell_regions = [], {}
            for dim, tag in gmsh.model.getPhysicalGroups(3):
                region_nodes, region_cells = set(), []
                volume = 0.0
                for entity in gmsh.model.getEntitiesForPhysicalGroup(dim, tag):
                    kinds, ids, connectivity = gmsh.model.mesh.getElements(3,int(entity))
                    for kind, element_ids, nodes in zip(kinds,ids,connectivity):
                        volume += float(element_measures(kind,entity).sum())
                        region_cells.extend(int(item) for item in element_ids)
                        region_nodes.update(int(item) for item in nodes)
                if not region_cells:
                    continue
                points = xyz[[node_index[item] for item in sorted(region_nodes)]]
                volume_groups.append({'name':gmsh.model.getPhysicalName(dim,tag) or f'Physical_3_{tag}',
                    'dim':3,'tags':[int(tag)],'elements':len(region_cells),'volume':volume,
                    'bounds':points.min(axis=0).tolist()+points.max(axis=0).tolist(),
                    'centroid':points.mean(axis=0).tolist()})
                for cell in region_cells:
                    cell_regions.setdefault(cell,[]).append(int(tag))
            counts = Counter()
            face_regions = {}
            kinds, element_tags, arrays = gmsh.model.mesh.getElements(3)
            cells = sum(len(x) for x in element_tags)
            for kind, ids, array in zip(kinds,element_tags,arrays):
                _, _, _, width, _, primary = gmsh.model.mesh.getElementProperties(int(kind))
                if primary not in _faces:
                    raise ValueError('This volume element type is not supported by the boundary viewer.')
                for cell,row in zip(ids,np.asarray(array).reshape(-1,width)):
                    for face in _faces[primary]:
                        key = tuple(sorted(int(row[n]) for n in face))
                        counts[key] += 1
                        if counts[key]==1:
                            face_regions[key]=cell_regions.get(int(cell),[])
                        else:
                            face_regions.pop(key,None)
            if not cells:
                raise ValueError('The mesh contains no volume elements.')
            entity_groups = {}
            names = {}
            for dim, tag in gmsh.model.getPhysicalGroups(2):
                key = int(tag)
                names[key] = gmsh.model.getPhysicalName(dim, tag) or f'Physical_{dim}_{tag}'
                for entity in gmsh.model.getEntitiesForPhysicalGroup(dim, tag):
                    entity_groups.setdefault(int(entity), []).append(key)
            group_triangles = {tag: [] for tag in names}
            group_elements = Counter()
            group_areas = Counter()
            overlaps = set()
            triangles, used = [], set()
            interfaces = 0
            for _, entity in gmsh.model.getEntities(2):
                kinds, _, arrays = gmsh.model.mesh.getElements(2, entity)
                for kind, array in zip(kinds, arrays):
                    areas = element_measures(kind,entity)
                    _, _, _, width, _, primary = gmsh.model.mesh.getElementProperties(int(kind))
                    if primary not in (3, 4):
                        raise ValueError('Boundary elements must be triangles or quadrilaterals.')
                    for row,area in zip(np.asarray(array).reshape(-1, width),areas):
                        corners = [int(n) for n in row[:primary]]
                        incidence = counts.get(tuple(sorted(corners)), 0)
                        if incidence == 2:
                            interfaces += 1
                            continue
                        if incidence != 1:
                            continue
                        groups = entity_groups.get(entity, [])
                        for first in groups:
                            for second in groups:
                                if first < second:
                                    overlaps.add((first,second))
                        local = [[0, 1, 2]] if primary == 3 else [[0, 1, 2], [0, 2, 3]]
                        for tri in local:
                            indices = [node_index[corners[n]] for n in tri]
                            used.update(indices)
                            triangles.append({'nodes':indices,'tags':groups,
                                'volume_tags':face_regions.get(tuple(sorted(corners)),[])})
                            for tag in groups:
                                group_triangles[tag].append(indices)
                        for tag in groups:
                            group_elements[tag] += 1
                            group_areas[tag] += float(area)
            if not used:
                raise ValueError('No surface mesh is connected to the volume mesh. Save the mesh with boundary elements.')
            ordered = sorted(used)
            compact = {old: new for new, old in enumerate(ordered)}
            surface_coords = xyz[ordered]
            groups = []
            for tag, name in names.items():
                if not group_triangles[tag]:
                    continue
                indices = sorted({n for tri in group_triangles[tag] for n in tri})
                points = xyz[indices]
                groups.append({'name': name, 'dim': 2, 'tags': [tag], 'elements': group_elements[tag], 'area':group_areas[tag],
                               'bounds': points.min(axis=0).tolist() + points.max(axis=0).tolist(),
                               'centroid': points.mean(axis=0).tolist()})
            scale = {'m':1.0,'mm':1e-3,'cm':1e-2,'um':1e-6}.get(coordinate_unit)
            for group in groups:
                group['area_si'] = group['area']*scale**2 if scale is not None else None
            for group in volume_groups:
                group['volume_si'] = group['volume']*scale**3 if scale is not None else None
            summary = {'filename': filename, 'dimension': 3, 'coordinate_unit': coordinate_unit or None, 'region_measures_version':1,
                       'overlapping_boundary_tags':[list(pair) for pair in sorted(overlaps)],
                       'bounds': surface_coords.min(axis=0).tolist() + surface_coords.max(axis=0).tolist(),
                       'nodes':len(tags),'cells':cells,'boundary_groups':groups,'volume_groups':volume_groups,
                       'untagged_surface_triangles': sum(not t['tags'] for t in triangles),
                       'internal_interface_elements': interfaces,
                       'preview_geometry': 'boundary corner nodes; original mesh coordinates unchanged'}
            preview = {'nodes': surface_coords.tolist(),
                       'triangles':[{'nodes':[compact[n] for n in t['nodes']],'tags':t['tags'],
                           'volume_tags':t['volume_tags']} for t in triangles],
                       'bounds':summary['bounds'],'groups':groups,'volume_groups':volume_groups}
            return summary, preview
        finally:
            gmsh.finalize()
