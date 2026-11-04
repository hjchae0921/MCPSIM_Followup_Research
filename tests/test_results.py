"""Result binding is conservative and postprocessing never hides solver failures."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from codegen.execute import execute
from codegen.results import resolve_fields


class FakeFunction:
    def __init__(self,name,shape,parts=()):
        self.name=name;self.ufl_shape=shape;self._cpp_object=object();self.parts=parts
        self.function_space=SimpleNamespace(ufl_element=lambda:SimpleNamespace(is_mixed=bool(parts)),num_sub_spaces=len(parts))
    def sub(self,index):return self.parts[index]
    def collapse(self):return self


class LinearProblem:
    def __init__(self,u):self.u=u


class NonlinearProblem(LinearProblem):pass


class ResultBindingTests(unittest.TestCase):
    def setUp(self):
        modules={'dolfinx':SimpleNamespace(fem=SimpleNamespace(Function=FakeFunction)),
            'dolfinx.fem.petsc':SimpleNamespace(LinearProblem=LinearProblem,NonlinearProblem=NonlinearProblem)}
        self.patch=patch.dict(sys.modules,modules);self.patch.start();self.addCleanup(self.patch.stop)

    def test_solver_field_is_selected_over_unsolved_placeholder(self):
        old=FakeFunction('temperature',());computed=FakeFunction('temperature',())
        resolved,errors=resolve_fields({'temperature':old,'stage_data':{'solution':computed},'problem':LinearProblem(computed)},
            [{'name':'temperature','quantity':'temperature','shape':[]}],'single_physics')
        self.assertIs(resolved['temperature'],computed);self.assertFalse(errors)

    def test_ambiguous_fields_are_reported_instead_of_picking_arbitrary_values(self):
        resolved,errors=resolve_fields({'first':FakeFunction('temperature',()),'second':FakeFunction('temperature',())},
            [{'name':'temperature','quantity':'temperature','shape':[]}],'single_physics')
        self.assertFalse(resolved);self.assertIn('temperature',errors)

    def test_mixed_solution_is_split_in_approved_unknown_order(self):
        u=FakeFunction('arbitrary_1',(3,));phi=FakeFunction('arbitrary_2',())
        parent=FakeFunction('mixed',(4,),(u,phi))
        for coupling in ('multi_physics_fully_coupled','multiphysics_fully_coupled','multi_physics_\uc591\ubc29\ud5a5'):
            with self.subTest(coupling=coupling):
                resolved,errors=resolve_fields({'problem':LinearProblem(parent)},[
                    {'name':'displacement','quantity':'displacement','shape':[3]},
                    {'name':'potential','quantity':'potential','shape':[]}],coupling)
                self.assertFalse(errors);self.assertIs(resolved['displacement'],u);self.assertIs(resolved['potential'],phi)


class ExecuteTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name);(self.folder/'input.json').write_text('{}')
        self.script=self.folder/'solve.py'

    def test_runs_once_as_main_and_exports_after_computation(self):
        self.script.write_text("if __name__ == '__main__':\n    answer=42\n")
        argv=list(sys.argv);path=list(sys.path)
        with patch('codegen.execute.export_unknowns') as export:
            execute(self.script,self.folder);self.assertEqual(export.call_count,1)
            self.assertEqual(export.call_args.args[0]['answer'],42)
        self.assertEqual(sys.argv,argv);self.assertEqual(sys.path,path)

    def test_export_error_preserves_successful_solve_and_records_message(self):
        self.script.write_text('answer=42\n')
        with patch('codegen.execute.export_unknowns',side_effect=ValueError('missing field')):execute(self.script,self.folder)
        manifest=json.loads((self.folder/'results/manifest.json').read_text())
        self.assertEqual(manifest['status'],'failed');self.assertEqual(manifest['error'],'missing field')

    def test_solver_error_is_not_treated_as_postprocessing_error(self):
        self.script.write_text("raise RuntimeError('solver failed')\n")
        with patch('codegen.execute.export_unknowns') as export:
            with self.assertRaisesRegex(RuntimeError,'solver failed'):execute(self.script,self.folder)
            export.assert_not_called()

    def test_zero_exit_exports_and_nonzero_exit_propagates(self):
        self.script.write_text('answer=42\nraise SystemExit(0)\n')
        with patch('codegen.execute.export_unknowns') as export:execute(self.script,self.folder);export.assert_called_once()
        self.script.write_text('raise SystemExit(2)\n')
        with self.assertRaises(SystemExit):execute(self.script,self.folder)


if __name__=='__main__':unittest.main()
