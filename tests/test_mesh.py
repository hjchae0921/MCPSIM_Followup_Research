"""Actual Gmsh physical groups and coordinate/measure consistency."""
import json
import unittest
from web import app
from boundary_condition_agent.mesh import read_mesh

class MeshTests(unittest.TestCase):
    def test_all_six_meshes_preserve_actual_group_names_and_coordinates(self):
        for folder in sorted((app.ROOT/'benchmarks').glob('[0-9][0-9]_*')):
            with self.subTest(mesh=folder.name):
                summary, preview = read_mesh(folder/'model.msh','model.msh')
                self.assertTrue(summary['boundary_groups'])
                self.assertTrue(summary['cells'])
                self.assertIsNone(summary['coordinate_unit'])
                metadata=json.loads((folder/'geometry.json').read_text())
                for group in summary['boundary_groups']:
                    self.assertEqual(group['tags'],metadata['groups'][group['name']]['tags'])
                    self.assertGreater(group['area'],0)
                    self.assertIsNone(group['area_si'])
                self.assertTrue(summary['volume_groups'])
                for group in summary['volume_groups']:
                    self.assertEqual(group['dim'],3)
                    self.assertEqual(group['tags'],metadata['groups'][group['name']]['tags'])
                    self.assertGreater(group['elements'],0)
                    self.assertGreater(group['volume'],0)
                    self.assertIsNone(group['volume_si'])
                volume_tags={tag for group in summary['volume_groups'] for tag in group['tags']}
                self.assertTrue(all(set(triangle['volume_tags'])<=volume_tags for triangle in preview['triangles']))
                self.assertEqual(summary['untagged_surface_triangles'],0)
                self.assertTrue(all(len(t['nodes'])==3 for t in preview['triangles']))
                self.assertEqual(summary['bounds'],preview['bounds'])

    def test_area_and_volume_measures_preserve_coordinates_and_convert_length_units(self):
        folder=app.ROOT/'benchmarks/01_heat_sink'
        summary,preview=read_mesh(folder/'model.msh','model.msh','mm')
        base=next(g for g in summary['boundary_groups'] if g['name']=='Base_Bottom')
        self.assertAlmostEqual(base['area'],80*60,places=7)
        self.assertAlmostEqual(base['area_si'],0.0048,places=12)
        self.assertAlmostEqual(sum(g['volume'] for g in summary['volume_groups']),60000,places=6)
        self.assertAlmostEqual(sum(g['volume_si'] for g in summary['volume_groups']),6e-5,places=12)
        original,_=read_mesh(folder/'model.msh','model.msh','m')
        self.assertEqual(summary['bounds'],original['bounds'])
        self.assertAlmostEqual(original['boundary_groups'][0]['area_si']/base['area_si'],1e6)

