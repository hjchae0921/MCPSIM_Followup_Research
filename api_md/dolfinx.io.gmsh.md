<!-- Source: https://docs.fenicsproject.org/dolfinx/v0.10.0.post5/python/generated/dolfinx.io.gmsh.html -->

# dolfinx.io.gmsh

 

Tools to extract data from Gmsh models.

 

Functions

 

| `cell_perm_array`(cell_type, num_nodes) | The permutation array for permuting Gmsh ordering to DOLFINx ordering. |
| --- | --- |
| `extract_geometry`(model[, name]) | Extract the mesh geometry from a Gmsh model. |
| `extract_topology_and_markers`(model[, name]) | Extract all entities tagged with a physical marker in the gmsh model. |
| `model_to_mesh`(model, comm, rank[, gdim, ...]) | Create a Mesh from a Gmsh model. |
| `read_from_msh`(filename, comm[, rank, gdim, ...]) | Read a Gmsh .msh file and return a [`dolfinx.mesh.Mesh`](dolfinx.mesh.html#dolfinx.mesh.Mesh) and cell facet markers. |
| `ufl_mesh`(gmsh_cell, gdim, dtype) | Create a UFL mesh from a Gmsh cell identifier and geometric dimension. |

 

Classes

 

| `MeshData`(mesh, cell_tags, facet_tags, ...) | Data for representing a mesh and associated tags. |
| --- | --- |
| `PhysicalGroup`(dim, tag) | Physical group info. |
| `TopologyDict` | TopologyDict is a TypedDict for storing the topology of the marked cell. |

 

***class*dolfinx.io.gmsh.MeshData(*mesh: [Mesh](dolfinx.mesh.html#dolfinx.mesh.Mesh)*, *cell_tags: [MeshTags](dolfinx.mesh.html#dolfinx.mesh.MeshTags) | None*, *facet_tags: [MeshTags](dolfinx.mesh.html#dolfinx.mesh.MeshTags) | None*, *ridge_tags: [MeshTags](dolfinx.mesh.html#dolfinx.mesh.MeshTags) | None*, *peak_tags: [MeshTags](dolfinx.mesh.html#dolfinx.mesh.MeshTags) | None*, *physical_groups: dict[str, PhysicalGroup]*)**

> Bases: `NamedTuple`
> 
>  
> 
> Data for representing a mesh and associated tags.
> 
>  
> 
> **Parameters:**
> 
> > - **mesh** – Mesh.
> > - **cell_tags** – MeshTags for cells.
> > - **facet_tags** – MeshTags for facets (codim 1).
> > - **ridge_tags** – MeshTags for ridges (codim 2).
> > - **peak_tags** – MeshTags for peaks (codim 3).
> > - **physical_groups** – Physical groups in the mesh, where the key is the physical name and the value is a tuple with the dimension and tag.
> 
>  
> 
> Create new instance of MeshData(mesh, cell_tags, facet_tags, ridge_tags, peak_tags, physical_groups)
> 
>  
> 
> **cell_tags*: [MeshTags](dolfinx.mesh.html#dolfinx.mesh.MeshTags) | None***
> 
> > Alias for field number 1
> 
>  
> 
> **facet_tags*: [MeshTags](dolfinx.mesh.html#dolfinx.mesh.MeshTags) | None***
> 
> > Alias for field number 2
> 
>  
> 
> **mesh*: [Mesh](dolfinx.mesh.html#dolfinx.mesh.Mesh)***
> 
> > Alias for field number 0
> 
>  
> 
> **peak_tags*: [MeshTags](dolfinx.mesh.html#dolfinx.mesh.MeshTags) | None***
> 
> > Alias for field number 4
> 
>  
> 
> **physical_groups*: dict[str, PhysicalGroup]***
> 
> > Alias for field number 5
> 
>  
> 
> **ridge_tags*: [MeshTags](dolfinx.mesh.html#dolfinx.mesh.MeshTags) | None***
> 
> > Alias for field number 3

 

***class*dolfinx.io.gmsh.PhysicalGroup(*dim: int*, *tag: int*)**

> Bases: `NamedTuple`
> 
>  
> 
> Physical group info.
> 
>  
> 
> **Parameters:**
> 
> > - **dim** – dimension of the physical group
> > - **tag** – tag of the physical group
> 
>  
> 
> Create new instance of PhysicalGroup(dim, tag)
> 
>  
> 
> **dim*: int***
> 
> > Alias for field number 0
> 
>  
> 
> **tag*: int***
> 
> > Alias for field number 1

 

***class*dolfinx.io.gmsh.TopologyDict**

> Bases: `TypedDict`
> 
>  
> 
> TopologyDict is a TypedDict for storing the topology of the marked cell.
> 
>  
> 
> **Parameters:**
> 
> > - **topology** – 2D array containing the topology of the marked cell.
> > - **cell_data** – List with the corresponding markers.
> 
>   
> 
> Note
> 
>  
> 
> The TypedDict is only used for type hinting, and does not enforce the structure of the dictionary, but rather provides a hint to the user and the type checker.
> 
>   
> 
> **cell_data*: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[[integer](https://numpy.org/doc/2.2/reference/arrays.scalars.html#numpy.integer)]]***
> 
> > 
> 
>  
> 
> **entity_tags*: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[[integer](https://numpy.org/doc/2.2/reference/arrays.scalars.html#numpy.integer)]]***
> 
> > 
> 
>  
> 
> **topology*: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[[integer](https://numpy.org/doc/2.2/reference/arrays.scalars.html#numpy.integer)]]***
> 
> >

 

**dolfinx.io.gmsh.cell_perm_array(*cell_type: [CellType](dolfinx.cpp.mesh.html#dolfinx.cpp.mesh.CellType)*, *num_nodes: int*) → list[int]**

> The permutation array for permuting Gmsh ordering to DOLFINx ordering.
> 
>  
> 
> **Parameters:**
> 
> > - **cell_type** – DOLFINx cell type.
> > - **num_nodes** – Number of nodes in the cell.
> 
> 
> **Returns:**
> 
> > An array `p` such that `a_dolfinx[i] = a_gmsh[p[i]]`.

 

**dolfinx.io.gmsh.extract_geometry(*model*, *name: str | None = None*) → [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[float64]]**

> Extract the mesh geometry from a Gmsh model.
> 
>  
> 
> Returns an array of shape `(num_nodes, 3)`, where the i-th row corresponds to the i-th node in the mesh.
> 
>  
> 
> **Parameters:**
> 
> > - **model** – Gmsh model
> > - **name** – Name of the Gmsh model. If not set the current model will be used.
> 
> 
> **Returns:**
> 
> > The mesh geometry as an array of shape `(num_nodes, 3)`.

 

**dolfinx.io.gmsh.extract_topology_and_markers(*model*, *name: str | None = None*) → tuple[dict[int, TopologyDict], dict[str, PhysicalGroup]]**

> Extract all entities tagged with a physical marker in the gmsh model.
> 
>  
> 
> Returns a nested dictionary where the first key is the gmsh MSH element type integer. Each element type present in the model contains the cell topology of the elements and corresponding markers.
> 
>  
> 
> **Parameters:**
> 
> > - **model** – Gmsh model.
> > - **name** – Name of the gmsh model. If not set the current model will be used.
> 
> 
> **Returns:**
> 
> > A tuple `(topologies, physical_groups)`, where `topologies` is a nested dictionary where each key corresponds to a gmsh cell type. Each cell type found in the mesh has a 2D array containing the topology of the marked cell and a list with the corresponding markers. `physical_groups` is a dictionary where the key is the physical name and the value is a tuple with the dimension and tag.

 

**dolfinx.io.gmsh.model_to_mesh(*model, comm: ~mpi4py.MPI.Comm, rank: int, gdim: int = 3, partitioner: ~collections.abc.Callable[[~mpi4py.MPI.Comm, int, int, ~dolfinx.cpp.graph.AdjacencyList_int32], ~dolfinx.cpp.graph.AdjacencyList_int32] | None = None, dtype=<class 'numpy.float64'>*) → MeshData**

> Create a Mesh from a Gmsh model.
> 
>  
> 
> Creates a [`dolfinx.mesh.Mesh`](dolfinx.mesh.html#dolfinx.mesh.Mesh) from the physical entities of the highest topological dimension in the Gmsh model. In parallel, the gmsh model is processed on one MPI rank, and the [`dolfinx.mesh.Mesh`](dolfinx.mesh.html#dolfinx.mesh.Mesh) is distributed across ranks.
> 
>  
> 
> **Parameters:**
> 
> > - **model** – Gmsh model.
> > - **comm** – MPI communicator to use for mesh creation.
> > - **rank** – MPI rank that the Gmsh model is initialized on.
> > - **gdim** – Geometrical dimension of the mesh.
> > - **partitioner** – Function that computes the parallel distribution of cells across MPI ranks.
> 
> 
> **Returns:**
> 
> > MeshData with mesh and tags of corresponding entities by codimension. Codimension 0 is the cell tags, codimension 1 is the facet tags, codimension 2 is the ridge tags and codimension 3 is the peak tags as well as a lookup table from the physical groups by name to integer.
> 
>   
> 
> Note
> 
>  
> 
> For performance, this function should only be called once for large problems. For reuse, it is recommended to save the mesh and corresponding tags using [`dolfinx.io.XDMFFile`](dolfinx.io.html#dolfinx.io.XDMFFile) after creation for efficient access.

 

**dolfinx.io.gmsh.read_from_msh(*filename: str | [Path](https://docs.fenicsproject.org/ffcx/v0.10.1.post0/_autogenerated/ffcx.options.html#ffcx.options.Path)*, *comm: [Comm](https://mpi4py.readthedocs.io/en/4.1.1/reference/mpi4py.MPI.Comm.html#mpi4py.MPI.Comm)*, *rank: int = 0*, *gdim: int = 3*, *partitioner: Callable[[[Comm](https://mpi4py.readthedocs.io/en/4.1.1/reference/mpi4py.MPI.Comm.html#mpi4py.MPI.Comm), int, int, [AdjacencyList](dolfinx.graph.html#dolfinx.graph.AdjacencyList)], [AdjacencyList_int32](dolfinx.cpp.graph.html#dolfinx.cpp.graph.AdjacencyList_int32)] | None = None*) → MeshData**

> Read a Gmsh .msh file and return a [`dolfinx.mesh.Mesh`](dolfinx.mesh.html#dolfinx.mesh.Mesh) and cell facet markers.
> 
>   
> 
> Note
> 
>  
> 
> This function requires the Gmsh Python module.
> 
>   
> 
> **Parameters:**
> 
> > - **filename** – Name of `.msh` file.
> > - **comm** – MPI communicator to create the mesh on.
> > - **rank** – Rank of `comm` responsible for reading the `.msh` file.
> > - **gdim** – Geometric dimension of the mesh
> 
> 
> **Returns:**
> 
> > Meshdata with mesh, cell tags, facet tags, edge tags, vertex tags and physical groups.

 

**dolfinx.io.gmsh.ufl_mesh(*gmsh_cell: int*, *gdim: int*, *dtype: [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[Any] | None | type[Any] | _SupportsDType[[dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[Any]] | str | tuple[Any, int] | tuple[Any, SupportsIndex | [Sequence](https://docs.fenicsproject.org/ffcx/v0.10.1.post0/_autogenerated/ffcx.main.html#ffcx.main.Sequence)[SupportsIndex]] | list[Any] | _DTypeDict | tuple[Any, Any]*) → [Mesh](https://docs.fenicsproject.org/ufl/2025.2.0.post0/api-doc/ufl.html#ufl.domain.Mesh)**

> Create a UFL mesh from a Gmsh cell identifier and geometric dimension.
> 
>  
> 
> See [https://gmsh.info//doc/texinfo/gmsh.html#MSH-file-format](https://gmsh.info//doc/texinfo/gmsh.html#MSH-file-format).
> 
>  
> 
> **Parameters:**
> 
> > - **gmsh_cell** – Gmsh cell identifier.
> > - **gdim** – Geometric dimension of the mesh.
> 
> 
> **Returns:**
> 
> > UFL Mesh using Lagrange elements (equispaced) of the corresponding DOLFINx cell.
