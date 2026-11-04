"""The initial mesh length choice reaches both numeric authoring stages."""
import json
import unittest
from copy import deepcopy

from tests import test_values as fixtures


class AuthoringUnitTests(unittest.TestCase):
    def setUp(self):
        self.case=fixtures.BoundaryValuesTests();self.case.setUp();self.addCleanup(self.case.doCleanups)
        self.f=self.case.f

    def test_material_and_boundary_values_receive_the_same_mesh_length_convention(self):
        self.f.mesh['summary']['coordinate_unit']='cm'
        before=deepcopy(self.f.mesh)
        self.f.start_materials()
        user=self.f.client.chat.completions.create.call_args.kwargs['messages'][1]['content']
        block=user.split('[Mesh length convention]\n')[1].split('\n\n')[0]
        material=json.loads(block)
        self.assertEqual(material,{'length_unit':'cm','meters_per_length_unit':0.01})
        self.case.start()
        request=self.f.client.chat.completions.create.call_args.kwargs
        self.assertEqual(request['response_format']['json_schema']['name'],'boundary_values')
        context=json.loads(request['messages'][1]['content'])
        self.assertEqual(context['unit_context'],material)
        self.assertEqual(context['mesh']['coordinate_unit'],'cm')
        self.assertEqual(self.f.mesh,before)

    def test_missing_mesh_unit_stays_unknown_instead_of_defaulting_to_meters(self):
        self.f.mesh['summary']['coordinate_unit']=None
        self.f.start_materials()
        text=self.f.client.chat.completions.create.call_args.kwargs['messages'][1]['content']
        block=text.split('[Mesh length convention]\n')[1].split('\n\n')[0]
        self.assertEqual(json.loads(block),{'length_unit':None,'meters_per_length_unit':None})
        self.case.start()
        context=json.loads(self.f.client.chat.completions.create.call_args.kwargs['messages'][1]['content'])
        self.assertIsNone(context['unit_context']['length_unit'])



class LengthConversionTests(unittest.TestCase):
    def test_explicit_lengths_preserve_physical_values_and_convert_only_once(self):
        from common.units import convert_length
        cases=[(205,'W/(m·K)',0.205,'W/(mm·K)'),
               (10,'W/(m² K)',1e-5,'W/(mm² K)'),(25,'W/(m² K)',2.5e-5,'W/(mm² K)'),
               (1e6,'W/m^3',0.001,'W/mm^3'),
               (1,'m',1000,'mm'),(1,'m^-1',0.001,'mm^-1'),
               (2,'kg m-3',2e-9,'kg mm-3'),(2,'N/m2',2e-6,'N/mm2')]
        for value,unit,expected,expected_unit in cases:
            with self.subTest(unit=unit):
                result,new_unit,note=convert_length(value,unit,{'coordinate_unit':'mm'})
                self.assertAlmostEqual(result,expected);self.assertEqual(new_unit,expected_unit)
                self.assertEqual(note['source_value'],value)
                again=convert_length(result,new_unit,{'coordinate_unit':'mm'})
                self.assertEqual(again,(result,new_unit,None))

    def test_vector_tensor_zero_and_dimensionless_temperature_are_preserved(self):
        from common.units import convert_length
        self.assertEqual(convert_length([0,1,2],'m',{'coordinate_unit':'mm'})[:2],([0,1000,2000],'mm'))
        value=[[0,1],[2,3]]
        result,unit,_=convert_length(value,'N/m²',{'coordinate_unit':'mm'})
        self.assertEqual(result,[[0,1e-6],[2e-6,3e-6]])
        for val,unit in ((0,''),(293.15,'K'),(20,'degC'),(210,'GPa')):
            self.assertEqual(convert_length(val,unit,{'coordinate_unit':'mm'}),(val,unit,None))
        self.assertEqual(convert_length(1,'m',{'coordinate_unit':None}),(1,'m',None))
        self.assertEqual(convert_length(None,'m',{'coordinate_unit':'mm'}),(None,'m',None))

    def test_unit_parser_does_not_execute_code_or_guess_ambiguous_units(self):
        from common.units import convert_length
        for unit in ("m*__import__('os').system('false')",'W/(m K','W/(mK)'):
            self.assertEqual(convert_length(1,unit,{'coordinate_unit':'mm'}),(1,unit,None))

    def test_new_material_recommendations_are_normalized_without_approval(self):
        from tests import fixtures as setup
        f=setup.AuthoringFixture();f.setUp();self.addCleanup(f.tearDown)
        f.material_answer=f.material_recommendation()
        f.material_answer['response']['ambiguities'][0]['options'][0]['updates'][0].update(value=210000000000,unit='N/m²')
        state=f.start_materials();turn=state['material_turns'][-1]
        self.assertEqual(turn['response']['options'][0]['values'][0]['unit'],'N/mm²')
        self.assertAlmostEqual(turn['response']['options'][0]['values'][0]['value'],210000)
        self.assertTrue(turn['unit_normalizations']);self.assertIsNone(state['material_card'])

if __name__=='__main__':unittest.main()
