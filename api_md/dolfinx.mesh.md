<!-- Source: https://docs.fenicsproject.org/dolfinx/v0.10.0.post5/python/generated/dolfinx.mesh.html -->

# dolfinx.mesh

 

Creation, refining and marking of meshes.

 

Functions

 

| `compute_incident_entities`(topology, ...) | Compute all entities of `d1` connected to `entities` of dimension `d0`. |
| --- | --- |
| `compute_midpoints`(msh, dim, entities) | Compute the midpoints of a set of mesh entities. |
| `create_box`(comm, points, n[, cell_type, ...]) | Create a box mesh. |
| `create_geometry`(index_map, dofmap, element, ...) | Create a Geometry object. |
| `create_interval`(comm, nx, points[, dtype, ...]) | Create an interval mesh. |
| `create_mesh`(comm, cells, e, x[, ...]) | Create a mesh from topology and geometry arrays. |
| `create_rectangle`(comm, points, n[, ...]) | Create a rectangle mesh. |
| `create_submesh`(msh, dim, entities) | Create a mesh with specified entities from another mesh. |
| `create_unit_cube`(comm, nx, ny, nz[, ...]) | Create a mesh of a unit cube. |
| `create_unit_interval`(comm, nx[, dtype, ...]) | Create a mesh on the unit interval. |
| `create_unit_square`(comm, nx, ny[, ...]) | Create a mesh of a unit square. |
| `entities_to_geometry`(msh, dim, entities[, ...]) | Compute the geometric DOFs associated with the closure of the given mesh entities. |
| `exterior_facet_indices`(topology) | Compute the indices of all exterior facets that are owned by the caller. |
| `locate_entities`(msh, dim, marker) | Compute mesh entities satisfying a geometric marking function. |
| `locate_entities_boundary`(msh, dim, marker) | Compute mesh entities that are connected to an owned boundary facet and satisfy a geometric marking function. |
| `meshtags`(msh, dim, entities, values) | Create a MeshTags object that associates data with a subset of mesh entities. |
| `meshtags_from_entities`(msh, dim, entities, ...) | Create a :class:dolfinx.mesh.MeshTags` object that associates data with a subset of mesh entities, where the entities are defined by their vertices. |
| `refine`(msh[, edges, partitioner, option]) | Refine a mesh. |
| `transfer_meshtag`(meshtag, msh1, parent_cell) | Generate cell mesh tags on a refined mesh from the mesh tags on the coarse parent mesh. |
| `uniform_refine`(msh[, partitioner]) | Uniformly refine a mesh. |

 

Classes

 

| `CellType`(*values) |  |
| --- | --- |
| `DiagonalType`(*values) |  |
| `EntityMap`(entity_map) | A bidirectional map that relates entities in two different topologies. |
| `Geometry`(geometry) | The geometry of a `dolfinx.mesh.Mesh` |
| `GhostMode`(*values) |  |
| `IdentityPartitionerPlaceholder`(self) |  |
| `Mesh`(msh, domain) | A mesh. |
| `MeshTags`(meshtags) | Mesh tags associate data (markers) with a subset of mesh entities of a given dimension. |
| `RefinementOption`(*values) |  |
| `Topology`(topology) | Topology for a `dolfinx.mesh.Mesh` |

 

***class*dolfinx.mesh.CellType(**values*)**

> Bases: `Enum`
> 
>  
> 
> **hexahedron*= -8***
> 
> > 
> 
>  
> 
> **interval*= 2***
> 
> > 
> 
>  
> 
> ***property*name**
> 
> > (self) -> object
> 
>  
> 
> **point*= 1***
> 
> > 
> 
>  
> 
> **prism*= -6***
> 
> > 
> 
>  
> 
> **pyramid*= -5***
> 
> > 
> 
>  
> 
> **quadrilateral*= -4***
> 
> > 
> 
>  
> 
> **tetrahedron*= 4***
> 
> > 
> 
>  
> 
> **triangle*= 3***
> 
> >

 

***class*dolfinx.mesh.DiagonalType(**values*)**

> Bases: `Enum`
> 
>  
> 
> **crossed*= 2***
> 
> > 
> 
>  
> 
> **left*= 0***
> 
> > 
> 
>  
> 
> **left_right*= 4***
> 
> > 
> 
>  
> 
> **right*= 1***
> 
> > 
> 
>  
> 
> **right_left*= 5***
> 
> >

 

***class*dolfinx.mesh.EntityMap(*entity_map*)**

> Bases: `object`
> 
>  
> 
> A bidirectional map that relates entities in two different topologies.
> 
>  
> 
> Initialise an entity map from a C++ EntityMap object.
> 
>  
> 
> **Parameters:**
> 
> > **entity_map** – A C++ EntityMap object
> 
>   
> 
> Note
> 
>  
> 
> EntityMap objects should not usually be created using this initializer directly.
> 
>   
> 
> ***property*dim**
> 
> > Get the topological dimension of the entities related by this EntityMap.
> > 
> >  
> > 
> > **Returns:**
> > 
> > > The topological dimension
> > 
> > 
> > **Return type:**
> > 
> > > int
> 
>  
> 
> ***property*sub_topology**
> 
> > 
> 
>  
> 
> **sub_topology_to_topology(*entities*, *inverse*)**
> 
> > Map entities between the sub-topology and the parent topology.
> > 
> >  
> > 
> > If inverse is False, this function maps a list of self.dim()-dimensional entities from self.sub_topology() to the corresponding entities in self.topology(). If inverse is True, it performs the inverse mapping from self.topology() to self.sub_topology(). Entities that do not exist in the sub-topology are marked as -1.
> > 
> >   
> > 
> > Note
> > 
> >  
> > 
> > If inverse is True, this function recomputes the inverse map on every call (it is not cached), which may be expensive if called repeatedly.
> > 
> >   
> > 
> > **Parameters:**
> > 
> > > - **entities** – A list of entity indices in the source topology.
> > > - **inverse** – If False, maps from self.sub_topology() to self.topology(). If True, maps from this.topology() to this.sub_topology().
> > 
> > 
> > **Returns:**
> > 
> > > A list of mapped entity indices. Entities that don’t exist in the target topology are marked as -1.
> 
>  
> 
> ***property*topology**
> 
> >

 

***class*dolfinx.mesh.Geometry(*geometry: [Geometry_float32](dolfinx.cpp.mesh.html#dolfinx.cpp.mesh.Geometry_float32) | [Geometry_float64](dolfinx.cpp.mesh.html#dolfinx.cpp.mesh.Geometry_float64)*)**

> Bases: `object`
> 
>  
> 
> The geometry of a `dolfinx.mesh.Mesh`
> 
>  
> 
> Initialize a geometry from a C++ geometry.
> 
>  
> 
> **Parameters:**
> 
> > **geometry** – The C++ geometry object.
> 
>   
> 
> Note
> 
>  
> 
> Geometry objects should usually be constructed with the `create_geometry()` and not using this class initializer. This class is combined with different base classes that depend on the scalar type used in the Geometry.
> 
>   
> 
> ***property*cmap*: [CoordinateElement](dolfinx.fem.html#dolfinx.fem.CoordinateElement)***
> 
> > Element that describes the geometry map.
> 
>  
> 
> ***property*dim**
> 
> > Dimension of the Euclidean coordinate system.
> 
>  
> 
> ***property*dofmap*: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]***
> 
> > Dofmap for the geometry, shape `(num_cells, dofs_per_cell)`.
> 
>  
> 
> **index_map() → [IndexMap](dolfinx.cpp.common.html#dolfinx.cpp.common.IndexMap)**
> 
> > Index map describing the layout of the geometry points (nodes).
> 
>  
> 
> ***property*input_global_indices*: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int64]]***
> 
> > Global input indices of the geometry nodes.
> 
>  
> 
> ***property*x*: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[float32]] | [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[float64]]***
> 
> > Geometry coordinate points, `shape=(num_points, 3)`.

 

***class*dolfinx.mesh.GhostMode(**values*)**

> Bases: `Enum`
> 
>  
> 
> **none*= 0***
> 
> > 
> 
>  
> 
> **shared_facet*= 1***
> 
> >

 

***class*dolfinx.mesh.IdentityPartitionerPlaceholder(*self*)**

> Bases: `object`

 

***class*dolfinx.mesh.Mesh(*msh: [Mesh_float32](dolfinx.cpp.mesh.html#dolfinx.cpp.mesh.Mesh_float32) | [Mesh_float64](dolfinx.cpp.mesh.html#dolfinx.cpp.mesh.Mesh_float64)*, *domain: [Mesh](https://docs.fenicsproject.org/ufl/2025.2.0.post0/api-doc/ufl.html#ufl.domain.Mesh) | None*)**

> Bases: `object`
> 
>  
> 
> A mesh.
> 
>  
> 
> Initialize mesh from a C++ mesh.
> 
>  
> 
> **Parameters:**
> 
> > - **msh** – A C++ mesh object.
> > - **domain** – A UFL domain.
> 
>   
> 
> Note
> 
>  
> 
> Mesh objects should usually be constructed using `create_mesh()` and not using this class initializer. This class is combined with different base classes that depend on the scalar type used in the Mesh.
> 
>   
> 
> **basix_cell() → [CellType](https://docs.fenicsproject.org/basix/v0.10.0/python/_autosummary/basix.html#basix.CellType)**
> 
> > Return the Basix cell type.
> 
>  
> 
> ***property*comm**
> 
> > 
> 
>  
> 
> ***property*geometry*: Geometry***
> 
> > Mesh geometry.
> 
>  
> 
> **h(*dim: int*, *entities: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]*) → [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[float64]]**
> 
> > Geometric size measure of cell entities.
> > 
> >  
> > 
> > **Parameters:**
> > 
> > > - **dim** – Topological dimension of the entities to compute the size measure of.
> > > - **entities** – Indices of entities of dimension `dim` to compute size measure of.
> > 
> > 
> > **Returns:**
> > 
> > > Size measure for each requested entity.
> 
>  
> 
> ***property*name**
> 
> > 
> 
>  
> 
> ***property*topology*: Topology***
> 
> > Mesh topology.
> 
>  
> 
> **ufl_cell() → [Cell](https://docs.fenicsproject.org/ufl/2025.2.0.post0/api-doc/ufl.html#ufl.cell.Cell)**
> 
> > Return the UFL cell type.
> > 
> >   
> > 
> > Note
> > 
> >  
> > 
> > This method is required for UFL compatibility.
> 
>  
> 
> **ufl_domain() → [Mesh](https://docs.fenicsproject.org/ufl/2025.2.0.post0/api-doc/ufl.html#ufl.domain.Mesh) | None**
> 
> > Return the ufl domain corresponding to the mesh.
> > 
> >  
> > 
> > **Returns:**
> > 
> > > The UFL domain. Is `None` if the domain has not been set.
> > 
> >   
> > 
> > Note
> > 
> >  
> > 
> > This method is required for UFL compatibility.

 

***class*dolfinx.mesh.MeshTags(*meshtags*)**

> Bases: `object`
> 
>  
> 
> Mesh tags associate data (markers) with a subset of mesh entities of a given dimension.
> 
>  
> 
> Initialize tags from a C++ MeshTags object.
> 
>  
> 
> **Parameters:**
> 
> > **meshtags** – C++ mesh tags object.
> 
>   
> 
> Note
> 
>  
> 
> MeshTags objects should not usually be created using this initializer directly.
> 
>  
> 
> A Python mesh is passed to the initializer as it may have UFL data attached that is not attached the C + + Mesh that is associated with the C + + `meshtags` object. If mesh is passed, `mesh` and `meshtags` must share the same C + + mesh.
> 
>   
> 
> ***property*dim*: int***
> 
> > Topological dimension of the tagged entities.
> 
>  
> 
> **find(*value*) → [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]**
> 
> > Get a list of all entity indices with a given value.
> > 
> >  
> > 
> > **Parameters:**
> > 
> > > **value** – Tag value to search for.
> > 
> > 
> > **Returns:**
> > 
> > > Indices of entities with tag `value`.
> 
>  
> 
> ***property*indices*: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]***
> 
> > Indices of tagged mesh entities.
> 
>  
> 
> ***property*name*: str***
> 
> > Name of the mesh tags object.
> 
>  
> 
> ***property*topology*: [Topology](dolfinx.cpp.mesh.html#dolfinx.cpp.mesh.Topology)***
> 
> > Mesh topology with which the tags are associated.
> 
>  
> 
> **ufl_id() → int**
> 
> > Identiftying integer used by UFL.
> 
>  
> 
> ***property*values**
> 
> > Values associated with tagged mesh entities.

 

***class*dolfinx.mesh.RefinementOption(**values*)**

> Bases: `Enum`
> 
>  
> 
> **none*= 0***
> 
> > 
> 
>  
> 
> **parent_cell*= 2***
> 
> > 
> 
>  
> 
> **parent_cell_and_facet*= 3***
> 
> > 
> 
>  
> 
> **parent_facet*= 1***
> 
> >

 

***class*dolfinx.mesh.Topology(*topology: [Topology](dolfinx.cpp.mesh.html#dolfinx.cpp.mesh.Topology)*)**

> Bases: `object`
> 
>  
> 
> Topology for a `dolfinx.mesh.Mesh`
> 
>  
> 
> Initialize a topology from a C++ topology. :param topology: The C++ topology object
> 
>   
> 
> Note
> 
>  
> 
> Topology objects should usually be constructed with the `dolfinx.cpp.mesh.create_topology()` and not this class initializer.
> 
>   
> 
> **cell_name() → str**
> 
> > String representation of the cell-type of the topology
> 
>  
> 
> ***property*cell_type*: [CellType](dolfinx.cpp.mesh.html#dolfinx.cpp.mesh.CellType)***
> 
> > Get the cell type of the topology.
> 
>  
> 
> ***property*comm**
> 
> > 
> 
>  
> 
> **connectivity(*d0: int*, *d1: int*) → [AdjacencyList_int32](dolfinx.cpp.graph.html#dolfinx.cpp.graph.AdjacencyList_int32)**
> 
> > Return connectivity from entities of dimension `d0` to entities of dimension `d1`.
> > 
> >  
> > 
> > **Parameters:**
> > 
> > > - **d0** – Dimension of entity one is mapping from
> > > - **d1** – Dimension of entity one is mapping to
> 
>  
> 
> **create_connectivity(*d0: int*, *d1: int*)**
> 
> > Build entity connectivity `d0 -> d1`.
> > 
> >  
> > 
> > **Parameters:**
> > 
> > > - **d0** – Dimension of entities connectivity is from.
> > > - **d1** – Dimension of entities connectivity is to.
> 
>  
> 
> **create_entities(*dim: int*) → bool**
> 
> > Create entities of given topological dimension.
> > 
> >  
> > 
> > **Parameters:**
> > 
> > > **dim** – Topological dimension of entities to create.
> > 
> > 
> > **Returns:**
> > 
> > > `True` is entities are created, ``False` is if entities already existed.
> 
>  
> 
> **create_entity_permutations()**
> 
> > Compute entity permutations and reflections.
> 
>  
> 
> ***property*dim*: int***
> 
> > Return the topological dimension of the mesh.
> 
>  
> 
> ***property*entity_types*: list[list[[CellType](dolfinx.cpp.mesh.html#dolfinx.cpp.mesh.CellType)]]***
> 
> > Entity types in the topology for all topological dimensions.
> 
>  
> 
> **get_cell_permutation_info() → [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[uint32]]**
> 
> > Get permutation information.
> > 
> >  
> > 
> > The returned data is used for packing coefficients and assembling of tensors. The bits of each integer encodes the number of reflections and permutations for each sub-entity of the cell to be able to map it to the reference element.
> 
>  
> 
> **get_facet_permutations() → [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[uint8]]**
> 
> > Get the permutation integer to apply to facets.
> > 
> >  
> > 
> > The bits of each integer describes the number of reflections and rotations that has to be applied to a facet to map between a facet in the mesh (relative to a cell) and the corresponding facet on the reference element. The data has the shape `(num_cells, num_facets_per_cell)`, flattened row-wise. The number of cells include potential ghost cells.
> > 
> >   
> > 
> > Note
> > 
> >  
> > 
> > The data can be unpacked with `numpy.unpack_bits`.
> 
>  
> 
> **index_map(*dim: int*) → [IndexMap](dolfinx.cpp.common.html#dolfinx.cpp.common.IndexMap)**
> 
> > Get the IndexMap that describes the parallel distribution of the mesh entities.
> > 
> >  
> > 
> > **Parameters:**
> > 
> > > **dim** – Topological dimension.
> > 
> > 
> > **Returns:**
> > 
> > > Index map for the entities of dimension `dim`.
> 
>  
> 
> **index_maps(*dim: int*) → list[[IndexMap](dolfinx.cpp.common.html#dolfinx.cpp.common.IndexMap)]**
> 
> > **Get the IndexMaps that describes the parallel distribution of**
> > 
> > > the mesh entities, for each entity type of the dimension.
> > 
> >  
> > 
> > **Parameters:**
> > 
> > > **dim** – Topological dimension.
> > 
> > 
> > **Returns:**
> > 
> > > List of IndexMaps for the entities of dimension `dim`. May be empty if not yet computed.
> 
>  
> 
> **interprocess_facets() → [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]**
> 
> > List of inter-process facets, if facet topology has been computed.
> 
>  
> 
> ***property*original_cell_index*: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int64]]***
> 
> > Get the original cell index

 

**dolfinx.mesh.compute_incident_entities(*topology: Topology*, *entities: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]*, *d0: int*, *d1: int*) → [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]**

> Compute all entities of `d1` connected to `entities` of dimension `d0`.
> 
>  
> 
> **Parameters:**
> 
> > - **topology** – The topology.
> > - **entities** – List of entities of dimension `d0`.
> > - **d0** – Topological dimension.
> > - **d1** – Topological dimension to map to.
> 
> 
> **Returns:**
> 
> > Incident entity indices.

 

**dolfinx.mesh.compute_midpoints(*msh: Mesh*, *dim: int*, *entities: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]*)**

> Compute the midpoints of a set of mesh entities.
> 
>  
> 
> **Parameters:**
> 
> > - **msh** – The mesh.
> > - **dim** – Topological dimension of the mesh entities to consider.
> > - **entities** – Indices of entities in `mesh` to consider.
> 
> 
> **Returns:**
> 
> > Midpoints of the entities, shape `(num_entities, 3)`.

 

**dolfinx.mesh.create_box(*comm: ~mpi4py.MPI.Comm, points: list[~collections.abc.Buffer | ~numpy._typing._array_like._SupportsArray[~numpy.dtype[~typing.Any]] | ~numpy._typing._nested_sequence._NestedSequence[~numpy._typing._array_like._SupportsArray[~numpy.dtype[~typing.Any]]] | bool | int | float | complex | str | bytes | ~numpy._typing._nested_sequence._NestedSequence[bool | int | float | complex | str | bytes]], n: ~collections.abc.Sequence[int], cell_type=CellType.tetrahedron, dtype: ~numpy.dtype[~typing.Any] | None | type[~typing.Any] | ~numpy._typing._dtype_like._SupportsDType[~numpy.dtype[~typing.Any]] | str | tuple[~typing.Any, int] | tuple[~typing.Any, ~typing.SupportsIndex | ~collections.abc.Sequence[~typing.SupportsIndex]] | list[~typing.Any] | ~numpy._typing._dtype_like._DTypeDict | tuple[~typing.Any, ~typing.Any] = <class 'numpy.float64'>, ghost_mode=GhostMode.shared_facet, partitioner=None*) → Mesh**

> Create a box mesh.
> 
>  
> 
> **Parameters:**
> 
> > - **comm** – MPI communicator.
> > - **points** – Coordinates of the ‘lower-left’ and ‘upper-right’ corners of the box.
> > - **n** – List of cells in each direction
> > - **cell_type** – The cell type.
> > - **dtype** – Float type for the mesh geometry(`numpy.float32` or `numpy.float64`).
> > - **ghost_mode** – The ghost mode used in the mesh partitioning.
> > - **partitioner** – Function that computes the parallel distribution of cells across MPI ranks.
> 
> 
> **Returns:**
> 
> > A mesh of a box domain.

 

**dolfinx.mesh.create_geometry(*index_map: [IndexMap](dolfinx.cpp.common.html#dolfinx.cpp.common.IndexMap)*, *dofmap: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]*, *element: [CoordinateElement](dolfinx.fem.html#dolfinx.fem.CoordinateElement)*, *x: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)*, *input_global_indices: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int64]]*) → Geometry**

> Create a Geometry object.
> 
>  
> 
> **Parameters:**
> 
> > - **index_map** – Index map describing the layout of the geometry points (nodes).
> > - **dofmap** – The geometry (point) dofmap. For a cell, it gives the row in the point coordinates `x` of each local geometry node. `shape=(num_cells, num_dofs_per_cell)`.
> > - **element** – Element that describes the cell geometry map.
> > - **x** – The point coordinates. The shape is `(num_points, geometric_dimension).`
> > - **input_global_indices** – The ‘global’ input index of each point, commonly from a mesh input file.

 

**dolfinx.mesh.create_interval(*comm: ~mpi4py.MPI.Comm, nx: int, points: ~collections.abc.Buffer | ~numpy._typing._array_like._SupportsArray[~numpy.dtype[~typing.Any]] | ~numpy._typing._nested_sequence._NestedSequence[~numpy._typing._array_like._SupportsArray[~numpy.dtype[~typing.Any]]] | bool | int | float | complex | str | bytes | ~numpy._typing._nested_sequence._NestedSequence[bool | int | float | complex | str | bytes], dtype: ~numpy.dtype[~typing.Any] | None | type[~typing.Any] | ~numpy._typing._dtype_like._SupportsDType[~numpy.dtype[~typing.Any]] | str | tuple[~typing.Any, int] | tuple[~typing.Any, ~typing.SupportsIndex | ~collections.abc.Sequence[~typing.SupportsIndex]] | list[~typing.Any] | ~numpy._typing._dtype_like._DTypeDict | tuple[~typing.Any, ~typing.Any] = <class 'numpy.float64'>, ghost_mode=GhostMode.shared_facet, partitioner=None*) → Mesh**

> Create an interval mesh.
> 
>  
> 
> **Parameters:**
> 
> > - **comm** – MPI communicator.
> > - **nx** – Number of cells.
> > - **points** – Coordinates of the end points.
> > - **dtype** – Float type for the mesh geometry(`numpy.float32` or `numpy.float64`).
> > - **ghost_mode** – Ghost mode used in the mesh partitioning. Options are `GhostMode.none` and `GhostMode.shared_facet`.
> > - **partitioner** – Partitioning function to use for determining the parallel distribution of cells across MPI ranks.
> 
> 
> **Returns:**
> 
> > An interval mesh.

 

**dolfinx.mesh.create_mesh(*comm: [Comm](https://mpi4py.readthedocs.io/en/4.1.1/reference/mpi4py.MPI.Comm.html#mpi4py.MPI.Comm)*, *cells: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int64]]*, *e: [Mesh](https://docs.fenicsproject.org/ufl/2025.2.0.post0/api-doc/ufl.html#ufl.domain.Mesh) | [FiniteElement](https://docs.fenicsproject.org/basix/v0.10.0/python/_autosummary/basix.finite_element.html#basix.finite_element.FiniteElement) | _BasixElement | [CoordinateElement](dolfinx.fem.html#dolfinx.fem.CoordinateElement)*, *x: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[[floating](https://numpy.org/doc/2.2/reference/arrays.scalars.html#numpy.floating)]]*, *partitioner: Callable | None = None*, *max_facet_to_cell_links: int = 2*) → Mesh**

> Create a mesh from topology and geometry arrays.
> 
>  
> 
> **Parameters:**
> 
> > - **comm** – MPI communicator to define the mesh on.
> > - **cells** – Cells of the mesh. `cells[i]` are the ‘nodes’ of cell `i`.
> > - **x** – Mesh geometry (‘node’ coordinates), with shape `(num_nodes, gdim)`.
> > - **e** – UFL mesh. The mesh scalar type is determined by the scalar type of `e`.
> > - **partitioner** – Function that determines the parallel distribution of cells across MPI ranks.
> > - **max_facet_to_cell_links** – Maximum number of cells a facet can be connected to.
> 
>   
> 
> Note
> 
>  
> 
> If required, the coordinates `x` will be cast to the same scalar type as the domain/element `e`.
> 
>   
> 
> **Returns:**
> 
> > A mesh.

 

**dolfinx.mesh.create_rectangle(*comm: ~mpi4py.MPI.Comm, points: ~collections.abc.Buffer | ~numpy._typing._array_like._SupportsArray[~numpy.dtype[~typing.Any]] | ~numpy._typing._nested_sequence._NestedSequence[~numpy._typing._array_like._SupportsArray[~numpy.dtype[~typing.Any]]] | bool | int | float | complex | str | bytes | ~numpy._typing._nested_sequence._NestedSequence[bool | int | float | complex | str | bytes], n: ~collections.abc.Sequence[int], cell_type=CellType.triangle, dtype: ~numpy.dtype[~typing.Any] | None | type[~typing.Any] | ~numpy._typing._dtype_like._SupportsDType[~numpy.dtype[~typing.Any]] | str | tuple[~typing.Any, int] | tuple[~typing.Any, ~typing.SupportsIndex | ~collections.abc.Sequence[~typing.SupportsIndex]] | list[~typing.Any] | ~numpy._typing._dtype_like._DTypeDict | tuple[~typing.Any, ~typing.Any] = <class 'numpy.float64'>, ghost_mode=GhostMode.shared_facet, partitioner=None, diagonal: ~dolfinx.cpp.mesh.DiagonalType = DiagonalType.right*) → Mesh**

> Create a rectangle mesh.
> 
>  
> 
> **Parameters:**
> 
> > - **comm** – MPI communicator.
> > - **points** – Coordinates of the lower - left and upper - right corners of the rectangle.
> > - **n** – Number of cells in each direction.
> > - **cell_type** – Mesh cell type.
> > - **dtype** – Float type for the mesh geometry(`numpy.float32` or `numpy.float64`)
> > - **ghost_mode** – Ghost mode used in the mesh partitioning.
> > - **partitioner** – Function that computes the parallel distribution of cells across MPI ranks.
> > - **diagonal** – Direction of diagonal of triangular meshes. See `DiagonalType` for available options.
> 
> 
> **Returns:**
> 
> > A mesh of a rectangle.

 

**dolfinx.mesh.create_submesh(*msh: Mesh*, *dim: int*, *entities: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]*) → tuple[Mesh, EntityMap, EntityMap, [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]]**

> Create a mesh with specified entities from another mesh.
> 
>  
> 
> **Parameters:**
> 
> > - **msh** – Mesh to create the sub-mesh from.
> > - **dim** – Topological dimension of the entities in `msh` to include in the sub-mesh.
> > - **entities** – Indices of entities in `msh` to include in the sub-mesh.
> 
> 
> **Returns:**
> 
> > The (1) sub mesh, (2) entity map, (3) vertex map, and (4) node map (geometry). Each of the maps a local index of the sub mesh to a local index of `msh`.

 

**dolfinx.mesh.create_unit_cube(*comm: ~mpi4py.MPI.Comm*, *nx: int*, *ny: int*, *nz: int*, *cell_type=CellType.tetrahedron*, *dtype: ~numpy.dtype[~typing.Any] | None | type[~typing.Any] | ~numpy._typing._dtype_like._SupportsDType[~numpy.dtype[~typing.Any]] | str | tuple[~typing.Any*, *int] | tuple[~typing.Any*, *~typing.SupportsIndex | ~collections.abc.Sequence[~typing.SupportsIndex]] | list[~typing.Any] | ~numpy._typing._dtype_like._DTypeDict | tuple[~typing.Any*, *~typing.Any] = <class 'numpy.float64'>*, *ghost_mode=GhostMode.shared_facet*, *partitioner=None*) → Mesh**

> Create a mesh of a unit cube.
> 
>  
> 
> **Parameters:**
> 
> > - **comm** – MPI communicator.
> > - **nx** – Number of cells in “x” direction.
> > - **ny** – Number of cells in “y” direction.
> > - **nz** – Number of cells in “z” direction.
> > - **cell_type** – Mesh cell type
> > - **dtype** – Float type for the mesh geometry(`numpy.float32` or `numpy.float64`).
> > - **ghost_mode** – Ghost mode used in the mesh partitioning.
> > - **partitioner** – Function that computes the parallel distribution of cells across MPI ranks.
> 
> 
> **Returns:**
> 
> > A mesh of an axis-aligned unit cube with corners at `(0, 0, 0)` and `(1, 1, 1)`.

 

**dolfinx.mesh.create_unit_interval(*comm: ~mpi4py.MPI.Comm*, *nx: int*, *dtype: ~numpy.dtype[~typing.Any] | None | type[~typing.Any] | ~numpy._typing._dtype_like._SupportsDType[~numpy.dtype[~typing.Any]] | str | tuple[~typing.Any*, *int] | tuple[~typing.Any*, *~typing.SupportsIndex | ~collections.abc.Sequence[~typing.SupportsIndex]] | list[~typing.Any] | ~numpy._typing._dtype_like._DTypeDict | tuple[~typing.Any*, *~typing.Any] = <class 'numpy.float64'>*, *ghost_mode=GhostMode.shared_facet*, *partitioner=None*) → Mesh**

> Create a mesh on the unit interval.
> 
>  
> 
> **Parameters:**
> 
> > - **comm** – MPI communicator.
> > - **nx** – Number of cells.
> > - **points** – Coordinates of the end points.
> > - **dtype** – Float type for the mesh geometry(`numpy.float32` or `numpy.float64`).
> > - **ghost_mode** – Ghost mode used in the mesh partitioning. Options are `GhostMode.none` and `GhostMode.shared_facet`.
> > - **partitioner** – Partitioning function to use for determining the parallel distribution of cells across MPI ranks.
> 
> 
> **Returns:**
> 
> > A unit interval mesh with end points at 0 and 1.

 

**dolfinx.mesh.create_unit_square(*comm: ~mpi4py.MPI.Comm*, *nx: int*, *ny: int*, *cell_type=CellType.triangle*, *dtype: ~numpy.dtype[~typing.Any] | None | type[~typing.Any] | ~numpy._typing._dtype_like._SupportsDType[~numpy.dtype[~typing.Any]] | str | tuple[~typing.Any*, *int] | tuple[~typing.Any*, *~typing.SupportsIndex | ~collections.abc.Sequence[~typing.SupportsIndex]] | list[~typing.Any] | ~numpy._typing._dtype_like._DTypeDict | tuple[~typing.Any*, *~typing.Any] = <class 'numpy.float64'>*, *ghost_mode=GhostMode.shared_facet*, *partitioner=None*, *diagonal: ~dolfinx.cpp.mesh.DiagonalType = DiagonalType.right*) → Mesh**

> Create a mesh of a unit square.
> 
>  
> 
> **Parameters:**
> 
> > - **comm** – MPI communicator.
> > - **nx** – Number of cells in the “x” direction.
> > - **ny** – Number of cells in the “y” direction.
> > - **cell_type** – Mesh cell type.
> > - **dtype** – Float type for the mesh geometry(`numpy.float32` or `numpy.float64`).
> > - **ghost_mode** – Ghost mode used in the mesh partitioning.
> > - **partitioner** – Function that computes the parallel distribution of cells across MPI ranks.
> > - **diagonal** – Direction of diagonal. See `DiagonalType` for available options.
> 
> 
> **Returns:**
> 
> > A mesh of a square with corners at `(0, 0)` and `(1, 1)`.

 

**dolfinx.mesh.entities_to_geometry(*msh: Mesh*, *dim: int*, *entities: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]*, *permute=False*) → [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]**

> Compute the geometric DOFs associated with the closure of the given mesh entities.
> 
>  
> 
> **Parameters:**
> 
> > - **msh** – The mesh.
> > - **dim** – Topological dimension of the entities of interest.
> > - **entities** – Entity indices (local to the process).
> > - **permute** – Permute the DOFs such that they are consistent with the orientation of dim-dimensional mesh entities. This requires create_entity_permutations to be called first.
> 
> 
> **Returns:**
> 
> > The geometric DOFs associated with the closure of the entities in entities.

 

**dolfinx.mesh.exterior_facet_indices(*topology: Topology*) → [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]**

> Compute the indices of all exterior facets that are owned by the caller.
> 
>  
> 
> An exterior facet (co-dimension 1) is one that is connected globally to only one cell of co-dimension 0).
> 
>   
> 
> Note
> 
>  
> 
> This is a collective operation that should be called on all processes.
> 
>   
> 
> **Parameters:**
> 
> > **topology** – The topology
> 
> 
> **Returns:**
> 
> > Sorted list of owned facet indices that are exterior facets of the mesh.

 

**dolfinx.mesh.locate_entities(*msh: Mesh*, *dim: int*, *marker: Callable*) → [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)**

> Compute mesh entities satisfying a geometric marking function.
> 
>  
> 
> **Parameters:**
> 
> > - **msh** – Mesh to locate entities on.
> > - **dim** – Topological dimension of the mesh entities to consider.
> > - **marker** – A function that takes an array of points `x` with shape `(gdim, num_points)` and returns an array of booleans of length `num_points`, evaluating to True for entities to be located.
> 
> 
> **Returns:**
> 
> > Indices (local to the process) of marked mesh entities.

 

**dolfinx.mesh.locate_entities_boundary(*msh: Mesh*, *dim: int*, *marker: Callable*) → [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)**

> Compute mesh entities that are connected to an owned boundary facet and satisfy a geometric marking function.
> 
>  
> 
> For vertices and edges, in parallel this function will not necessarily mark all entities that are on the exterior boundary. For example, it is possible for a process to have a vertex that lies on the boundary without any of the attached facets being a boundary facet. When used to find degrees-of-freedom, e.g. using [`dolfinx.fem.locate_dofs_topological()`](dolfinx.fem.html#dolfinx.fem.locate_dofs_topological), the function that uses the data returned by this function must typically perform some parallel communication.
> 
>  
> 
> **Parameters:**
> 
> > - **msh** – Mesh to locate boundary entities on.
> > - **dim** – Topological dimension of the mesh entities to consider
> > - **marker** – Function that takes an array of points `x` with shape `(gdim, num_points)` and returns an array of booleans of length `num_points`, evaluating to `True` for entities to be located.
> 
> 
> **Returns:**
> 
> > Indices (local to the process) of marked mesh entities.

 

**dolfinx.mesh.meshtags(*msh: Mesh*, *dim: int*, *entities: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]*, *values: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray) | int | float*) → MeshTags**

> Create a MeshTags object that associates data with a subset of mesh entities.
> 
>  
> 
> **Parameters:**
> 
> > - **msh** – The mesh.
> > - **dim** – Topological dimension of the mesh entity.
> > - **entities** – Indices(local to process) of entities to associate values with . The array must be sorted and must not contain duplicates.
> > - **values** – The corresponding value for each entity.
> 
> 
> **Returns:**
> 
> > A mesh tags object.
> 
>   
> 
> Note
> 
>  
> 
> The type of the returned MeshTags is inferred from the type of `values`.

 

**dolfinx.mesh.meshtags_from_entities(*msh: Mesh*, *dim: int*, *entities: [AdjacencyList](dolfinx.graph.html#dolfinx.graph.AdjacencyList)*, *values: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[Any]]*)**

> Create a :class:dolfinx.mesh.MeshTags` object that associates data with a subset of mesh entities, where the entities are defined by their vertices.
> 
>  
> 
> **Parameters:**
> 
> > - **msh** – The mesh.
> > - **dim** – Topological dimension of the mesh entity.
> > - **entities** – Entities to associated values with, with entities defined by their vertices.
> > - **values** – The corresponding value for each entity.
> 
> 
> **Returns:**
> 
> > A mesh tags object.
> 
>   
> 
> Note
> 
>  
> 
> The type of the returned MeshTags is inferred from the type of `values`.

 

**dolfinx.mesh.refine(*msh: ~dolfinx.mesh.Mesh*, *edges: ~numpy.ndarray | None = None*, *partitioner: ~collections.abc.Callable | ~dolfinx.cpp.refinement.IdentityPartitionerPlaceholder = <dolfinx.cpp.refinement.IdentityPartitionerPlaceholder object>*, *option: ~dolfinx.cpp.refinement.RefinementOption = RefinementOption.parent_cell*) → tuple[Mesh, [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]], [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int8]]]**

> Refine a mesh.
> 
>   
> 
> Note
> 
>  
> 
> Using the None partitioner for the refined mesh, the refined mesh will **not** include ghosts cells (cells connected by facet to an owned cells) even if the parent mesh is ghosted. The refined cells will be on the same process as the parent cell.
> 
>   
> 
> **Parameters:**
> 
> > - **msh** – Mesh from which to create the refined mesh.
> > - **edges** – Indices of edges to split during refinement. If `None`, mesh refinement is uniform.
> > - **partitioner** – Partitioner to distribute the refined mesh. If a `IdentityPartitionerPlaceholder` is passed (default) no redistribution is performed, i.e. refined cells remain on the same process as the parent cell, but the ghost layer is updated. If a custom partitioner is passed, it will be used for distributing the refined mesh. If `None` is passed no redistribution will happen.
> > - **option** – Controls whether parent cells and/or parent facets are computed.
> 
> 
> **Returns:**
> 
> > Refined mesh, (optional) parent cells, (optional) parent facets

 

**dolfinx.mesh.transfer_meshtag(*meshtag: MeshTags*, *msh1: Mesh*, *parent_cell: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int32]]*, *parent_facet: [ndarray](https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.html#numpy.ndarray)[tuple[int, ...], [dtype](https://numpy.org/doc/2.2/reference/generated/numpy.dtype.html#numpy.dtype)[int8]] | None = None*) → MeshTags**

> Generate cell mesh tags on a refined mesh from the mesh tags on the coarse parent mesh.
> 
>  
> 
> **Parameters:**
> 
> > - **meshtag** – Mesh tags on the coarse, parent mesh.
> > - **msh1** – The refined mesh.
> > - **parent_cell** – Index of the parent cell for each cell in the refined mesh.
> > - **parent_facet** – Index of the local parent facet for each cell in the refined mesh. Only required for transfer tags on facets.
> 
> 
> **Returns:**
> 
> > Mesh tags on the refined mesh.

 

**dolfinx.mesh.uniform_refine(*msh: Mesh*, *partitioner: Callable | None = None*) → Mesh**

> Uniformly refine a mesh.
> 
>   
> 
> Note
> 
>  
> 
> Using the default partitioner for the refined mesh, the refined mesh will **not** include ghosts cells (cells connected by facet to an owned cells) even if the parent mesh is ghosted. The refined cells will be on the same process as the parent cell.
> 
>   
> 
> **Parameters:**
> 
> > - **msh** – Mesh from which to create the refined mesh.
> > - **partitioner** – Partitioner to distribute the refined mesh. If `None` is passed (default) no redistribution will happen.
> 
> 
> **Returns:**
> 
> > The refined mesh.
