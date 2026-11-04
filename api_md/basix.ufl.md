# basix.ufl

Functions to directly wrap Basix elements in UFL.

## basix.ufl.blocked_element(sub_element: _ElementBase, shape: tuple[int, ...], symmetry: bool | None = None) → _ElementBase

Create a UFL compatible blocked element.

**Parameters:**

- sub_element – Element used for each block.
- shape – Value shape of the element. For scalar-valued families, this can be used to create vector and tensor elements.
- symmetry – Set to True if the tensor is symmetric. Valid for rank 2 elements only.

**Returns:** A blocked finite element.

## basix.ufl.custom_element(cell_type: CellType, reference_value_shape: list[int] | tuple[int, ...], wcoeffs: ndarray[tuple[Any, ...], dtype[floating]], x: list[list[ndarray[tuple[Any, ...], dtype[floating]]]], M: list[list[ndarray[tuple[Any, ...], dtype[floating]]]], interpolation_nderivs: int, map_type: MapType, sobolev_space: SobolevSpace, discontinuous: bool, embedded_subdegree: int, embedded_superdegree: int, polyset_type: PolysetType = PolysetType.standard, dtype: type[Any] | dtype[Any] | _SupportsDType[dtype[Any]] | tuple[Any, Any] | list[Any] | _DTypeDict | str | None = None) → _ElementBase

Create a UFL compatible custom Basix element.

**Parameters:**

- cell_type – The cell type
- reference_value_shape – The reference value shape of the element
- wcoeffs – Matrices for the kth value index containing the expansion coefficients defining a polynomial basis spanning the polynomial space for this element. Shape is (dim(finite element polyset), dim(Legenre polynomials)).
- x – Interpolation points. Indices are (tdim, entity index, point index, dim).
- M – The interpolation matrices. Indices are (tdim, entity index, dof, vs, point_index, derivative).
- interpolation_nderivs – The number of derivatives that need to be used during interpolation.
- map_type – The type of map to be used to map values from the reference to a cell.
- sobolev_space – Underlying Sobolev space for the element.
- discontinuous – Indicates whether or not this is the discontinuous version of the element.
- embedded_subdegree – The highest degree n such that a Lagrange (or vector Lagrange) element of degree n is a subspace of this element.
- embedded_superdegree – The highest degree of a polynomial in this element’s polyset.
- polyset_type – Polyset type for the element.
- dtype – Floating point data type.

**Returns:** A custom finite element.

## basix.ufl.element(family: ElementFamily | str, cell: CellType | str, degree: int, lagrange_variant: LagrangeVariant = LagrangeVariant.unset, dpc_variant: DPCVariant = DPCVariant.unset, discontinuous: bool = False, shape: tuple[int, ...] | None = None, symmetry: bool | None = None, dof_ordering: list[int] | None = None, dtype: type[Any] | dtype[Any] | _SupportsDType[dtype[Any]] | tuple[Any, Any] | list[Any] | _DTypeDict | str | None = None) → _ElementBase

Create a UFL compatible element using Basix.

**Parameters:**

- family – Element family/type.
- cell – Element cell type.
- degree – Degree of the finite element.
- lagrange_variant – Variant of Lagrange to be used.
- dpc_variant – Variant of DPC to be used.
- discontinuous – If True, the discontinuous version of the element is created.
- shape – Value shape of the element. For scalar-valued families, this can be used to create vector and tensor elements.
- symmetry – Set to True if the tensor is symmetric. Valid for rank 2 elements only.
- dof_ordering – Ordering of dofs for ElementDofLayout.
- dtype – Floating point data type.

**Returns:** A finite element.

## basix.ufl.enriched_element(elements: list[_ElementBase], map_type: MapType | None = None) → _ElementBase

Create an UFL compatible enriched element from a list of elements.

**Parameters:**

- elements – The list of elements
- map_type – The map type for the enriched element.

**Returns:** An enriched finite element.

## basix.ufl.mixed_element(elements: list[_ElementBase]) → _ElementBase

Create a UFL compatible mixed element from a list of elements.

**Parameters:** elements – The list of elements

**Returns:** A mixed finite element.

## basix.ufl.quadrature_element(cell: str | CellType, value_shape: tuple[int, ...] = (), scheme: str | None = None, degree: int | None = None, points: ndarray[tuple[Any, ...], dtype[floating]] | None = None, weights: ndarray[tuple[Any, ...], dtype[floating]] | None = None, pullback: AbstractPullback = IdentityPullback(), symmetry: bool | None = None, dtype: type[Any] | dtype[Any] | _SupportsDType[dtype[Any]] | tuple[Any, Any] | list[Any] | _DTypeDict | str | None = None) → _ElementBase

Create a quadrature element.

When creating this element, either the quadrature scheme and degree must be input or the quadrature points and weights must be.

**Parameters:**

- cell – Cell to create the element on.
- value_shape – Value shape of the element.
- scheme – Quadrature scheme.
- degree – Quadrature degree.
- points – Quadrature points.
- weights – Quadrature weights.
- pullback – Map name.
- symmetry – Set to True if the tensor is symmetric. Valid for rank 2 elements only.
- dtype – Data type of quadrature points and weights

**Returns:** A ‘quadrature’ finite element.

## basix.ufl.real_element(cell: CellType | str, value_shape: tuple[int, ...]) → _ElementBase

Create a real element.

**Parameters:**

- cell – Cell to create the element on.
- value_shape – Value shape of the element.

**Returns:** A ‘real’ finite element.

## basix.ufl.wrap_element(element: FiniteElement) → _ElementBase

Wrap a Basix element as a Basix UFL element.

