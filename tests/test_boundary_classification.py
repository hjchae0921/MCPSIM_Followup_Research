"""Classified natural-boundary inputs, independent of the mutable live library."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from problem_selection_agent.formulation import Formulation, FormulationReview
from problem_selection_agent.catalog import Catalog, check_formulation
from boundary_condition_agent import parameter_selection, values


class BoundaryClassificationTests(unittest.TestCase):
    def setUp(self):
        self.spec={'problem':{'type':'linear_elasticity','unknowns':['displacement'],
            'linearity':'linear','time_dependence':'independent','history_dependence':False,'dimension':3,
            'coupling':{'type':'single_physics','dependencies':[{'from':None,'to':None}]}},
            'materials':[{'constitutive_models':[{'model':'linear_elasticity','fields':['displacement'],'symmetry':'isotropic'}]}]}
        self.form={'weak_form':[{'field':'displacement','unknown':r'\mathbf{u}',
            'test_function':r'\mathbf{v}','type':'linear',
            'bilinear_form':r'a(u,v)=\int_\Omega\varepsilon(v):C:\varepsilon(u)\,dx+\int_{\Gamma_R}v\cdot K_u u\,ds',
            'linear_form':r'L(v)=\int_\Omega v\cdot b\,dx+\int_{\Gamma_N}v\cdot\bar{t}\,ds+\int_{\Gamma_R}v\cdot K_u u_{ext}\,ds'}],
            'kinematics':[r'\varepsilon(u)=\operatorname{sym}(\nabla u)'],
            'constitutive':[r'\sigma=C:\varepsilon(u)'],
            'constitutive_parameters':[{'name':'youngs_modulus','symbol':'E'},{'name':'poissons_ratio','symbol':r'\nu'}],
            'boundary_parameters':[{'name':'prescribed_traction','symbol':r'\bar{t}','kind':'neumann'},
                {'name':'mechanical_robin_stiffness','symbol':'K_u','kind':'robin'},
                {'name':'external_displacement','symbol':'u_{ext}','kind':'robin'}],
            'source_parameters':[{'name':'body_force','symbol':'b'}]}
        self.left={'name':'Left','dim':2,'tags':[2]};self.right={'name':'Right','dim':2,'tags':[3]}
        self.volume={'name':'Solid','dim':3,'tags':[1]}
        self.summary={'dimension':3,'coordinate_unit':'mm','boundary_groups':[self.left,self.right],'volume_groups':[self.volume]}
        self.unknowns=[{'name':'displacement','quantity':'displacement','shape':[3]}]
        self.assessment={'boundary_parameters':[{'name':p['name'],'requirement':'not_needed','regions':[],'reason':'Unused.'} for p in self.form['boundary_parameters']],
            'source_parameters':[{'name':'body_force','requirement':'not_needed','regions':[],'reason':'Unused.'}],
            'dirichlet_conditions':[{'field':'displacement','requirement':'needed','regions':[self.left],'components':[],'reason':'Fixed left end.'}]}

    def test_new_formulations_require_one_of_the_two_boundary_kinds(self):
        self.assertEqual(Formulation.model_validate(self.form).model_dump(),self.form)
        schema=Formulation.model_json_schema()['$defs']['BoundaryParameter']
        self.assertIn('kind',schema['required'])
        self.assertEqual(schema['properties']['kind']['enum'],['neumann','robin'])
        for kind in (None,'dirichlet','source','Neumann'):
            invalid=deepcopy(self.form);invalid['boundary_parameters'][0]['kind']=kind
            with self.subTest(kind=kind),self.assertRaises(ValueError):Formulation.model_validate(invalid)
        invalid=deepcopy(self.form);invalid['boundary_parameters'][0].pop('kind')
        with self.assertRaises(ValueError):Formulation.model_validate(invalid)

    def test_material_and_volume_inputs_remain_separate_from_boundary_classification(self):
        for scope in ('constitutive_parameters','source_parameters'):
            invalid=deepcopy(self.form);invalid[scope][0]['kind']='robin'
            with self.subTest(scope=scope),self.assertRaises(ValueError):Formulation.model_validate(invalid)
        invalid=deepcopy(self.form);invalid['source_parameters'][0]['name']='prescribed_traction'
        with self.assertRaisesRegex(ValueError,'unique'):Formulation.model_validate(invalid)

    def test_expert_review_uses_the_same_classification_contract(self):
        self.assertEqual(FormulationReview.model_validate({'explanation':'Reviewed.','formulation':self.form}).formulation.boundary_parameters[-1].kind,'robin')
        legacy=deepcopy(self.form);legacy['boundary_parameters'][-1].pop('kind')
        with self.assertRaises(ValueError):FormulationReview.model_validate({'explanation':'Missing classification.','formulation':legacy})

    def test_catalog_preserves_classification_when_saving_and_reusing(self):
        with tempfile.TemporaryDirectory() as folder:
            catalog=Catalog(folder);saved=catalog.register(self.spec,self.form)
            record=json.loads((Path(folder)/saved['file']).read_text())
            self.assertEqual(record['formulation']['boundary_parameters'],self.form['boundary_parameters'])
            self.assertEqual(catalog.lookup(self.spec)['formulation'],self.form)

    def test_legacy_library_reads_do_not_guess_or_rewrite_missing_kinds(self):
        legacy=deepcopy(self.form)
        for item in legacy['boundary_parameters']:item.pop('kind')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'legacy.json';path.write_text(json.dumps({**self.spec,'formulation':legacy}))
            before=path.read_bytes();catalog=Catalog(folder)
            self.assertEqual(catalog.lookup(self.spec)['formulation'],legacy)
            self.assertEqual(path.read_bytes(),before)
            with self.assertRaises(ValueError):catalog.register(self.spec,legacy)
        self.assertEqual(check_formulation(legacy,self.spec,allow_legacy=True),legacy)

    def test_condition_selection_receives_classification_and_equations_verbatim(self):
        state={'initial_request':'Fix the left end and pull the right end.',
            'functionspace_card':{'unknowns':self.unknowns},'formulation':self.form}
        before=deepcopy(state);messages,_=parameter_selection.messages(state,self.summary)
        context=json.loads(messages[1]['content'])
        self.assertEqual(context['weak_form'],self.form['weak_form'])
        self.assertEqual(context['boundary_parameters'],self.form['boundary_parameters'])
        self.assertEqual(context['source_parameters'],self.form['source_parameters'])
        self.assertEqual(state,before)

    def test_condition_agent_cannot_overwrite_the_library_classification(self):
        Reply=parameter_selection.response_model(self.form,self.summary,self.unknowns,wire=True)
        response={'explanation':'Use the specified constraints.','assessment':self.assessment,'recommendations':[]}
        wire=parameter_selection.wire_reply(response);Reply.model_validate_json(json.dumps(wire))
        wire['assessment']['boundary_parameters']['external_displacement']['kind']='neumann'
        with self.assertRaises(ValueError):Reply.model_validate_json(json.dumps(wire))

    def test_selected_boundary_values_retain_kinds_and_volume_sources_do_not_gain_them(self):
        assessment=deepcopy(self.assessment)
        for item in assessment['boundary_parameters']:item.update(requirement='needed',regions=[self.right])
        assessment['source_parameters'][0].update(requirement='needed',regions=[self.volume])
        rows=values.requirements(assessment,self.form,self.summary,self.unknowns)
        kinds={row['name']:row['kind'] for row in rows if row['scope']=='boundary_parameters'}
        self.assertEqual(kinds,{p['name']:p['kind'] for p in self.form['boundary_parameters']})
        self.assertTrue(all('kind' not in row for row in rows if row['scope']!='boundary_parameters'))
        legacy=deepcopy(self.form)
        for item in legacy['boundary_parameters']:item.pop('kind')
        self.assertTrue(all('kind' not in row for row in values.requirements(assessment,legacy,self.summary,self.unknowns)))


if __name__=='__main__':unittest.main()
