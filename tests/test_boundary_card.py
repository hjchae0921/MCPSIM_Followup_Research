"""Dirichlet projections preserve physical constraints and enforce scalar component values."""
from copy import deepcopy
import json
import unittest

from codegen.boundary_card import card, card_model


class BoundaryCardTests(unittest.TestCase):
    def setUp(self):
        self.unknowns=[{'name':'displacement','quantity':'displacement','shape':[3]},
            {'name':'temperature','quantity':'temperature','shape':[]}]
        self.left={'name':'Grip_Left','dim':2,'tags':[2]}
        self.right={'name':'Grip_Right','dim':2,'tags':[3]}

    def condition(self,field,components,value,region=None,unit='mm'):
        return {'field':field,'components':components,'value':value,'region':region or self.left,'unit':unit}

    def test_whole_vector_splits_without_adding_transverse_constraints_to_tension(self):
        conditions=[self.condition('displacement',[],[0,0,0]),
            self.condition('displacement',[0],0.1,self.right)]
        before=deepcopy(conditions)
        result=card(self.unknowns,conditions)['boundary_conditions']
        self.assertEqual(conditions,before)
        self.assertEqual([(c['region']['name'],c['components'],c['parameters']['value']['value']) for c in result],
            [('Grip_Left',[0],0.0),('Grip_Left',[1],0.0),('Grip_Left',[2],0.0),('Grip_Right',[0],0.1)])
        self.assertTrue(all(c['parameters']['value']['unit']=='mm' and c['kind']=='Dirichlet' for c in result))

    def test_partial_components_preserve_order_and_approved_shared_scalar(self):
        selected=card(self.unknowns,[self.condition('displacement',[2,0],[0.3,0.1])])['boundary_conditions']
        self.assertEqual([(p['components'],p['parameters']['value']['value']) for p in selected],[([2],0.3),([0],0.1)])
        shared=card(self.unknowns,[self.condition('displacement',[1,2],0)])['boundary_conditions']
        self.assertEqual([p['components'] for p in shared],[[1],[2]])
        self.assertTrue(all(p['parameters']['value']['value']==0 for p in shared))

    def test_scalar_field_retains_empty_components_and_scalar_value(self):
        result=card(self.unknowns,[self.condition('temperature',[],293.15,unit='K')])['boundary_conditions']
        self.assertEqual(len(result),1);self.assertEqual(result[0]['components'],[])
        self.assertEqual(result[0]['parameters']['value'],{'value':293.15,'unit':'K'})
        self.assertEqual(card(self.unknowns,[])['boundary_conditions'],[])

    def test_tensor_and_single_component_vector_have_scalar_component_outputs(self):
        fields=[{'name':'tensor','quantity':'tensor','shape':[2,2]},
            {'name':'vector','quantity':'vector','shape':[1]}]
        result=card(fields,[self.condition('tensor',[],[[1,2],[3,4]],unit=''),
            self.condition('vector',[],[0])])['boundary_conditions']
        self.assertEqual([c['components'] for c in result],[[0],[1],[2],[3],[0]])
        self.assertEqual([c['parameters']['value']['value'] for c in result],[1,2,3,4,0])

    def test_invalid_source_shapes_components_values_and_duplicates_are_rejected(self):
        invalid=[self.condition('missing',[],0),self.condition('temperature',[0],0),
            self.condition('temperature',[],[0]),self.condition('displacement',[],0),
            self.condition('displacement',[3],0),self.condition('displacement',[-1],0),
            self.condition('displacement',[True],0),self.condition('displacement',[0,0],0),
            self.condition('displacement',[0,2],[1,2,3]),self.condition('displacement',[0],True),
            self.condition('displacement',[0],float('nan')),self.condition('displacement',[0],float('inf'))]
        for condition in invalid:
            with self.subTest(condition=condition),self.assertRaises(ValueError):card(self.unknowns,[condition])
        with self.assertRaises(ValueError):card(self.unknowns,[self.condition('displacement',[],[0,0,0]),self.condition('displacement',[1],0)])

    def test_output_schema_enforces_field_component_choices_and_numeric_scalar(self):
        Model=card_model(self.unknowns)
        valid=card(self.unknowns,[self.condition('displacement',[1],0)])
        Model.model_validate_json(json.dumps(valid))
        mutations=[{'field':'unknown'}, {'components':[]},{'components':[0,1]},{'components':[3]},
            {'kind':'Neumann'},{'parameters':{'value':{'value':[0,0,0],'unit':'mm'}}},
            {'parameters':{'value':{'value':True,'unit':'mm'}}}]
        for mutation in mutations:
            bad=deepcopy(valid);bad['boundary_conditions'][0].update(mutation)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):Model.model_validate_json(json.dumps(bad))
        # A scalar field cannot use the component numbering of the vector field.
        bad=deepcopy(valid);bad['boundary_conditions'][0]['field']='temperature'
        with self.assertRaises(ValueError):Model.model_validate_json(json.dumps(bad))
        def strict(node):
            if isinstance(node,dict):
                if '$ref' in node:self.assertEqual(set(node),{'$ref'})
                if node.get('type')=='object':
                    self.assertFalse(node['additionalProperties']);self.assertEqual(set(node['required']),set(node['properties']))
                for child in node.values():strict(child)
            elif isinstance(node,list):
                for child in node:strict(child)
        strict(Model.model_json_schema())


if __name__=='__main__':unittest.main()
