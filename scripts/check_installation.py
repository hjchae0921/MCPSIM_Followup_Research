"""Check required Python packages and the local finite element runtime."""
import importlib
import json

def main():
    names=['dolfinx','basix','ufl','gmsh','mpi4py','petsc4py','openai','langgraph','pydantic','numpy','pyvista','matplotlib','markdown_it','tiktoken']
    packages={name:importlib.import_module(name) for name in names}
    from mpi4py import MPI
    from petsc4py import PETSc
    print(json.dumps({'python_packages':'available','dolfinx':packages['dolfinx'].__version__,
        'petsc':PETSc.Sys.getVersion(),'mpi_size':MPI.COMM_WORLD.size},indent=2))

if __name__=='__main__':main()
