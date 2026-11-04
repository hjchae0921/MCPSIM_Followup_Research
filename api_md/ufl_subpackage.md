# ufl package

## Submodules

## ufl.action module

This module defines the Action class.

- **class** `class ufl.action.Action(*args, **kw)`
  Bases: BaseForm
  UFL base form type: respresents the action of an object on another.

Bases: BaseForm

UFL base form type: respresents the action of an object on another.

- `For example:`
  res = Ax

A would be the first argument, left and x would be the second argument,
right.

Action objects will result when the action of an assembled object
(e.g. a Matrix) is taken. This delays the evaluation of the action until
assembly occurs.

- **method** `equals(other)`
  Check if two Actions are equal.

- **method** `left()`
  Get left.

- **method** `right()`
  Get right.

- **method** `ufl_domains()`
  Return all domains found in the base form.

- **method** `ufl_function_spaces()`
  Get the tuple of function spaces of the underlying form.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

## ufl.adjoint module

This module defines the Adjoint class.

- **class** `class ufl.adjoint.Adjoint(*args, **kw)`
  Bases: BaseForm
  UFL base form type: represents the adjoint of an object.
  Adjoint objects will result when the adjoint of an assembled object
  (e.g. a Matrix) is taken. This delays the evaluation of the adjoint until
  assembly occurs.

Bases: BaseForm

UFL base form type: represents the adjoint of an object.

Adjoint objects will result when the adjoint of an assembled object
(e.g. a Matrix) is taken. This delays the evaluation of the adjoint until
assembly occurs.

- **method** `equals(other)`
  Check if two Adjoints are equal.

- **method** `form()`
  Return the form.

- **method** `ufl_domains()`
  Return all domains found in the base form.

- **method** `ufl_function_spaces()`
  Get the tuple of function spaces of the underlying form.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

## ufl.algebra module

Basic algebra operations.

- **class** `class ufl.algebra.Abs(a)`
  Bases: Operator
  Absolute value.

Bases: Operator

Absolute value.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.algebra.Conj(a)`
  Bases: Operator
  Complex conjugate.

Bases: Operator

Complex conjugate.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.algebra.Division(a, b)`
  Bases: Operator
  Division.

Bases: Operator

Division.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.algebra.Imag(a)`
  Bases: Operator
  Imaginary part.

Bases: Operator

Imaginary part.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.algebra.Power(a, b)`
  Bases: Operator
  Power.

Bases: Operator

Power.

- **method** `evaluate(x, mapping, component, index_values)`
  Evalute.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.algebra.Product(a, b)`
  Bases: Operator
  The product of two or more UFL objects.

Bases: Operator

The product of two or more UFL objects.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.algebra.Real(a)`
  Bases: Operator
  Real part.

Bases: Operator

Real part.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.algebra.Sum(a, b)`
  Bases: Operator
  Sum.

Bases: Operator

Sum.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

## ufl.argument module

Argument.

This module defines the class Argument and a number of related
classes (functions), including TestFunction and TrialFunction.

- **class** `class ufl.argument.Argument(*args, **kw)`
  Bases: FormArgument, BaseArgument
  UFL value: Representation of an argument to a form.

Bases: FormArgument, BaseArgument

UFL value: Representation of an argument to a form.

- **method** `ufl_domains()`
  Return UFL domains.

- **function** `ufl.argument.Arguments(function_space, number)`
  Create an Argument in a mixed space.
  Returns a tuple with the function components corresponding to the subelements.

- **class** `class ufl.argument.BaseArgument(function_space, number, part=None)`
  Bases: object
  UFL value: Representation of an argument to a form.

Bases: object

UFL value: Representation of an argument to a form.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **method** `number()`
  Return the Argument number.

- **method** `part()`
  Return the part.

- **method** `ufl_domain()`
  Return the UFL domain.

- **method** `ufl_domains()`
  Return UFL domains.

- **method** `ufl_element()`
  Return The UFL element.

- **method** `ufl_function_space()`
  Get the function space of this Argument.

- **property** `property ufl_shape`
  Return the associated UFL shape.

- **class** `class ufl.argument.Coargument(*args, **kw)`
  Bases: BaseForm, BaseArgument
  UFL value: Representation of an argument to a form in a dual space.

Bases: BaseForm, BaseArgument

UFL value: Representation of an argument to a form in a dual space.

- **method** `arguments(outer_form=None)`
  Return all Argument objects found in form.

- **method** `equals(other)`
  Check equality.

- **method** `ufl_domain()`
  Return the UFL domain.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **function** `ufl.argument.TestFunction(function_space, part=None)`
  UFL value: Create a test function argument to a form.

- **function** `ufl.argument.TestFunctions(function_space)`
  Create a TestFunction in a mixed space.
  Returns a tuple with the function components corresponding to the
  subelements.

- **function** `ufl.argument.TrialFunction(function_space, part=None)`
  UFL value: Create a trial function argument to a form.

- **function** `ufl.argument.TrialFunctions(function_space)`
  Create a TrialFunction in a mixed space.
  Returns a tuple with the function components corresponding to the
  subelements.

## ufl.averaging module

Averaging operations.

- **class** `class ufl.averaging.CellAvg(f)`
  Bases: Operator
  Cell average.

Bases: Operator

Cell average.

- **method** `evaluate(x, mapping, component, index_values)`
  Performs an approximate symbolic evaluation, since we don’t have a cell.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.averaging.FacetAvg(f)`
  Bases: Operator
  Facet average.

Bases: Operator

Facet average.

- **method** `evaluate(x, mapping, component, index_values)`
  Performs an approximate symbolic evaluation, since we dont have a cell.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

## ufl.cell module

Types for representing a cell.

- **class** `class ufl.cell.AbstractCell`
  Bases: UFLObject
  A base class for all cells.

Bases: UFLObject

A base class for all cells.

- **method** `abstractmethod cellname() → str`
  Return the cellname of the cell.

- **method** `edge_types() → tuple[AbstractCell, ...]`
  Get the unique edge types.

- **method** `edges() → tuple[AbstractCell, ...]`
  Get the edges.

- **method** `face_types() → tuple[AbstractCell, ...]`
  Get the unique face types.

- **method** `faces() → tuple[AbstractCell, ...]`
  Get the faces.

- **method** `facet_types() → tuple[AbstractCell, ...]`
  Get the unique facet types.
  Facets are entities of dimension tdim-1.

- **method** `facets() → tuple[AbstractCell, ...]`
  Get the facets.
  Facets are entities of dimension tdim-1.

- **method** `abstractmethod has_simplex_facets() → bool`
  Return True if all the facets of this cell are simplex cells.

- **method** `abstractmethod is_simplex() → bool`
  Return True if this is a simplex cell.

- **method** `num_edges() → int`
  Get the number of edges.

- **method** `num_faces() → int`
  Get the number of faces.

- **method** `num_facets() → int`
  Get the number of facets.
  Facets are entities of dimension tdim-1.

- **method** `num_peaks() → int`
  Get the number of peaks.
  Peaks are entities of dimension tdim-3.

- **method** `num_ridges() → int`
  Get the number of ridges.
  Ridges are entities of dimension tdim-2.

- **method** `abstractmethod num_sub_entities(dim: int) → int`
  Get the number of sub-entities of the given dimension.

- **method** `num_vertices() → int`
  Get the number of vertices.

- **method** `peak_types() → tuple[AbstractCell, ...]`
  Get the unique peak types.
  Peaks are entities of dimension tdim-3.

- **method** `peaks() → tuple[AbstractCell, ...]`
  Get the peaks.
  Peaks are entities of dimension tdim-3.

- **method** `abstractmethod reconstruct(**kwargs: Any) → AbstractCell`
  Reconstruct this cell, overwriting properties by those in kwargs.

- **method** `ridge_types() → tuple[AbstractCell, ...]`
  Get the unique ridge types.
  Ridges are entities of dimension tdim-2.

- **method** `ridges() → tuple[AbstractCell, ...]`
  Get the ridges.
  Ridges are entities of dimension tdim-2.

- **method** `abstractmethod sub_entities(dim: int) → tuple[AbstractCell, ...]`
  Get the sub-entities of the given dimension.

- **method** `abstractmethod sub_entity_types(dim: int) → tuple[AbstractCell, ...]`
  Get the unique sub-entity types of the given dimension.

- **method** `abstractmethod topological_dimension() → int`
  Return the dimension of the topology of this cell.

- **method** `vertex_types() → tuple[AbstractCell, ...]`
  Get the unique vertices types.

- **method** `vertices() → tuple[AbstractCell, ...]`
  Get the vertices.

- **class** `class ufl.cell.Cell(cellname: str)`
  Bases: AbstractCell
  Representation of a named finite element cell with known structure.

Bases: AbstractCell

Representation of a named finite element cell with known structure.

- **method** `cellname() → str`
  Return the cellname of the cell.

- **method** `has_simplex_facets() → bool`
  Return True if all the facets of this cell are simplex cells.

- **method** `is_simplex() → bool`
  Return True if this is a simplex cell.

- **method** `num_sub_entities(dim: int) → int`
  Get the number of sub-entities of the given dimension.

- **method** `reconstruct(**kwargs: Any) → Cell`
  Reconstruct this cell, overwriting properties by those in kwargs.

- **method** `sub_entities(dim: int) → tuple[AbstractCell, ...]`
  Get the sub-entities of the given dimension.

- **method** `sub_entity_types(dim: int) → tuple[AbstractCell, ...]`
  Get the unique sub-entity types of the given dimension.

- **method** `topological_dimension() → int`
  Return the dimension of the topology of this cell.

- **class** `class ufl.cell.TensorProductCell(*cells: AbstractCell)`
  Bases: AbstractCell
  Tensor product cell.

Bases: AbstractCell

Tensor product cell.

- **method** `cellname() → str`
  Return the cellname of the cell.

- **method** `has_simplex_facets() → bool`
  Return True if all the facets of this cell are simplex cells.

- **method** `is_simplex() → bool`
  Return True if this is a simplex cell.

- **method** `num_sub_entities(dim: int) → int`
  Get the number of sub-entities of the given dimension.

- **method** `reconstruct(**kwargs: Any) → AbstractCell`
  Reconstruct this cell, overwriting properties by those in kwargs.

- **method** `sub_cells() → tuple[AbstractCell, ...]`
  Return list of cell factors.

- **method** `sub_entities(dim: int) → tuple[AbstractCell, ...]`
  Get the sub-entities of the given dimension.

- **method** `sub_entity_types(dim: int) → tuple[AbstractCell, ...]`
  Get the unique sub-entity types of the given dimension.

- **method** `topological_dimension() → int`
  Return the dimension of the topology of this cell.

- **function** `ufl.cell.as_cell(cell: AbstractCell | str | tuple[AbstractCell, ...]) → AbstractCell`
  Convert any valid object to a Cell or return cell if it is already a Cell.
  Allows an already valid cell, a known cellname string, or a tuple of cells for a product cell.

- **function** `ufl.cell.hypercube(topological_dimension: int)`
  Return a hypercube cell of the given dimension.

- **function** `ufl.cell.simplex(topological_dimension: int)`
  Return a simplex cell of the given dimension.

## ufl.checks module

Utility functions for checking properties of expressions.

- **function** `ufl.checks.is_cellwise_constant(expr)`
  Return whether expression is constant over a single cell.

- **function** `ufl.checks.is_python_scalar(expression)`
  Return True iff expression is of a Python scalar type.

- **function** `ufl.checks.is_scalar_constant_expression(expr)`
  Check if an expression is a globally constant scalar expression.

- **function** `ufl.checks.is_true_ufl_scalar(expression)`
  Return True iff expression is scalar-valued, with no free indices.

- **function** `ufl.checks.is_ufl_scalar(expression)`
  Return True iff expression is scalar-valued, but possibly containing free indices.

## ufl.classes module

Classes.

It contains functionality used by algorithms for dealing with groups
of classes, and for mapping types to different handler functions.

- **class** `class ufl.classes.Abs(a)`
  Bases: Operator
  Absolute value.

Bases: Operator

Absolute value.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.AbstractCell`
  Bases: UFLObject
  A base class for all cells.

Bases: UFLObject

A base class for all cells.

- **method** `abstractmethod cellname() → str`
  Return the cellname of the cell.

- **method** `edge_types() → tuple[AbstractCell, ...]`
  Get the unique edge types.

- **method** `edges() → tuple[AbstractCell, ...]`
  Get the edges.

- **method** `face_types() → tuple[AbstractCell, ...]`
  Get the unique face types.

- **method** `faces() → tuple[AbstractCell, ...]`
  Get the faces.

- **method** `facet_types() → tuple[AbstractCell, ...]`
  Get the unique facet types.
  Facets are entities of dimension tdim-1.

- **method** `facets() → tuple[AbstractCell, ...]`
  Get the facets.
  Facets are entities of dimension tdim-1.

- **method** `abstractmethod has_simplex_facets() → bool`
  Return True if all the facets of this cell are simplex cells.

- **method** `abstractmethod is_simplex() → bool`
  Return True if this is a simplex cell.

- **method** `num_edges() → int`
  Get the number of edges.

- **method** `num_faces() → int`
  Get the number of faces.

- **method** `num_facets() → int`
  Get the number of facets.
  Facets are entities of dimension tdim-1.

- **method** `num_peaks() → int`
  Get the number of peaks.
  Peaks are entities of dimension tdim-3.

- **method** `num_ridges() → int`
  Get the number of ridges.
  Ridges are entities of dimension tdim-2.

- **method** `abstractmethod num_sub_entities(dim: int) → int`
  Get the number of sub-entities of the given dimension.

- **method** `num_vertices() → int`
  Get the number of vertices.

- **method** `peak_types() → tuple[AbstractCell, ...]`
  Get the unique peak types.
  Peaks are entities of dimension tdim-3.

- **method** `peaks() → tuple[AbstractCell, ...]`
  Get the peaks.
  Peaks are entities of dimension tdim-3.

- **method** `abstractmethod reconstruct(**kwargs: Any) → AbstractCell`
  Reconstruct this cell, overwriting properties by those in kwargs.

- **method** `ridge_types() → tuple[AbstractCell, ...]`
  Get the unique ridge types.
  Ridges are entities of dimension tdim-2.

- **method** `ridges() → tuple[AbstractCell, ...]`
  Get the ridges.
  Ridges are entities of dimension tdim-2.

- **method** `abstractmethod sub_entities(dim: int) → tuple[AbstractCell, ...]`
  Get the sub-entities of the given dimension.

- **method** `abstractmethod sub_entity_types(dim: int) → tuple[AbstractCell, ...]`
  Get the unique sub-entity types of the given dimension.

- **method** `abstractmethod topological_dimension() → int`
  Return the dimension of the topology of this cell.

- **method** `vertex_types() → tuple[AbstractCell, ...]`
  Get the unique vertices types.

- **method** `vertices() → tuple[AbstractCell, ...]`
  Get the vertices.

- **class** `class ufl.classes.AbstractDomain(topological_dimension, geometric_dimension)`
  Bases: object
  Symbolic representation of a geometric domain.
  Domain has only a geometric and a topological dimension.

Bases: object

Symbolic representation of a geometric domain.

Domain has only a geometric and a topological dimension.

- **method** `can_make_function_space(element: AbstractFiniteElement) → bool`
  Check whether this mesh can make a function space with element.

- **method** `geometric_dimension()`
  Return the dimension of the space this domain is embedded in.

- **method** `iterable_like(element: AbstractFiniteElement) → Iterable[Mesh] | MeshSequence`
  Return iterable object that is iterable like element.

- **property** `property meshes`
  Return the component meshes.

- **method** `topological_dimension()`
  Return the dimension of the topology of this domain.

- **class** `class ufl.classes.AbstractFiniteElement`
  Bases: ABC
  Base class for all finite elements.
  To make your element library compatible with UFL, you should make a
  subclass of AbstractFiniteElement and provide implementions of all
  the abstract methods and properties. All methods and properties that
  are not marked as abstract are implemented here and should not need
  to be overwritten in your subclass.
  An example of how the methods in your subclass could be implemented
  can be found in Basix; see
  https://github.com/FEniCS/basix/blob/main/python/basix/ufl.py

Bases: ABC

Base class for all finite elements.

To make your element library compatible with UFL, you should make a
subclass of AbstractFiniteElement and provide implementions of all
the abstract methods and properties. All methods and properties that
are not marked as abstract are implemented here and should not need
to be overwritten in your subclass.

An example of how the methods in your subclass could be implemented
can be found in Basix; see
https://github.com/FEniCS/basix/blob/main/python/basix/ufl.py

- **property** `abstract property cell: Cell`
  Return the cell of the finite element.

- **property** `abstract property embedded_subdegree: int`
  Degree of the maximum degree Lagrange space that is spanned by this element.
  This returns the degree of the highest degree Lagrange space
  such that the polynomial space of the Lagrange space is a
  subspace of this element’s polynomial space. If this element’s
  polynomial space does not include the constant function, this
  function should return -1.
  Note that on a simplex cells, the polynomial space of Lagrange
  space is a complete polynomial space, but on other cells this is
  not true. For example, on quadrilateral cells, the degree 1
  Lagrange space includes the degree 2 polynomial xy.

- **property** `abstract property embedded_superdegree: int | None`
  Degree of the minimum degree Lagrange space that spans this element.
  This returns the degree of the lowest degree Lagrange space such
  that the polynomial space of the Lagrange space is a superspace
  of this element’s polynomial space. If this element contains
  basis functions that are not in any Lagrange space, this
  function should return None.
  Note that on a simplex cells, the polynomial space of Lagrange
  space is a complete polynomial space, but on other cells this is
  not true. For example, on quadrilateral cells, the degree 1
  Lagrange space includes the degree 2 polynomial xy.

- **method** `is_cellwise_constant() → bool`
  Check whether this element is spatially constant over each cell.

- **property** `property num_sub_elements: int`
  Return number of sub-elements.
  This function does not recurse: ie it does not count the sub-elements of
  sub-elements.

- **property** `abstract property pullback: AbstractPullback`
  Return the pullback for this element.

- **property** `abstract property reference_value_shape: tuple[int, ...]`
  Return the shape of the value space on the reference cell.

- **property** `property reference_value_size: int`
  Return the integer product of the reference value shape.

- **property** `abstract property sobolev_space: SobolevSpace`
  Return the underlying Sobolev space.

- **property** `abstract property sub_elements: Sequence`
  Return list of sub-elements.
  This function does not recurse: ie it does not extract the sub-elements
  of sub-elements.

- **class** `class ufl.classes.AbstractFunctionSpace`
  Bases: object
  Abstract function space.

Bases: object

Abstract function space.

- **method** `ufl_sub_spaces()`
  Return ufl sub spaces.

- **class** `class ufl.classes.AbstractPullback`
  Bases: ABC
  An abstract pull back.

Bases: ABC

An abstract pull back.

- **method** `apply(expr: Expr, domain: AbstractDomain | None = None) → Expr`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `abstract property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `abstractmethod physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.Acos(argument)`
  Bases: MathFunction
  Inverse cosine.

- **class** `class ufl.classes.Action(*args, **kw)`
  Bases: BaseForm
  UFL base form type: respresents the action of an object on another.

Bases: BaseForm

UFL base form type: respresents the action of an object on another.

- `For example:`
  res = Ax

A would be the first argument, left and x would be the second argument,
right.

Action objects will result when the action of an assembled object
(e.g. a Matrix) is taken. This delays the evaluation of the action until
assembly occurs.

- **method** `equals(other)`
  Check if two Actions are equal.

- **method** `left()`
  Get left.

- **method** `right()`
  Get right.

- **method** `ufl_domains()`
  Return all domains found in the base form.

- **method** `ufl_function_spaces()`
  Get the tuple of function spaces of the underlying form.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.classes.Adjoint(*args, **kw)`
  Bases: BaseForm
  UFL base form type: represents the adjoint of an object.
  Adjoint objects will result when the adjoint of an assembled object
  (e.g. a Matrix) is taken. This delays the evaluation of the adjoint until
  assembly occurs.

Bases: BaseForm

UFL base form type: represents the adjoint of an object.

Adjoint objects will result when the adjoint of an assembled object
(e.g. a Matrix) is taken. This delays the evaluation of the adjoint until
assembly occurs.

- **method** `equals(other)`
  Check if two Adjoints are equal.

- **method** `form()`
  Return the form.

- **method** `ufl_domains()`
  Return all domains found in the base form.

- **method** `ufl_function_spaces()`
  Get the tuple of function spaces of the underlying form.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.classes.AndCondition(left, right)`
  Bases: BinaryCondition
  And condition.

Bases: BinaryCondition

And condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.classes.Argument(*args, **kw)`
  Bases: FormArgument, BaseArgument
  UFL value: Representation of an argument to a form.

Bases: FormArgument, BaseArgument

UFL value: Representation of an argument to a form.

- **method** `ufl_domains()`
  Return UFL domains.

- **class** `class ufl.classes.Asin(argument)`
  Bases: MathFunction
  Inverse sine.

- **class** `class ufl.classes.Atan(argument)`
  Bases: MathFunction
  Inverse tangent.

- **class** `class ufl.classes.Atan2(arg1, arg2)`
  Bases: Operator
  Inverse tangent with two inputs.

Bases: Operator

Inverse tangent with two inputs.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.BaseForm`
  Bases: object
  Description of an object containing arguments.

Bases: object

Description of an object containing arguments.

- **method** `arguments()`
  Return all Argument objects found in form.

- **method** `coefficients()`
  Return all Coefficient objects found in form.

- **method** `empty()`
  Returns whether the BaseForm has no components.

- **method** `geometric_quantities()`
  Return all GeometricQuantity objects found in form.

- **method** `ufl_domain()`
  Return the single geometric integration domain occuring in the base form.
  Fails if multiple domains are found.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.classes.BaseFormCoordinateDerivative(integrand, coefficients, arguments, coefficient_derivatives)`
  Bases: BaseFormDerivative, CoordinateDerivative
  Derivative of a base form w.r.t. the SpatialCoordinates.

Bases: BaseFormDerivative, CoordinateDerivative

Derivative of a base form w.r.t. the SpatialCoordinates.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.BaseFormDerivative(integrand, coefficients, arguments, coefficient_derivatives)`
  Bases: CoefficientDerivative, BaseForm
  Derivative of a base form w.r.t the degrees of freedom in a discrete Coefficient.

Bases: CoefficientDerivative, BaseForm

Derivative of a base form w.r.t the degrees of freedom in a discrete Coefficient.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.BaseFormOperator(*operands, function_space, derivatives=None, argument_slots=())`
  Bases: Operator, BaseForm, Counted
  Base form operator.

Bases: Operator, BaseForm, Counted

Base form operator.

- **method** `argument_slots(outer_form=False)`
  Returns a tuple of expressions containing argument and coefficient based expressions.
  We get an argument uhat when we take the Gateaux derivative in
  the direction uhat: d/du N(u; v*) = dNdu(u; uhat, v*) where uhat
  is a ufl.Argument and v* a ufl.Coargument Applying the action
  replace the last argument by coefficient: action(dNdu(u; uhat,
  v*), w) = dNdu(u; w, v*) where du is a ufl.Coefficient.

- **method** `coefficients()`
  Return all BaseCoefficient objects found in base form operator.

- **method** `count()`
  Return the count associated to the base form operator.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **method** `ufl_function_space()`
  Return the function space associated to the operator.
  I.e. return the dual of the base form operator’s Coargument space.

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **property** `property ufl_shape`
  Return the UFL shape of the coefficient produced by the operator.

- **class** `class ufl.classes.BaseFormOperatorCoordinateDerivative(integrand, coefficients, arguments, coefficient_derivatives)`
  Bases: BaseFormOperatorDerivative, CoordinateDerivative
  Derivative of a base form operator w.r.t. the SpatialCoordinates.

Bases: BaseFormOperatorDerivative, CoordinateDerivative

Derivative of a base form operator w.r.t. the SpatialCoordinates.

- **property** `property ufl_free_indices`
  Built-in immutable sequence.
  If no argument is given, the constructor returns an empty tuple.
  If iterable is specified the tuple is initialized from iterable’s items.
  If the argument is a tuple, the return value is the same object.

- **property** `property ufl_index_dimensions`
  Built-in immutable sequence.
  If no argument is given, the constructor returns an empty tuple.
  If iterable is specified the tuple is initialized from iterable’s items.
  If the argument is a tuple, the return value is the same object.

- **property** `property ufl_shape`
  Return the UFL shape of the coefficient produced by the operator.

- **class** `class ufl.classes.BaseFormOperatorDerivative(integrand, coefficients, arguments, coefficient_derivatives)`
  Bases: BaseFormDerivative, BaseFormOperator
  Derivative of a base form operator w.r.t the degrees of freedom in a discrete Coefficient.

Bases: BaseFormDerivative, BaseFormOperator

Derivative of a base form operator w.r.t the degrees of freedom in a discrete Coefficient.

- **method** `argument_slots(outer_form=False)`
  Return a tuple of expressions containing argument and coefficient based expressions.

- **property** `property ufl_free_indices`
  Built-in immutable sequence.
  If no argument is given, the constructor returns an empty tuple.
  If iterable is specified the tuple is initialized from iterable’s items.
  If the argument is a tuple, the return value is the same object.

- **property** `property ufl_index_dimensions`
  Built-in immutable sequence.
  If no argument is given, the constructor returns an empty tuple.
  If iterable is specified the tuple is initialized from iterable’s items.
  If the argument is a tuple, the return value is the same object.

- **property** `property ufl_shape`
  Return the UFL shape of the coefficient produced by the operator.

- **class** `class ufl.classes.BesselFunction(name, nu, argument)`
  Bases: Operator
  Base class for all bessel functions.

Bases: Operator

Base class for all bessel functions.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.BesselI(nu, argument)`
  Bases: BesselFunction
  Bessel I function.

- **class** `class ufl.classes.BesselJ(nu, argument)`
  Bases: BesselFunction
  Bessel J function.

- **class** `class ufl.classes.BesselK(nu, argument)`
  Bases: BesselFunction
  Bessel K function.

- **class** `class ufl.classes.BesselY(nu, argument)`
  Bases: BesselFunction
  Bessel Y function.

- **class** `class ufl.classes.BinaryCondition(name, left, right)`
  Bases: Condition
  Binary condition.

- **class** `class ufl.classes.Cell(cellname: str)`
  Bases: AbstractCell
  Representation of a named finite element cell with known structure.

Bases: AbstractCell

Representation of a named finite element cell with known structure.

- **method** `cellname() → str`
  Return the cellname of the cell.

- **method** `has_simplex_facets() → bool`
  Return True if all the facets of this cell are simplex cells.

- **method** `is_simplex() → bool`
  Return True if this is a simplex cell.

- **method** `num_sub_entities(dim: int) → int`
  Get the number of sub-entities of the given dimension.

- **method** `reconstruct(**kwargs: Any) → Cell`
  Reconstruct this cell, overwriting properties by those in kwargs.

- **method** `sub_entities(dim: int) → tuple[AbstractCell, ...]`
  Get the sub-entities of the given dimension.

- **method** `sub_entity_types(dim: int) → tuple[AbstractCell, ...]`
  Get the unique sub-entity types of the given dimension.

- **method** `topological_dimension() → int`
  Return the dimension of the topology of this cell.

- **class** `class ufl.classes.CellAvg(f)`
  Bases: Operator
  Cell average.

Bases: Operator

Cell average.

- **method** `evaluate(x, mapping, component, index_values)`
  Performs an approximate symbolic evaluation, since we don’t have a cell.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.CellCoordinate(domain)`
  Bases: GeometricCellQuantity
  The coordinate in a reference cell.
  In the context of expression integration,
  represents the reference cell coordinate of each quadrature point.
  In the context of expression evaluation in a point in a cell,
  represents that point in the reference coordinate system of the cell.

Bases: GeometricCellQuantity

The coordinate in a reference cell.

In the context of expression integration,
represents the reference cell coordinate of each quadrature point.

In the context of expression evaluation in a point in a cell,
represents that point in the reference coordinate system of the cell.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'X'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.CellDiameter(domain)`
  Bases: GeometricCellQuantity
  The diameter of the cell, i.e., maximal distance of two points in the cell.

Bases: GeometricCellQuantity

The diameter of the cell, i.e., maximal distance of two points in the cell.

- **attribute** `name = 'diameter'`

- **class** `class ufl.classes.CellEdgeVectors(domain)`
  Bases: GeometricCellQuantity
  The vectors between physical cell vertices for each edge in cell.

Bases: GeometricCellQuantity

The vectors between physical cell vertices for each edge in cell.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'CEV'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.CellFacetJacobian(domain)`
  Bases: GeometricFacetQuantity
  The Jacobian of the mapping from reference facet to reference cell coordinates.
  CFJ_ij = dX_i/dXf_j

Bases: GeometricFacetQuantity

The Jacobian of the mapping from reference facet to reference cell coordinates.

CFJ_ij = dX_i/dXf_j

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'CFJ'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.CellFacetJacobianDeterminant(domain)`
  Bases: GeometricFacetQuantity
  The pseudo-determinant of the CellFacetJacobian.

Bases: GeometricFacetQuantity

The pseudo-determinant of the CellFacetJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'detCFJ'`

- **class** `class ufl.classes.CellFacetJacobianInverse(domain)`
  Bases: GeometricFacetQuantity
  The pseudo-inverse of the CellFacetJacobian.

Bases: GeometricFacetQuantity

The pseudo-inverse of the CellFacetJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'CFK'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.CellFacetOrigin(domain)`
  Bases: GeometricFacetQuantity
  The reference cell coordinate corresponding to origin of a reference facet.

Bases: GeometricFacetQuantity

The reference cell coordinate corresponding to origin of a reference facet.

- **attribute** `name = 'X0f'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.CellNormal(domain)`
  Bases: GeometricCellQuantity
  The upwards pointing normal vector of the current manifold cell.

Bases: GeometricCellQuantity

The upwards pointing normal vector of the current manifold cell.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'cell_normal'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.classes.CellOrientation(domain)`
  Bases: GeometricCellQuantity
  The orientation (+1/-1) of the current cell.
  For non-manifold cells (tdim == gdim), this equals the sign
  of the Jacobian determinant, i.e. +1 if the physical cell is
  oriented the same way as the reference cell and -1 otherwise.
  For manifold cells of tdim==gdim-1 this is input data belonging
  to the mesh, used to distinguish between the sides of the manifold.

Bases: GeometricCellQuantity

The orientation (+1/-1) of the current cell.

For non-manifold cells (tdim == gdim), this equals the sign
of the Jacobian determinant, i.e. +1 if the physical cell is
oriented the same way as the reference cell and -1 otherwise.

For manifold cells of tdim==gdim-1 this is input data belonging
to the mesh, used to distinguish between the sides of the manifold.

- **attribute** `name = 'cell_orientation'`

- **class** `class ufl.classes.CellOrigin(domain)`
  Bases: GeometricCellQuantity
  The spatial coordinate corresponding to origin of a reference cell.

Bases: GeometricCellQuantity

The spatial coordinate corresponding to origin of a reference cell.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'x0'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.CellRidgeJacobian(domain)`
  Bases: GeometricRidgeQuantity
  The Jacobian of the mapping from reference ridge to reference cell coordinates.
  CRJ_ij = dX_i/dXe_j

Bases: GeometricRidgeQuantity

The Jacobian of the mapping from reference ridge to reference cell coordinates.

CRJ_ij = dX_i/dXe_j

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'CRJ'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.CellRidgeJacobianDeterminant(domain)`
  Bases: GeometricRidgeQuantity
  The pseudo-determinant of the CellRidgeJacobian.

Bases: GeometricRidgeQuantity

The pseudo-determinant of the CellRidgeJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'detCRJ'`

- **class** `class ufl.classes.CellRidgeJacobianInverse(domain)`
  Bases: GeometricRidgeQuantity
  The pseudo-inverse of the RidgeFacetJacobian.

Bases: GeometricRidgeQuantity

The pseudo-inverse of the RidgeFacetJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'CEK'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.CellRidgeOrigin(domain)`
  Bases: GeometricRidgeQuantity
  The reference cell coordinate corresponding to origin of a reference ridge.

Bases: GeometricRidgeQuantity

The reference cell coordinate corresponding to origin of a reference ridge.

- **attribute** `name = 'X0e'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.CellVertices(domain)`
  Bases: GeometricCellQuantity
  Physical cell vertices.

Bases: GeometricCellQuantity

Physical cell vertices.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'CV'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.CellVolume(domain)`
  Bases: GeometricCellQuantity
  The volume of the cell.

Bases: GeometricCellQuantity

The volume of the cell.

- **attribute** `name = 'volume'`

- **class** `class ufl.classes.Circumradius(domain)`
  Bases: GeometricCellQuantity
  The circumradius of the cell.

Bases: GeometricCellQuantity

The circumradius of the cell.

- **attribute** `name = 'circumradius'`

- **class** `class ufl.classes.Coargument(*args, **kw)`
  Bases: BaseForm, BaseArgument
  UFL value: Representation of an argument to a form in a dual space.

Bases: BaseForm, BaseArgument

UFL value: Representation of an argument to a form in a dual space.

- **method** `arguments(outer_form=None)`
  Return all Argument objects found in form.

- **method** `equals(other)`
  Check equality.

- **method** `ufl_domain()`
  Return the UFL domain.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.classes.Coefficient(*args, **kw)`
  Bases: FormArgument, BaseCoefficient
  UFL form argument type: Representation of a form coefficient.

Bases: FormArgument, BaseCoefficient

UFL form argument type: Representation of a form coefficient.

- **method** `ufl_domains()`
  Get the UFL domains.

- **class** `class ufl.classes.CoefficientDerivative(integrand, coefficients, arguments, coefficient_derivatives)`
  Bases: Derivative
  Derivative of form integrand w.r.t. the degrees of freedom in a discrete Coefficient.

Bases: Derivative

Derivative of form integrand w.r.t. the degrees of freedom in a discrete Coefficient.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.Cofactor(A)`
  Bases: CompoundTensorOperator
  Cofactor.

Bases: CompoundTensorOperator

Cofactor.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.Cofunction(*args, **kw)`
  Bases: BaseCoefficient, BaseForm
  UFL form argument type: Representation of a form coefficient from a dual space.

Bases: BaseCoefficient, BaseForm

UFL form argument type: Representation of a form coefficient from a dual space.

- **method** `equals(other)`
  Check equality.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.classes.ComplexValue(value)`
  Bases: ScalarValue
  Representation of a constant, complex scalar.

Bases: ScalarValue

Representation of a constant, complex scalar.

- **method** `argument()`
  Get the argument.

- **method** `modulus()`
  Get the modulus.

- **class** `class ufl.classes.ComponentTensor(expression, indices)`
  Bases: Operator
  Maps the free indices of a scalar valued expression to tensor axes.

Bases: Operator

Maps the free indices of a scalar valued expression to tensor axes.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **method** `indices()`
  Get indices.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.CompoundDerivative(operands)`
  Bases: Derivative
  Base class for all compound derivative types.

Bases: Derivative

Base class for all compound derivative types.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.CompoundTensorOperator(operands)`
  Bases: Operator
  Compount tensor operator.

Bases: Operator

Compount tensor operator.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.Condition(operands)`
  Bases: Operator
  Condition.

Bases: Operator

Condition.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.Conditional(condition, true_value, false_value)`
  Bases: Operator
  Conditional expression.
  In C++ these take the format (condition ? true_value : false_value).

Bases: Operator

Conditional expression.

In C++ these take the format (condition ? true_value : false_value).

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.Conj(a)`
  Bases: Operator
  Complex conjugate.

Bases: Operator

Complex conjugate.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.Constant(domain, shape=(), count=None)`
  Bases: Terminal, Counted
  Constant.

Bases: Terminal, Counted

Constant.

- **method** `is_cellwise_constant()`
  Return True if the function is cellwise constant.

- **method** `ufl_domain()`
  Get the UFL domain.

- **method** `ufl_domains()`
  Get the UFL domains.

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.ConstantValue`
  Bases: Terminal
  Constant value.

Bases: Terminal

Constant value.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **method** `ufl_domains()`
  Return tuple of domains related to this terminal object.

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.ContravariantPiola`
  Bases: AbstractPullback
  The contravariant Piola pull back.

Bases: AbstractPullback

The contravariant Piola pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.CoordinateDerivative(integrand, coefficients, arguments, coefficient_derivatives)`
  Bases: CoefficientDerivative
  Derivative of the integrand of a form w.r.t. the SpatialCoordinates.

Bases: CoefficientDerivative

Derivative of the integrand of a form w.r.t. the SpatialCoordinates.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.Cos(argument)`
  Bases: MathFunction
  Cosine.

- **class** `class ufl.classes.Cosh(argument)`
  Bases: MathFunction
  Hyperbolic cosine.

- **class** `class ufl.classes.CovariantContravariantPiola`
  Bases: AbstractPullback
  The covariant contravariant Piola pull back.

Bases: AbstractPullback

The covariant contravariant Piola pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element.

Get the physical value shape when this pull back is applied to an element.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.CovariantPiola`
  Bases: AbstractPullback
  The covariant Piola pull back.

Bases: AbstractPullback

The covariant Piola pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.Cross(a, b)`
  Bases: CompoundTensorOperator
  Cross.

Bases: CompoundTensorOperator

Cross.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = (3,)`

- **class** `class ufl.classes.Curl(f)`
  Bases: CompoundDerivative
  Compound derivative.

Bases: CompoundDerivative

Compound derivative.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.CustomPullback`
  Bases: AbstractPullback
  Custom pull back.
  This should probably be removed.

Bases: AbstractPullback

Custom pull back.

This should probably be removed.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.Derivative(operands)`
  Bases: Operator
  Base class for all derivative types.

Bases: Operator

Base class for all derivative types.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.Determinant(A)`
  Bases: CompoundTensorOperator
  Determinant.

Bases: CompoundTensorOperator

Determinant.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.Deviatoric(A)`
  Bases: CompoundTensorOperator
  Deviatoric.

Bases: CompoundTensorOperator

Deviatoric.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.DirectionalSobolevSpace(orders)`
  Bases: SobolevSpace
  Directional Sobolev space.
  Symbolic representation of a Sobolev space with varying smoothness
  in different spatial directions.

- **class** `class ufl.classes.Div(f)`
  Bases: CompoundDerivative
  Div.

Bases: CompoundDerivative

Div.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.Division(a, b)`
  Bases: Operator
  Division.

Bases: Operator

Division.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.Dot(a, b)`
  Bases: CompoundTensorOperator
  Dot.

Bases: CompoundTensorOperator

Dot.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.DoubleContravariantPiola`
  Bases: AbstractPullback
  The double contravariant Piola pull back.

Bases: AbstractPullback

The double contravariant Piola pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.DoubleCovariantPiola`
  Bases: AbstractPullback
  The double covariant Piola pull back.

Bases: AbstractPullback

The double covariant Piola pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.DualSpace(domain, element, label='')`
  Bases: BaseFunctionSpace, UFLObject
  Representation of a Dual space.

Bases: BaseFunctionSpace, UFLObject

Representation of a Dual space.

- **method** `dual()`
  Get the dual of the space.

- **class** `class ufl.classes.EQ(left, right)`
  Bases: BinaryCondition
  Equality condition.

Bases: BinaryCondition

Equality condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.classes.Equation(lhs, rhs)`
  Bases: object
  Equation.
  This class is used to represent equations expressed by the “==”
  operator. Examples include a == L and F == 0 where a, L and F are
  Form objects.

- **class** `class ufl.classes.Erf(argument)`
  Bases: MathFunction
  Erf function.

Bases: MathFunction

Erf function.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.classes.Exp(argument)`
  Bases: MathFunction
  Exponentiation..

- **class** `class ufl.classes.Expr`
  Bases: object
  Base class for all UFL expression types.

Bases: object

Base class for all UFL expression types.

- `Instance properties`
  Every Expr instance will have certain properties.
  The most important ones are ufl_operands, ufl_shape,
  ufl_free_indices, and ufl_index_dimensions properties.
  Expressions are immutable and hashable.

- `Type traits`
  The Expr API defines a number of type traits that each subclass
  needs to provide. Most of these are specified indirectly via
  the arguments to the ufl_type class decorator, allowing UFL
  to do some consistency checks and automate most of the traits
  for most types. Type traits are accessed via a class or
  instance object of the form obj._ufl_traitname_. See the source
  code for description of each type trait.

- `Operators`
  Some Python special functions are implemented in this class,
  some are implemented in subclasses, and some are attached to
  this class in the ufl_type class decorator.

- `Defining subclasses`
  To define a new expression class, inherit from either
  Terminal or Operator, and apply the ufl_type class
  decorator with suitable arguments.  See the docstring of
  ufl_type for details on its arguments.  Looking at existing
  classes similar to the one you wish to add is a good
  idea. Looking through the comments in the Expr class and
  ufl_type to understand all the properties that may need to
  be specified is also a good idea. Note that many algorithms in
  UFL and form compilers will need handlers implemented for each
  new type::.

- `Type collections`
  All Expr subclasses are collected by ufl_type in global
  variables available via Expr.

- `Profiling`
  Object creation statistics can be collected by doing
  Giving a list of creation and deletion counts for each typecode.

- **property** `property T`
  Transpose a rank-2 tensor expression.
  For more general transpose operations of higher order tensor
  expressions, use indexing and Tensor.

- **method** `dx(*ii)`
  Return the partial derivative with respect to spatial variable number ii.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate expression at given coordinate with given values for terminals.

- **method** `static ufl_disable_profiling()`
  Turn off the object counting mechanism. Return object init and del counts.

- **method** `ufl_domain()`
  Return the single unique domain this expression is defined on, or throw an error.

- **method** `ufl_domains()`
  Return all domains this expression is defined on.

- **method** `static ufl_enable_profiling()`
  Turn on the object counting mechanism and reset counts to zero.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.ExprList(*operands)`
  Bases: Operator
  List of Expr objects. For internal use, never to be created by end users.

Bases: Operator

List of Expr objects. For internal use, never to be created by end users.

- **method** `free_indices()`
  Get the free indices.

- **method** `index_dimensions()`
  Get the index dimensions.

- **property** `property ufl_free_indices`
  Get the UFL free indices.

- **property** `property ufl_index_dimensions`
  Get the UFL index dimensions.

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.ExprMapping(*operands)`
  Bases: Operator
  Mapping of Expr objects. For internal use, never to be created by end users.

Bases: Operator

Mapping of Expr objects. For internal use, never to be created by end users.

- **method** `free_indices()`
  Get the free indices.

- **method** `index_dimensions()`
  Get the index dimensions.

- **method** `ufl_domains()`
  Get the UFL domains.

- **property** `property ufl_free_indices`
  Get the UFL free indices.

- **property** `property ufl_index_dimensions`
  Get the UFL index dimensions.

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.ExternalOperator(*operands, function_space, derivatives=None, argument_slots=())`
  Bases: BaseFormOperator
  External operator.

Bases: BaseFormOperator

External operator.

- **method** `assemble(*args, **kwargs)`
  Assemble the external operator.

- **method** `grad()`
  Returns the symbolic grad of the external operator.

- **method** `ufl_element()`
  Shortcut to get the finite element of the function space of the external operator.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.classes.FacetArea(domain)`
  Bases: GeometricFacetQuantity
  The area of the facet.

Bases: GeometricFacetQuantity

The area of the facet.

- **attribute** `name = 'facetarea'`

- **class** `class ufl.classes.FacetAvg(f)`
  Bases: Operator
  Facet average.

Bases: Operator

Facet average.

- **method** `evaluate(x, mapping, component, index_values)`
  Performs an approximate symbolic evaluation, since we dont have a cell.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.FacetCoordinate(domain)`
  Bases: GeometricFacetQuantity
  The coordinate in a reference cell of a facet.
  In the context of expression integration over a facet,
  represents the reference facet coordinate of each quadrature point.
  In the context of expression evaluation in a point on a facet,
  represents that point in the reference coordinate system of the facet.

Bases: GeometricFacetQuantity

The coordinate in a reference cell of a facet.

In the context of expression integration over a facet,
represents the reference facet coordinate of each quadrature point.

In the context of expression evaluation in a point on a facet,
represents that point in the reference coordinate system of the facet.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'Xf'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.FacetEdgeVectors(domain)`
  Bases: GeometricFacetQuantity
  The vectors between physical cell vertices for each edge in current facet.

Bases: GeometricFacetQuantity

The vectors between physical cell vertices for each edge in current facet.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'FEV'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.FacetJacobian(domain)`
  Bases: GeometricFacetQuantity
  The Jacobian of the mapping from reference facet to spatial coordinates.
  The FacetJacobian is the product of the Jacobian and CellFacetJacobian:

Bases: GeometricFacetQuantity

The Jacobian of the mapping from reference facet to spatial coordinates.

The FacetJacobian is the product of the Jacobian and CellFacetJacobian:

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'FJ'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.FacetJacobianDeterminant(domain)`
  Bases: GeometricFacetQuantity
  The pseudo-determinant of the FacetJacobian.

Bases: GeometricFacetQuantity

The pseudo-determinant of the FacetJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'detFJ'`

- **class** `class ufl.classes.FacetJacobianInverse(domain)`
  Bases: GeometricFacetQuantity
  The pseudo-inverse of the FacetJacobian.

Bases: GeometricFacetQuantity

The pseudo-inverse of the FacetJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'FK'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.FacetNormal(domain)`
  Bases: GeometricFacetQuantity
  The outwards pointing normal vector of the current facet.

Bases: GeometricFacetQuantity

The outwards pointing normal vector of the current facet.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'n'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.classes.FacetOrientation(domain)`
  Bases: GeometricFacetQuantity
  The orientation (+1/-1) of the current facet relative to the reference cell.

Bases: GeometricFacetQuantity

The orientation (+1/-1) of the current facet relative to the reference cell.

- **attribute** `name = 'facet_orientation'`

- **class** `class ufl.classes.FacetOrigin(domain)`
  Bases: GeometricFacetQuantity
  The spatial coordinate corresponding to origin of a reference facet.

Bases: GeometricFacetQuantity

The spatial coordinate corresponding to origin of a reference facet.

- **attribute** `name = 'x0f'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.FacetRidgeJacobian(domain)`
  Bases: GeometricRidgeQuantity
  The Jacobian of the mapping from reference ridge to reference facet coordinates.
  FRJ_ij = dXf_i/dXe_j

Bases: GeometricRidgeQuantity

The Jacobian of the mapping from reference ridge to reference facet coordinates.

FRJ_ij = dXf_i/dXe_j

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'FRJ'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.FixedIndex(value)`
  Bases: IndexBase
  UFL value: An index with a specific value assigned.

- **class** `class ufl.classes.FloatValue(value)`
  Bases: RealValue
  Representation of a constant scalar floating point value.

- **class** `class ufl.classes.Form(integrals)`
  Bases: BaseForm
  Description of a weak form consisting of a sum of integrals over subdomains.

Bases: BaseForm

Description of a weak form consisting of a sum of integrals over subdomains.

- **method** `base_form_operators()`
  Return all BaseFormOperator objects found in form.

- **method** `coefficient_numbering()`
  Return a contiguous numbering of coefficients in a mapping {coefficient:number}.

- **method** `coefficients()`
  Return all Coefficient objects found in form.

- **method** `constant_numbering()`
  Return a contiguous numbering of constants in a mapping {constant:number}.

- **method** `constants()`
  Get constants.

- **method** `domain_numbering()`
  Return a contiguous numbering of domains in a mapping {domain:number}.

- **method** `empty()`
  Returns whether the form has no integrals.

- **method** `equals(other)`
  Evaluate bool(lhs_form == rhs_form).

- **method** `geometric_dimension()`
  Return the geometric dimension shared by all domains and functions in this form.

- **method** `integrals()`
  Return a sequence of all integrals in form.

- **method** `integrals_by_domain(domain)`
  Return a sequence of all integrals with a particular integration domain.

- **method** `integrals_by_type(integral_type)`
  Return a sequence of all integrals with a particular domain type.

- **method** `signature()`
  Signature for use with jit cache (independent of incidental numbering of indices etc).

- **method** `subdomain_data()`
  Returns a mapping on the form {domain:{integral_type: subdomain_data}}.

- **method** `terminal_numbering()`
  Return a contiguous numbering for all counted objects in the form.
  The returned object is mapping from terminal to its number (an integer).
  The numbering is computed per type so Coefficient,
  Constant, etc will each be numbered from zero.

- **method** `ufl_cell()`
  Return the single cell this form is defined on.
  Fails if multiple cells are found.

- **method** `ufl_domains()`
  Return the geometric integration domains occuring in the form.
  NB! This does not include domains of coefficients defined on
  other meshes.
  The return type is a tuple even if only a single domain exists.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.classes.FormArgument`
  Bases: Terminal
  An abstract class for a form argument (a thing in a primal finite element space).

Bases: Terminal

An abstract class for a form argument (a thing in a primal finite element space).

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.FormSum(*args, **kwargs)`
  Bases: BaseForm
  Form sum.
  Description of a weighted sum of variational forms and form-like objects
  components is the list of Forms to be summed
  arg_weights is a list of tuples of component index and weight

Bases: BaseForm

Form sum.

Description of a weighted sum of variational forms and form-like objects
components is the list of Forms to be summed
arg_weights is a list of tuples of component index and weight

- **method** `components()`
  Get components.

- **method** `empty()`
  Returns whether the FormSum has no components.

- **method** `equals(other)`
  Evaluate bool(lhs_form == rhs_form).

- **method** `ufl_domains()`
  Return all domains found in the base form.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **method** `weights()`
  Get weights.

- **class** `class ufl.classes.FunctionSpace(domain, element, label='')`
  Bases: BaseFunctionSpace, UFLObject
  Representation of a Function space.

Bases: BaseFunctionSpace, UFLObject

Representation of a Function space.

- **method** `dual()`
  Get the dual of the space.

- **class** `class ufl.classes.GE(left, right)`
  Bases: BinaryCondition
  Greater than or equal to condition.

Bases: BinaryCondition

Greater than or equal to condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.classes.GT(left, right)`
  Bases: BinaryCondition
  Greater than condition.

Bases: BinaryCondition

Greater than condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.classes.GeometricCellQuantity(domain)`
  Bases: GeometricQuantity
  Geometric cell quantity.

- **class** `class ufl.classes.GeometricFacetQuantity(domain)`
  Bases: GeometricQuantity
  Geometric facet quantity.

- **class** `class ufl.classes.GeometricQuantity(domain)`
  Bases: Terminal
  Geometric quantity.

Bases: Terminal

Geometric quantity.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **method** `ufl_domains()`
  Get the UFL domains.

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.GeometricRidgeQuantity(domain)`
  Bases: GeometricQuantity
  Geometric ridge quantity.

- **class** `class ufl.classes.Grad(f)`
  Bases: CompoundDerivative
  Grad.

Bases: CompoundDerivative

Grad.

- **method** `evaluate(x, mapping, component, index_values, derivatives=())`
  Get child from mapping and return the component asked for.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.Identity(dim)`
  Bases: ConstantValue
  Representation of an identity matrix.

Bases: ConstantValue

Representation of an identity matrix.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.IdentityPullback`
  Bases: AbstractPullback
  The identity pull back.

Bases: AbstractPullback

The identity pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.Imag(a)`
  Bases: Operator
  Imaginary part.

Bases: Operator

Imaginary part.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.Index(count=None)`
  Bases: IndexBase, Counted
  UFL value: An index with no value assigned.
  Used to represent free indices in Einstein indexing notation.

- **class** `class ufl.classes.IndexBase`
  Bases: object
  Base class for all indices.

- **class** `class ufl.classes.IndexSum(summand, index)`
  Bases: Operator
  Index sum.

Bases: Operator

Index sum.

- **method** `dimension()`
  Get dimension.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **method** `index()`
  Get index.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **property** `property ufl_shape`
  Get UFL shape.

- **class** `class ufl.classes.Indexed(expression, multiindex)`
  Bases: Operator
  Indexed expression.

Bases: Operator

Indexed expression.

- **method** `evaluate(x, mapping, component, index_values, derivatives=())`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.Inner(a, b)`
  Bases: CompoundTensorOperator
  Inner.

Bases: CompoundTensorOperator

Inner.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.IntValue(value)`
  Bases: RealValue
  Representation of a constant scalar integer value.

- **class** `class ufl.classes.Integral(integrand, integral_type, domain, subdomain_id, metadata, subdomain_data)`
  Bases: object
  An integral over a single domain.

Bases: object

An integral over a single domain.

- **method** `integral_type()`
  Return the domain type of this integral.

- **method** `integrand()`
  Return the integrand expression, which is an Expr instance.

- **method** `metadata()`
  Return the compiler metadata this integral has been annotated with.

- **method** `reconstruct(integrand=None, integral_type=None, domain=None, subdomain_id=None, metadata=None, subdomain_data=None)`
  Construct a new Integral object with some properties replaced with new values.

Construct a new Integral object with some properties replaced with new values.

- `Example:`
  <a = Integral instance>
  b = a.reconstruct(expand_compounds(a.integrand()))
  c = a.reconstruct(metadata={‘quadrature_degree’:2})

- **method** `subdomain_data()`
  Return the domain data of this integral.

- **method** `subdomain_id()`
  Return the subdomain id of this integral.

- **method** `ufl_domain()`
  Return the integration domain of this integral.

- **class** `class ufl.classes.Interpolate(expr, v)`
  Bases: BaseFormOperator
  Symbolic representation of the interpolation operator.

Bases: BaseFormOperator

Symbolic representation of the interpolation operator.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.classes.Inverse(A)`
  Bases: CompoundTensorOperator
  Inverse.

Bases: CompoundTensorOperator

Inverse.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.Jacobian(domain)`
  Bases: GeometricCellQuantity
  The Jacobian of the mapping from reference cell to spatial coordinates.

Bases: GeometricCellQuantity

The Jacobian of the mapping from reference cell to spatial coordinates.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'J'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.classes.JacobianDeterminant(domain)`
  Bases: GeometricCellQuantity
  The determinant of the Jacobian.
  Represents the signed determinant of a square Jacobian or the
  pseudo-determinant of a non-square Jacobian.

Bases: GeometricCellQuantity

The determinant of the Jacobian.

Represents the signed determinant of a square Jacobian or the
pseudo-determinant of a non-square Jacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'detJ'`

- **class** `class ufl.classes.JacobianInverse(domain)`
  Bases: GeometricCellQuantity
  The inverse of the Jacobian.
  Represents the inverse of a square Jacobian or the pseudo-inverse of
  a non-square Jacobian.

Bases: GeometricCellQuantity

The inverse of the Jacobian.

Represents the inverse of a square Jacobian or the pseudo-inverse of
a non-square Jacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'K'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.classes.L2Piola`
  Bases: AbstractPullback
  The L2 Piola pull back.

Bases: AbstractPullback

The L2 Piola pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.LE(left, right)`
  Bases: BinaryCondition
  Less than or equal condition.

Bases: BinaryCondition

Less than or equal condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.classes.LT(left, right)`
  Bases: BinaryCondition
  Less than condition.

Bases: BinaryCondition

Less than condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.classes.Label(count=None)`
  Bases: Terminal, Counted
  Label.

Bases: Terminal, Counted

Label.

- **method** `is_cellwise_constant()`
  Return true if the object is constant on each cell.

- **method** `ufl_domains()`
  Return tuple of domains related to this terminal object.

- **property** `property ufl_free_indices`
  Get the UFL free indices.

- **property** `property ufl_index_dimensions`
  Get the UFL index dimensions.

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.ListTensor(*expressions)`
  Bases: Operator
  Wraps a list of expressions into a tensor valued expression of one higher rank.

Bases: Operator

Wraps a list of expressions into a tensor valued expression of one higher rank.

- **method** `evaluate(x, mapping, component, index_values, derivatives=())`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.Ln(argument)`
  Bases: MathFunction
  Natural logarithm.

Bases: MathFunction

Natural logarithm.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.classes.MathFunction(name, argument)`
  Bases: Operator
  Base class for all unary scalar math functions.

Bases: Operator

Base class for all unary scalar math functions.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.Matrix(row_space, column_space, count=None)`
  Bases: BaseForm, Counted
  An assemble linear operator between two function spaces.

Bases: BaseForm, Counted

An assemble linear operator between two function spaces.

- **method** `equals(other)`
  Check equality.

- **method** `ufl_function_spaces()`
  Get the tuple of function spaces of this coefficient.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.classes.MaxCellEdgeLength(domain)`
  Bases: GeometricCellQuantity
  The maximum edge length of the cell.

Bases: GeometricCellQuantity

The maximum edge length of the cell.

- **attribute** `name = 'maxcelledgelength'`

- **class** `class ufl.classes.MaxFacetEdgeLength(domain)`
  Bases: GeometricFacetQuantity
  The maximum edge length of the facet.

Bases: GeometricFacetQuantity

The maximum edge length of the facet.

- **attribute** `name = 'maxfacetedgelength'`

- **class** `class ufl.classes.MaxValue(left, right)`
  Bases: Operator
  Take the maximum of two values.

Bases: Operator

Take the maximum of two values.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.Measure(integral_type, domain=None, subdomain_id='everywhere', metadata=None, subdomain_data=None)`
  Bases: object
  Representation of an integration measure.
  The Measure object holds information about integration properties
  to be transferred to a Form on multiplication with a scalar
  expression.

Bases: object

Representation of an integration measure.

The Measure object holds information about integration properties
to be transferred to a Form on multiplication with a scalar
expression.

- **method** `integral_type()`
  Return the domain type.
  Valid domain types are “cell”, “exterior_facet”, “interior_facet”, etc.

- **method** `metadata()`
  Return the integral metadata.
  This data is not interpreted by UFL.
  It is passed to the form compiler which can ignore it or use
  it to compile each integral of a form in a different way.

- **method** `reconstruct(integral_type=None, subdomain_id=None, domain=None, metadata=None, subdomain_data=None)`
  Construct a new Measure object with some properties replaced with new values.

Construct a new Measure object with some properties replaced with new values.

- `Example:`
  <dm = Measure instance>
  b = dm.reconstruct(subdomain_id=2)
  c = dm.reconstruct(metadata={ “quadrature_degree”: 3 })

- `Used by the call operator, so this is equivalent:`
  b = dm(2)
  c = dm(0, { “quadrature_degree”: 3 })

- **method** `subdomain_data()`
  Return the integral subdomain_data.
  This data is not interpreted by
  UFL.  Its intension is to give a context in which the domain
  id is interpreted.

- **method** `subdomain_id()`
  Return the domain id of this measure (integer).

- **method** `ufl_domain()`
  Return the domain associated with this measure.
  This may be None or a Domain object.

- **class** `class ufl.classes.MeasureProduct(*measures)`
  Bases: object
  Represents a product of measures.
  This is a notational intermediate object to handle the notation
  This is work in progress and not functional. It needs support
  in other parts of ufl and the rest of the code generation chain.

Bases: object

Represents a product of measures.

This is a notational intermediate object to handle the notation

This is work in progress and not functional. It needs support
in other parts of ufl and the rest of the code generation chain.

- **method** `sub_measures()`
  Return submeasures.

- **class** `class ufl.classes.MeasureSum(*measures)`
  Bases: object
  Represents a sum of measures.

Bases: object

Represents a sum of measures.

- `This is a notational intermediate object to translate the notation`
  f*(ds(1)+ds(3))

- `into`
  f*ds(1) + f*ds(3)

- **class** `class ufl.classes.Mesh(coordinate_element, ufl_id=None, cargo=None)`
  Bases: AbstractDomain, UFLObject
  Symbolic representation of a mesh.

Bases: AbstractDomain, UFLObject

Symbolic representation of a mesh.

- **method** `can_make_function_space(element: AbstractFiniteElement) → bool`
  Check whether this mesh can make a function space with element.

- **method** `is_piecewise_linear_simplex_domain()`
  Check if the domain is a piecewise linear simplex.

- **method** `iterable_like(element: AbstractFiniteElement) → Iterable[Mesh]`
  Return iterable object that is iterable like element.

- **property** `property meshes`
  Return the component meshes.

- **method** `ufl_cargo()`
  Return carried object that will not be used by UFL.

- **method** `ufl_cell()`
  Get the cell.

- **method** `ufl_coordinate_element()`
  Get the coordinate element.

- **method** `ufl_id()`
  Return the ufl_id of this object.

- **class** `class ufl.classes.MeshView(mesh, topological_dimension, ufl_id=None)`
  Bases: AbstractDomain, UFLObject
  Symbolic representation of a mesh.

Bases: AbstractDomain, UFLObject

Symbolic representation of a mesh.

- **method** `is_piecewise_linear_simplex_domain()`
  Check if the domain is a piecewise linear simplex.

- **method** `ufl_cell()`
  Get the cell.

- **method** `ufl_id()`
  Return the ufl_id of this object.

- **method** `ufl_mesh()`
  Get the mesh.

- **class** `class ufl.classes.MinCellEdgeLength(domain)`
  Bases: GeometricCellQuantity
  The minimum edge length of the cell.

Bases: GeometricCellQuantity

The minimum edge length of the cell.

- **attribute** `name = 'mincelledgelength'`

- **class** `class ufl.classes.MinFacetEdgeLength(domain)`
  Bases: GeometricFacetQuantity
  The minimum edge length of the facet.

Bases: GeometricFacetQuantity

The minimum edge length of the facet.

- **attribute** `name = 'minfacetedgelength'`

- **class** `class ufl.classes.MinValue(left, right)`
  Bases: Operator
  Take the minimum of two values.

Bases: Operator

Take the minimum of two values.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.MixedFunctionSpace(*args)`
  Bases: AbstractFunctionSpace, UFLObject
  Mixed function space.

Bases: AbstractFunctionSpace, UFLObject

Mixed function space.

- **method** `dual(*args)`
  Return the dual to this function space.
  If no additional arguments are passed then a MixedFunctionSpace is
  returned whose components are the duals of the originals.
  If additional arguments are passed, these must be integers. In this
  case, the MixedFunctionSpace which is returned will have dual
  components in the positions corresponding to the arguments passed, and
  the original components in the other positions.

- **method** `num_sub_spaces()`
  Return number of subspaces.

- **method** `ufl_domain()`
  Return ufl domain.

- **method** `ufl_domains()`
  Return ufl domains.

- **method** `ufl_element()`
  Return ufl element.

- **method** `ufl_elements()`
  Return ufl elements.

- **method** `ufl_sub_space(i)`
  Return i-th ufl sub space.

- **method** `ufl_sub_spaces()`
  Return ufl sub spaces.

- **class** `class ufl.classes.MixedPullback(element: _AbstractFiniteElement)`
  Bases: AbstractPullback
  Pull back for a mixed element.

Bases: AbstractPullback

Pull back for a mixed element.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.MultiIndex(indices)`
  Bases: Terminal
  Represents a sequence of indices, either fixed or free.

Bases: Terminal

Represents a sequence of indices, either fixed or free.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate index.

- **method** `indices()`
  Return tuple of indices.

- **method** `is_cellwise_constant()`
  Check if cellwise constant.
  Always True.

- **method** `ufl_domains()`
  Return tuple of domains related to this terminal object.

- **property** `property ufl_free_indices`
  Get the UFL free indices.
  This should not be used.

- **property** `property ufl_index_dimensions`
  Get the UFL index dimensions.
  This should not be used.

- **property** `property ufl_shape`
  Get the UFL shape.
  This should not be used.

- **class** `class ufl.classes.NE(left, right)`
  Bases: BinaryCondition
  Not equal condition.

Bases: BinaryCondition

Not equal condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.classes.NablaDiv(f)`
  Bases: CompoundDerivative
  Nabla div.

Bases: CompoundDerivative

Nabla div.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.NablaGrad(f)`
  Bases: CompoundDerivative
  Nabla grad.

Bases: CompoundDerivative

Nabla grad.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.NegativeRestricted(expression)`
  Bases: Restricted
  Negative restriction.

- **exception** `exception ufl.classes.NonStandardPullbackException`
  Bases: BaseException
  Exception to raise if a map is non-standard.

- **class** `class ufl.classes.NotCondition(condition)`
  Bases: Condition
  Not condition.

Bases: Condition

Not condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.classes.Operator(operands=None)`
  Bases: Expr
  Base class for all operators, i.e. non-terminal expression types.

Bases: Expr

Base class for all operators, i.e. non-terminal expression types.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.OrCondition(left, right)`
  Bases: BinaryCondition
  Or condition.

Bases: BinaryCondition

Or condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.classes.Outer(a, b)`
  Bases: CompoundTensorOperator
  Outer.

Bases: CompoundTensorOperator

Outer.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.PermutationSymbol(dim)`
  Bases: ConstantValue
  Representation of a permutation symbol.
  This is also known as the Levi-Civita symbol, antisymmetric symbol,
  or alternating symbol.

Bases: ConstantValue

Representation of a permutation symbol.

This is also known as the Levi-Civita symbol, antisymmetric symbol,
or alternating symbol.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.Perp(A)`
  Bases: CompoundTensorOperator
  Perp.

Bases: CompoundTensorOperator

Perp.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = (2,)`

- **class** `class ufl.classes.PhysicalPullback`
  Bases: AbstractPullback
  Physical pull back.
  This should probably be removed.

Bases: AbstractPullback

Physical pull back.

This should probably be removed.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.PositiveRestricted(expression)`
  Bases: Restricted
  Positive restriction.

- **class** `class ufl.classes.Power(a, b)`
  Bases: Operator
  Power.

Bases: Operator

Power.

- **method** `evaluate(x, mapping, component, index_values)`
  Evalute.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.Product(a, b)`
  Bases: Operator
  The product of two or more UFL objects.

Bases: Operator

The product of two or more UFL objects.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.QuadratureWeight(domain)`
  Bases: GeometricQuantity
  The current quadrature weight.
  Only used inside a quadrature context.

Bases: GeometricQuantity

The current quadrature weight.

Only used inside a quadrature context.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'weight'`

- **class** `class ufl.classes.Real(a)`
  Bases: Operator
  Real part.

Bases: Operator

Real part.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.RealValue(value)`
  Bases: ScalarValue
  Abstract class used to differentiate real values from complex ones.

Bases: ScalarValue

Abstract class used to differentiate real values from complex ones.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.ReferenceCellEdgeVectors(domain)`
  Bases: GeometricCellQuantity
  The vectors between reference cell vertices for each edge in cell.

Bases: GeometricCellQuantity

The vectors between reference cell vertices for each edge in cell.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'RCEV'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.ReferenceCellVolume(domain)`
  Bases: GeometricCellQuantity
  The volume of the reference cell.

Bases: GeometricCellQuantity

The volume of the reference cell.

- **attribute** `name = 'reference_cell_volume'`

- **class** `class ufl.classes.ReferenceCurl(f)`
  Bases: CompoundDerivative
  Reference curl.

Bases: CompoundDerivative

Reference curl.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.ReferenceDiv(f)`
  Bases: CompoundDerivative
  Reference divergence.

Bases: CompoundDerivative

Reference divergence.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.ReferenceFacetEdgeVectors(domain)`
  Bases: GeometricFacetQuantity
  The vectors between reference cell vertices for each edge in current facet.

Bases: GeometricFacetQuantity

The vectors between reference cell vertices for each edge in current facet.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'RFEV'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.ReferenceFacetVolume(domain)`
  Bases: GeometricFacetQuantity
  The volume of the reference cell of the current facet.

Bases: GeometricFacetQuantity

The volume of the reference cell of the current facet.

- **attribute** `name = 'reference_facet_volume'`

- **class** `class ufl.classes.ReferenceGrad(f)`
  Bases: CompoundDerivative
  Reference grad.

Bases: CompoundDerivative

Reference grad.

- **method** `evaluate(x, mapping, component, index_values, derivatives=())`
  Get child from mapping and return the component asked for.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.ReferenceNormal(domain)`
  Bases: GeometricFacetQuantity
  The outwards pointing normal vector of the current facet on the reference cell.

Bases: GeometricFacetQuantity

The outwards pointing normal vector of the current facet on the reference cell.

- **attribute** `name = 'reference_normal'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.ReferenceRidgeVolume(domain)`
  Bases: GeometricRidgeQuantity
  The volume of the reference cell of the current ridge.

Bases: GeometricRidgeQuantity

The volume of the reference cell of the current ridge.

- **attribute** `name = 'reference_ridge_volume'`

- **class** `class ufl.classes.ReferenceValue(f)`
  Bases: Operator
  Representation of the reference cell value of a form argument.

Bases: Operator

Representation of the reference cell value of a form argument.

- **method** `evaluate(x, mapping, component, index_values, derivatives=())`
  Get child from mapping and return the component asked for.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.Restricted(expression)`
  Bases: Operator
  Restriction.

Bases: Operator

Restriction.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **method** `side()`
  Get the side.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.RidgeCoordinate(domain)`
  Bases: GeometricRidgeQuantity
  The coordinate in a reference cell of a ridge.
  In the context of expression integration over a ridge,
  represents the reference ridge coordinate of each quadrature point.
  In the context of expression evaluation in a point on a ridge,
  represents that point in the reference coordinate system of the ridge.

Bases: GeometricRidgeQuantity

The coordinate in a reference cell of a ridge.

In the context of expression integration over a ridge,
represents the reference ridge coordinate of each quadrature point.

In the context of expression evaluation in a point on a ridge,
represents that point in the reference coordinate system of the ridge.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'Xe'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.RidgeJacobian(domain)`
  Bases: GeometricRidgeQuantity
  The Jacobian of the mapping from reference ridge to spatial coordinates.
  The RidgeJacobian is the product of the Jacobian and CellRidgeJacobian:

Bases: GeometricRidgeQuantity

The Jacobian of the mapping from reference ridge to spatial coordinates.

The RidgeJacobian is the product of the Jacobian and CellRidgeJacobian:

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'RJ'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.RidgeJacobianDeterminant(domain)`
  Bases: GeometricRidgeQuantity
  The pseudo-determinant of the RidgeJacobian.

Bases: GeometricRidgeQuantity

The pseudo-determinant of the RidgeJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'detRJ'`

- **class** `class ufl.classes.RidgeJacobianInverse(domain)`
  Bases: GeometricRidgeQuantity
  The pseudo-inverse of the RidgeJacobian.

Bases: GeometricRidgeQuantity

The pseudo-inverse of the RidgeJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'EK'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.RidgeOrigin(domain)`
  Bases: GeometricRidgeQuantity
  The spatial coordinate corresponding to origin of a reference ridge.

Bases: GeometricRidgeQuantity

The spatial coordinate corresponding to origin of a reference ridge.

- **attribute** `name = 'x0e'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.classes.ScalarValue(value)`
  Bases: ConstantValue
  A constant scalar value.

Bases: ConstantValue

A constant scalar value.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **method** `imag()`
  Imaginary part.

- **method** `real()`
  Real part.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **method** `value()`
  Get the value.

- **class** `class ufl.classes.Sin(argument)`
  Bases: MathFunction
  Sine.

- **class** `class ufl.classes.Sinh(argument)`
  Bases: MathFunction
  Hyperbolic sine.

- **class** `class ufl.classes.Skew(A)`
  Bases: CompoundTensorOperator
  Skew.

Bases: CompoundTensorOperator

Skew.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.SobolevSpace(name, parents=None)`
  Bases: object
  Symbolic representation of a Sobolev space.
  This implements a subset of the methods of a Python set so that
  finite elements and other Sobolev spaces can be tested for
  inclusion.

- **class** `class ufl.classes.SpatialCoordinate(domain)`
  Bases: GeometricCellQuantity
  The coordinate in a domain.
  In the context of expression integration,
  represents the domain coordinate of each quadrature point.
  In the context of expression evaluation in a point,
  represents the value of that point.

Bases: GeometricCellQuantity

The coordinate in a domain.

In the context of expression integration,
represents the domain coordinate of each quadrature point.

In the context of expression evaluation in a point,
represents the value of that point.

- **method** `count()`
  Count.

- **method** `evaluate(x, mapping, component, index_values)`
  Return the value of the coordinate.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'x'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.classes.Sqrt(argument)`
  Bases: MathFunction
  Square root.

- **class** `class ufl.classes.Sum(a, b)`
  Bases: Operator
  Sum.

Bases: Operator

Sum.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.Sym(A)`
  Bases: CompoundTensorOperator
  Sym.

Bases: CompoundTensorOperator

Sym.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.classes.SymmetricPullback(element: _AbstractFiniteElement, symmetry: dict[tuple[int, ...], int])`
  Bases: AbstractPullback
  Pull back for an element with symmetry.

Bases: AbstractPullback

Pull back for an element with symmetry.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.Tan(argument)`
  Bases: MathFunction
  Tangent.

- **class** `class ufl.classes.Tanh(argument)`
  Bases: MathFunction
  Hyperbolic tangent.

- **class** `class ufl.classes.TensorProductCell(*cells: AbstractCell)`
  Bases: AbstractCell
  Tensor product cell.

Bases: AbstractCell

Tensor product cell.

- **method** `cellname() → str`
  Return the cellname of the cell.

- **method** `has_simplex_facets() → bool`
  Return True if all the facets of this cell are simplex cells.

- **method** `is_simplex() → bool`
  Return True if this is a simplex cell.

- **method** `num_sub_entities(dim: int) → int`
  Get the number of sub-entities of the given dimension.

- **method** `reconstruct(**kwargs: Any) → AbstractCell`
  Reconstruct this cell, overwriting properties by those in kwargs.

- **method** `sub_cells() → tuple[AbstractCell, ...]`
  Return list of cell factors.

- **method** `sub_entities(dim: int) → tuple[AbstractCell, ...]`
  Get the sub-entities of the given dimension.

- **method** `sub_entity_types(dim: int) → tuple[AbstractCell, ...]`
  Get the unique sub-entity types of the given dimension.

- **method** `topological_dimension() → int`
  Return the dimension of the topology of this cell.

- **class** `class ufl.classes.TensorProductFunctionSpace(*function_spaces)`
  Bases: AbstractFunctionSpace, UFLObject
  Tensor product function space.

Bases: AbstractFunctionSpace, UFLObject

Tensor product function space.

- **method** `ufl_sub_spaces()`
  Return ufl sub spaces.

- **class** `class ufl.classes.Terminal`
  Bases: Expr
  Base class for terminal objects.
  A terminal node in the UFL expression tree.

Bases: Expr

Base class for terminal objects.

A terminal node in the UFL expression tree.

- **method** `evaluate(x, mapping, component, index_values, derivatives=())`
  Get self from mapping and return the component asked for.

- **method** `ufl_domains()`
  Return tuple of domains related to this terminal object.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_operands: tuple[FormArgument, ...] = ()`

- **attribute** `ufl_shape: tuple[int, ...]`

- **function** `ufl.classes.TestFunction(function_space, part=None)`
  UFL value: Create a test function argument to a form.

- **function** `ufl.classes.TestFunctions(function_space)`
  Create a TestFunction in a mixed space.
  Returns a tuple with the function components corresponding to the
  subelements.

- **class** `class ufl.classes.Trace(A)`
  Bases: CompoundTensorOperator
  Trace.

Bases: CompoundTensorOperator

Trace.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.classes.Transposed(A)`
  Bases: CompoundTensorOperator
  Transposed tensor.

Bases: CompoundTensorOperator

Transposed tensor.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **function** `ufl.classes.TrialFunction(function_space, part=None)`
  UFL value: Create a trial function argument to a form.

- **function** `ufl.classes.TrialFunctions(function_space)`
  Create a TrialFunction in a mixed space.
  Returns a tuple with the function components corresponding to the
  subelements.

- **class** `class ufl.classes.UndefinedPullback`
  Bases: AbstractPullback
  Undefined pull back.
  This should probably be removed.

Bases: AbstractPullback

Undefined pull back.

This should probably be removed.

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.classes.Variable(expression, label=None)`
  Bases: Operator
  A Variable is a representative for another expression.
  It will be used by the end-user mainly for defining
  a quantity to differentiate w.r.t. using diff.
  Example:

Bases: Operator

A Variable is a representative for another expression.

It will be used by the end-user mainly for defining
a quantity to differentiate w.r.t. using diff.
Example:

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **method** `expression()`
  Get expression.

- **method** `label()`
  Get label.

- **method** `ufl_domains()`
  Get the UFL domains.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **property** `property ufl_shape`

- **class** `class ufl.classes.VariableDerivative(f, v)`
  Bases: Derivative
  Variable Derivative.

Bases: Derivative

Variable Derivative.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.Zero(shape=(), free_indices=(), index_dimensions=None)`
  Bases: ConstantValue
  Representation of a zero valued expression.
  Class for representing zero tensors of different shapes.

Bases: ConstantValue

Representation of a zero valued expression.

Class for representing zero tensors of different shapes.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.classes.ZeroBaseForm(arguments)`
  Bases: BaseForm
  Description of a zero base form.
  ZeroBaseForm is idempotent with respect to assembly and is mostly
  used for sake of simplifying base-form expressions.

Bases: BaseForm

Description of a zero base form.

ZeroBaseForm is idempotent with respect to assembly and is mostly
used for sake of simplifying base-form expressions.

- **attribute** `form`

- **method** `ufl_domains()`
  Return all domains found in the base form.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

## ufl.coefficient module

This module defines the Coefficient class and a number of related classes, including Constant.

- **class** `class ufl.coefficient.BaseCoefficient(function_space, count=None)`
  Bases: Counted
  UFL form argument type: Parent Representation of a form coefficient.

Bases: Counted

UFL form argument type: Parent Representation of a form coefficient.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **method** `ufl_domain()`
  Shortcut to get the domain of the function space of this coefficient.

- **method** `ufl_domains()`
  Return tuple of domains related to this terminal object.

- **method** `ufl_element()`
  Shortcut to get the finite element of the function space of this coefficient.

- **method** `ufl_function_space()`
  Get the function space of this coefficient.

- **property** `property ufl_shape`
  Return the associated UFL shape.

- **class** `class ufl.coefficient.Coefficient(*args, **kw)`
  Bases: FormArgument, BaseCoefficient
  UFL form argument type: Representation of a form coefficient.

Bases: FormArgument, BaseCoefficient

UFL form argument type: Representation of a form coefficient.

- **method** `ufl_domains()`
  Get the UFL domains.

- **function** `ufl.coefficient.Coefficients(function_space)`
  Create a Coefficient in a mixed space.
  Returns a tuple with the function components corresponding to the subelements.

- **class** `class ufl.coefficient.Cofunction(*args, **kw)`
  Bases: BaseCoefficient, BaseForm
  UFL form argument type: Representation of a form coefficient from a dual space.

Bases: BaseCoefficient, BaseForm

UFL form argument type: Representation of a form coefficient from a dual space.

- **method** `equals(other)`
  Check equality.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

## ufl.compound_expressions module

Support for compound expressions as equivalent representations using basic operators.

- **function** `ufl.compound_expressions.adj_expr(A)`
  Adjoint of a matrix.

- **function** `ufl.compound_expressions.adj_expr_2x2(A)`
  Adjoint of a 2 by 2 matrix.

- **function** `ufl.compound_expressions.adj_expr_3x3(A)`
  Adjoint of a 3 by 3 matrix.

- **function** `ufl.compound_expressions.adj_expr_4x4(A)`
  Adjoint of a 4 by 4 matrix.

- **function** `ufl.compound_expressions.codeterminant_expr_nxn(A, rows, cols)`
  Determinant of a n by n matrix.

- **function** `ufl.compound_expressions.cofactor_expr(A)`
  Cofactor of a matrix.

- **function** `ufl.compound_expressions.cofactor_expr_2x2(A)`
  Cofactor of a 2 by 2 matrix.

- **function** `ufl.compound_expressions.cofactor_expr_3x3(A)`
  Cofactor of a 3 by 3 matrix.

- **function** `ufl.compound_expressions.cofactor_expr_4x4(A)`
  Cofactor of a 4 by 4 matrix.

- **function** `ufl.compound_expressions.cross_expr(a, b)`
  Symbolic cross product.

- **function** `ufl.compound_expressions.determinant_expr(A)`
  Compute the (pseudo-)determinant of A.

- **function** `ufl.compound_expressions.determinant_expr_2x2(B)`
  Determinant of a 2 by 2 matrix.

- **function** `ufl.compound_expressions.determinant_expr_3x3(A)`
  Determinant of a 3 by 3 matrix.

- **function** `ufl.compound_expressions.determinant_expr_nxn(A)`
  Determinant of a n by n matrix.

- **function** `ufl.compound_expressions.deviatoric_expr(A)`
  Deviatoric of a matrix.

- **function** `ufl.compound_expressions.deviatoric_expr_2x2(A)`
  Deviatoric of a 2 by 2 matrix.

- **function** `ufl.compound_expressions.deviatoric_expr_3x3(A)`
  Deviatoric of a 3 by 3 matrix.

- **function** `ufl.compound_expressions.generic_pseudo_determinant_expr(A)`
  Compute the pseudo-determinant of A: sqrt(det(A.T*A)).

- **function** `ufl.compound_expressions.generic_pseudo_inverse_expr(A)`
  Compute the Penrose-Moore pseudo-inverse of A: (A.T*A)^-1 * A.T.

- **function** `ufl.compound_expressions.inverse_expr(A)`
  Compute the inverse of A.

- **function** `ufl.compound_expressions.pseudo_determinant_expr(A)`
  Compute the pseudo-determinant of A.

- **function** `ufl.compound_expressions.pseudo_inverse_expr(A)`
  Compute the Penrose-Moore pseudo-inverse of A: (A.T*A)^-1 * A.T.

## ufl.conditional module

This module defines classes for conditional expressions.

- **class** `class ufl.conditional.AndCondition(left, right)`
  Bases: BinaryCondition
  And condition.

Bases: BinaryCondition

And condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.conditional.BinaryCondition(name, left, right)`
  Bases: Condition
  Binary condition.

- **class** `class ufl.conditional.Condition(operands)`
  Bases: Operator
  Condition.

Bases: Operator

Condition.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.conditional.Conditional(condition, true_value, false_value)`
  Bases: Operator
  Conditional expression.
  In C++ these take the format (condition ? true_value : false_value).

Bases: Operator

Conditional expression.

In C++ these take the format (condition ? true_value : false_value).

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.conditional.EQ(left, right)`
  Bases: BinaryCondition
  Equality condition.

Bases: BinaryCondition

Equality condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.conditional.GE(left, right)`
  Bases: BinaryCondition
  Greater than or equal to condition.

Bases: BinaryCondition

Greater than or equal to condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.conditional.GT(left, right)`
  Bases: BinaryCondition
  Greater than condition.

Bases: BinaryCondition

Greater than condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.conditional.LE(left, right)`
  Bases: BinaryCondition
  Less than or equal condition.

Bases: BinaryCondition

Less than or equal condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.conditional.LT(left, right)`
  Bases: BinaryCondition
  Less than condition.

Bases: BinaryCondition

Less than condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.conditional.MaxValue(left, right)`
  Bases: Operator
  Take the maximum of two values.

Bases: Operator

Take the maximum of two values.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.conditional.MinValue(left, right)`
  Bases: Operator
  Take the minimum of two values.

Bases: Operator

Take the minimum of two values.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.conditional.NE(left, right)`
  Bases: BinaryCondition
  Not equal condition.

Bases: BinaryCondition

Not equal condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.conditional.NotCondition(condition)`
  Bases: Condition
  Not condition.

Bases: Condition

Not condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.conditional.OrCondition(left, right)`
  Bases: BinaryCondition
  Or condition.

Bases: BinaryCondition

Or condition.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

## ufl.constant module

Support fpr non-literal values which are constant with respect to a domain.

- **class** `class ufl.constant.Constant(domain, shape=(), count=None)`
  Bases: Terminal, Counted
  Constant.

Bases: Terminal, Counted

Constant.

- **method** `is_cellwise_constant()`
  Return True if the function is cellwise constant.

- **method** `ufl_domain()`
  Get the UFL domain.

- **method** `ufl_domains()`
  Get the UFL domains.

- **property** `property ufl_shape`
  Get the UFL shape.

- **function** `ufl.constant.TensorConstant(domain, count=None)`
  Tensor constant.

- **function** `ufl.constant.VectorConstant(domain, count=None)`
  Vector constant.

## ufl.constantvalue module

This module defines classes representing constant values.

- **class** `class ufl.constantvalue.ComplexValue(value)`
  Bases: ScalarValue
  Representation of a constant, complex scalar.

Bases: ScalarValue

Representation of a constant, complex scalar.

- **method** `argument()`
  Get the argument.

- **method** `modulus()`
  Get the modulus.

- **class** `class ufl.constantvalue.ConstantValue`
  Bases: Terminal
  Constant value.

Bases: Terminal

Constant value.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **method** `ufl_domains()`
  Return tuple of domains related to this terminal object.

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.constantvalue.FloatValue(value)`
  Bases: RealValue
  Representation of a constant scalar floating point value.

- **class** `class ufl.constantvalue.Identity(dim)`
  Bases: ConstantValue
  Representation of an identity matrix.

Bases: ConstantValue

Representation of an identity matrix.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.constantvalue.IntValue(value)`
  Bases: RealValue
  Representation of a constant scalar integer value.

- **class** `class ufl.constantvalue.PermutationSymbol(dim)`
  Bases: ConstantValue
  Representation of a permutation symbol.
  This is also known as the Levi-Civita symbol, antisymmetric symbol,
  or alternating symbol.

Bases: ConstantValue

Representation of a permutation symbol.

This is also known as the Levi-Civita symbol, antisymmetric symbol,
or alternating symbol.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.constantvalue.RealValue(value)`
  Bases: ScalarValue
  Abstract class used to differentiate real values from complex ones.

Bases: ScalarValue

Abstract class used to differentiate real values from complex ones.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.constantvalue.ScalarValue(value)`
  Bases: ConstantValue
  A constant scalar value.

Bases: ConstantValue

A constant scalar value.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **method** `imag()`
  Imaginary part.

- **method** `real()`
  Real part.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **method** `value()`
  Get the value.

- **class** `class ufl.constantvalue.Zero(shape=(), free_indices=(), index_dimensions=None)`
  Bases: ConstantValue
  Representation of a zero valued expression.
  Class for representing zero tensors of different shapes.

Bases: ConstantValue

Representation of a zero valued expression.

Class for representing zero tensors of different shapes.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...]`

- **function** `ufl.constantvalue.as_ufl(expression)`
  Converts expression to an Expr if possible.

- **function** `ufl.constantvalue.format_float(x)`
  Format float value based on global UFL precision.

- **function** `ufl.constantvalue.zero(*shape)`
  UFL literal constant: Return a zero tensor with the given shape.

## ufl.differentiation module

Differential operators.

- **class** `class ufl.differentiation.BaseFormCoordinateDerivative(integrand, coefficients, arguments, coefficient_derivatives)`
  Bases: BaseFormDerivative, CoordinateDerivative
  Derivative of a base form w.r.t. the SpatialCoordinates.

Bases: BaseFormDerivative, CoordinateDerivative

Derivative of a base form w.r.t. the SpatialCoordinates.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.differentiation.BaseFormDerivative(integrand, coefficients, arguments, coefficient_derivatives)`
  Bases: CoefficientDerivative, BaseForm
  Derivative of a base form w.r.t the degrees of freedom in a discrete Coefficient.

Bases: CoefficientDerivative, BaseForm

Derivative of a base form w.r.t the degrees of freedom in a discrete Coefficient.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.differentiation.BaseFormOperatorCoordinateDerivative(integrand, coefficients, arguments, coefficient_derivatives)`
  Bases: BaseFormOperatorDerivative, CoordinateDerivative
  Derivative of a base form operator w.r.t. the SpatialCoordinates.

Bases: BaseFormOperatorDerivative, CoordinateDerivative

Derivative of a base form operator w.r.t. the SpatialCoordinates.

- **property** `property ufl_free_indices`
  Built-in immutable sequence.
  If no argument is given, the constructor returns an empty tuple.
  If iterable is specified the tuple is initialized from iterable’s items.
  If the argument is a tuple, the return value is the same object.

- **property** `property ufl_index_dimensions`
  Built-in immutable sequence.
  If no argument is given, the constructor returns an empty tuple.
  If iterable is specified the tuple is initialized from iterable’s items.
  If the argument is a tuple, the return value is the same object.

- **property** `property ufl_shape`
  Return the UFL shape of the coefficient produced by the operator.

- **class** `class ufl.differentiation.BaseFormOperatorDerivative(integrand, coefficients, arguments, coefficient_derivatives)`
  Bases: BaseFormDerivative, BaseFormOperator
  Derivative of a base form operator w.r.t the degrees of freedom in a discrete Coefficient.

Bases: BaseFormDerivative, BaseFormOperator

Derivative of a base form operator w.r.t the degrees of freedom in a discrete Coefficient.

- **method** `argument_slots(outer_form=False)`
  Return a tuple of expressions containing argument and coefficient based expressions.

- **property** `property ufl_free_indices`
  Built-in immutable sequence.
  If no argument is given, the constructor returns an empty tuple.
  If iterable is specified the tuple is initialized from iterable’s items.
  If the argument is a tuple, the return value is the same object.

- **property** `property ufl_index_dimensions`
  Built-in immutable sequence.
  If no argument is given, the constructor returns an empty tuple.
  If iterable is specified the tuple is initialized from iterable’s items.
  If the argument is a tuple, the return value is the same object.

- **property** `property ufl_shape`
  Return the UFL shape of the coefficient produced by the operator.

- **class** `class ufl.differentiation.CoefficientDerivative(integrand, coefficients, arguments, coefficient_derivatives)`
  Bases: Derivative
  Derivative of form integrand w.r.t. the degrees of freedom in a discrete Coefficient.

Bases: Derivative

Derivative of form integrand w.r.t. the degrees of freedom in a discrete Coefficient.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.differentiation.CompoundDerivative(operands)`
  Bases: Derivative
  Base class for all compound derivative types.

Bases: Derivative

Base class for all compound derivative types.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.differentiation.CoordinateDerivative(integrand, coefficients, arguments, coefficient_derivatives)`
  Bases: CoefficientDerivative
  Derivative of the integrand of a form w.r.t. the SpatialCoordinates.

Bases: CoefficientDerivative

Derivative of the integrand of a form w.r.t. the SpatialCoordinates.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.differentiation.Curl(f)`
  Bases: CompoundDerivative
  Compound derivative.

Bases: CompoundDerivative

Compound derivative.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.differentiation.Derivative(operands)`
  Bases: Operator
  Base class for all derivative types.

Bases: Operator

Base class for all derivative types.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.differentiation.Div(f)`
  Bases: CompoundDerivative
  Div.

Bases: CompoundDerivative

Div.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.differentiation.Grad(f)`
  Bases: CompoundDerivative
  Grad.

Bases: CompoundDerivative

Grad.

- **method** `evaluate(x, mapping, component, index_values, derivatives=())`
  Get child from mapping and return the component asked for.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.differentiation.NablaDiv(f)`
  Bases: CompoundDerivative
  Nabla div.

Bases: CompoundDerivative

Nabla div.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.differentiation.NablaGrad(f)`
  Bases: CompoundDerivative
  Nabla grad.

Bases: CompoundDerivative

Nabla grad.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.differentiation.ReferenceCurl(f)`
  Bases: CompoundDerivative
  Reference curl.

Bases: CompoundDerivative

Reference curl.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.differentiation.ReferenceDiv(f)`
  Bases: CompoundDerivative
  Reference divergence.

Bases: CompoundDerivative

Reference divergence.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.differentiation.ReferenceGrad(f)`
  Bases: CompoundDerivative
  Reference grad.

Bases: CompoundDerivative

Reference grad.

- **method** `evaluate(x, mapping, component, index_values, derivatives=())`
  Get child from mapping and return the component asked for.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.differentiation.VariableDerivative(f, v)`
  Bases: Derivative
  Variable Derivative.

Bases: Derivative

Variable Derivative.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...]`

## ufl.domain module

Types for representing a geometric domain.

- **class** `class ufl.domain.AbstractDomain(topological_dimension, geometric_dimension)`
  Bases: object
  Symbolic representation of a geometric domain.
  Domain has only a geometric and a topological dimension.

Bases: object

Symbolic representation of a geometric domain.

Domain has only a geometric and a topological dimension.

- **method** `can_make_function_space(element: AbstractFiniteElement) → bool`
  Check whether this mesh can make a function space with element.

- **method** `geometric_dimension()`
  Return the dimension of the space this domain is embedded in.

- **method** `iterable_like(element: AbstractFiniteElement) → Iterable[Mesh] | MeshSequence`
  Return iterable object that is iterable like element.

- **property** `property meshes`
  Return the component meshes.

- **method** `topological_dimension()`
  Return the dimension of the topology of this domain.

- **class** `class ufl.domain.Mesh(coordinate_element, ufl_id=None, cargo=None)`
  Bases: AbstractDomain, UFLObject
  Symbolic representation of a mesh.

Bases: AbstractDomain, UFLObject

Symbolic representation of a mesh.

- **method** `can_make_function_space(element: AbstractFiniteElement) → bool`
  Check whether this mesh can make a function space with element.

- **method** `is_piecewise_linear_simplex_domain()`
  Check if the domain is a piecewise linear simplex.

- **method** `iterable_like(element: AbstractFiniteElement) → Iterable[Mesh]`
  Return iterable object that is iterable like element.

- **property** `property meshes`
  Return the component meshes.

- **method** `ufl_cargo()`
  Return carried object that will not be used by UFL.

- **method** `ufl_cell()`
  Get the cell.

- **method** `ufl_coordinate_element()`
  Get the coordinate element.

- **method** `ufl_id()`
  Return the ufl_id of this object.

- **class** `class ufl.domain.MeshSequence(meshes: Sequence[Mesh])`
  Bases: AbstractDomain, UFLObject
  Symbolic representation of a mixed mesh.
  This class represents a collection of meshes that, along with
  a MixedElement, represent a mixed function space defined on
  multiple domains. This abstraction allows for defining the
  mixed function space with the conventional FunctionSpace
  class and integrating multi-domain problems seamlessly.
  Currently, all component meshes must have the same cell type (and
  thus the same topological dimension).
  Currently, one can only perform cell integrations when
  MeshSequence is used.

Bases: AbstractDomain, UFLObject

Symbolic representation of a mixed mesh.

This class represents a collection of meshes that, along with
a MixedElement, represent a mixed function space defined on
multiple domains. This abstraction allows for defining the
mixed function space with the conventional FunctionSpace
class and integrating multi-domain problems seamlessly.

Currently, all component meshes must have the same cell type (and
thus the same topological dimension).

Currently, one can only perform cell integrations when
MeshSequence is used.

- **method** `can_make_function_space(element: AbstractFiniteElement) → bool`
  Check whether this mesh can make a function space with element.

- **method** `iterable_like(element: AbstractFiniteElement) → MeshSequence`
  Return iterable object that is iterable like element.

- **property** `property meshes`
  Return the component meshes.

- **method** `ufl_cell()`
  Get the cell.

- **class** `class ufl.domain.MeshView(mesh, topological_dimension, ufl_id=None)`
  Bases: AbstractDomain, UFLObject
  Symbolic representation of a mesh.

Bases: AbstractDomain, UFLObject

Symbolic representation of a mesh.

- **method** `is_piecewise_linear_simplex_domain()`
  Check if the domain is a piecewise linear simplex.

- **method** `ufl_cell()`
  Get the cell.

- **method** `ufl_id()`
  Return the ufl_id of this object.

- **method** `ufl_mesh()`
  Get the mesh.

- **function** `ufl.domain.as_domain(domain)`
  Convert any valid object to an AbstractDomain type.

- **function** `ufl.domain.extract_domains(expr: Expr | Form, expand_mesh_sequence: bool = True)`
  Return all domains expression is defined on.

Return all domains expression is defined on.

- `Args:`
  expr: Expr or Form.
  expand_mesh_sequence: If True, MeshSequence components are expanded.

- `Returns:`
  tuple of domains.

- **function** `ufl.domain.extract_unique_domain(expr, expand_mesh_sequence: bool = True)`
  Return the single unique domain expression is defined on or throw an error.

Return the single unique domain expression is defined on or throw an error.

- `Args:`
  expr: Expr or Form.
  expand_mesh_sequence: If True, MeshSequence components are expanded.

- `Returns:`
  domain.

- **function** `ufl.domain.find_geometric_dimension(expr)`
  Find the geometric dimension of an expression.

- **function** `ufl.domain.join_domains(domains: Sequence[AbstractDomain], expand_mesh_sequence: bool = True)`
  Take a list of domains and return a set with only unique domain objects.

Take a list of domains and return a set with only unique domain objects.

- `Args:`
  domains: Sequence of domains.
  expand_mesh_sequence: If True, MeshSequence components are expanded.

- `Returns:`
  set of domains.

- **function** `ufl.domain.sort_domains(domains: Sequence[AbstractDomain])`
  Sort domains in a canonical ordering.

Sort domains in a canonical ordering.

- `Args:`
  domains: Sequence of domains.

- `Returns:`
  tuple of sorted domains.

## ufl.duals module

Predicates for recognising duals.

- **function** `ufl.duals.is_dual(object)`
  Determine if the object belongs to a dual space.
  This is not simply the negation of is_primal,
  because a mixed function space containing both primal
  and dual components is neither primal nor dual.

- **function** `ufl.duals.is_primal(object)`
  Determine if the object belongs to a primal space.
  This is not simply the negation of is_dual,
  because a mixed function space containing both primal
  and dual components is neither primal nor dual.

## ufl.equation module

The Equation class, used to express equations like a == L.

- **class** `class ufl.equation.Equation(lhs, rhs)`
  Bases: object
  Equation.
  This class is used to represent equations expressed by the “==”
  operator. Examples include a == L and F == 0 where a, L and F are
  Form objects.

## ufl.exprcontainers module

This module defines special types for representing mapping of expressions to expressions.

- **class** `class ufl.exprcontainers.ExprList(*operands)`
  Bases: Operator
  List of Expr objects. For internal use, never to be created by end users.

Bases: Operator

List of Expr objects. For internal use, never to be created by end users.

- **method** `free_indices()`
  Get the free indices.

- **method** `index_dimensions()`
  Get the index dimensions.

- **property** `property ufl_free_indices`
  Get the UFL free indices.

- **property** `property ufl_index_dimensions`
  Get the UFL index dimensions.

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.exprcontainers.ExprMapping(*operands)`
  Bases: Operator
  Mapping of Expr objects. For internal use, never to be created by end users.

Bases: Operator

Mapping of Expr objects. For internal use, never to be created by end users.

- **method** `free_indices()`
  Get the free indices.

- **method** `index_dimensions()`
  Get the index dimensions.

- **method** `ufl_domains()`
  Get the UFL domains.

- **property** `property ufl_free_indices`
  Get the UFL free indices.

- **property** `property ufl_index_dimensions`
  Get the UFL index dimensions.

- **property** `property ufl_shape`
  Get the UFL shape.

## ufl.exprequals module

Expr equals.

- **function** `ufl.exprequals.expr_equals(self, other)`
  Checks whether the two expressions are represented the exact same way.
  This does not check if the expressions are
  mathematically equal or equivalent! Used by sets and dicts.

## ufl.exproperators module

Expr operators.

This module attaches special functions to Expr.
This way we avoid circular dependencies between e.g.
Sum and its superclass Expr.

## ufl.finiteelement module

This module defines the UFL finite element classes.

- **class** `class ufl.finiteelement.AbstractFiniteElement`
  Bases: ABC
  Base class for all finite elements.
  To make your element library compatible with UFL, you should make a
  subclass of AbstractFiniteElement and provide implementions of all
  the abstract methods and properties. All methods and properties that
  are not marked as abstract are implemented here and should not need
  to be overwritten in your subclass.
  An example of how the methods in your subclass could be implemented
  can be found in Basix; see
  https://github.com/FEniCS/basix/blob/main/python/basix/ufl.py

Bases: ABC

Base class for all finite elements.

To make your element library compatible with UFL, you should make a
subclass of AbstractFiniteElement and provide implementions of all
the abstract methods and properties. All methods and properties that
are not marked as abstract are implemented here and should not need
to be overwritten in your subclass.

An example of how the methods in your subclass could be implemented
can be found in Basix; see
https://github.com/FEniCS/basix/blob/main/python/basix/ufl.py

- **property** `abstract property cell: Cell`
  Return the cell of the finite element.

- **property** `abstract property embedded_subdegree: int`
  Degree of the maximum degree Lagrange space that is spanned by this element.
  This returns the degree of the highest degree Lagrange space
  such that the polynomial space of the Lagrange space is a
  subspace of this element’s polynomial space. If this element’s
  polynomial space does not include the constant function, this
  function should return -1.
  Note that on a simplex cells, the polynomial space of Lagrange
  space is a complete polynomial space, but on other cells this is
  not true. For example, on quadrilateral cells, the degree 1
  Lagrange space includes the degree 2 polynomial xy.

- **property** `abstract property embedded_superdegree: int | None`
  Degree of the minimum degree Lagrange space that spans this element.
  This returns the degree of the lowest degree Lagrange space such
  that the polynomial space of the Lagrange space is a superspace
  of this element’s polynomial space. If this element contains
  basis functions that are not in any Lagrange space, this
  function should return None.
  Note that on a simplex cells, the polynomial space of Lagrange
  space is a complete polynomial space, but on other cells this is
  not true. For example, on quadrilateral cells, the degree 1
  Lagrange space includes the degree 2 polynomial xy.

- **method** `is_cellwise_constant() → bool`
  Check whether this element is spatially constant over each cell.

- **property** `property num_sub_elements: int`
  Return number of sub-elements.
  This function does not recurse: ie it does not count the sub-elements of
  sub-elements.

- **property** `abstract property pullback: AbstractPullback`
  Return the pullback for this element.

- **property** `abstract property reference_value_shape: tuple[int, ...]`
  Return the shape of the value space on the reference cell.

- **property** `property reference_value_size: int`
  Return the integer product of the reference value shape.

- **property** `abstract property sobolev_space: SobolevSpace`
  Return the underlying Sobolev space.

- **property** `abstract property sub_elements: Sequence`
  Return list of sub-elements.
  This function does not recurse: ie it does not extract the sub-elements
  of sub-elements.

## ufl.form module

The Form class.

- **class** `class ufl.form.BaseForm`
  Bases: object
  Description of an object containing arguments.

Bases: object

Description of an object containing arguments.

- **method** `arguments()`
  Return all Argument objects found in form.

- **method** `coefficients()`
  Return all Coefficient objects found in form.

- **method** `empty()`
  Returns whether the BaseForm has no components.

- **method** `geometric_quantities()`
  Return all GeometricQuantity objects found in form.

- **method** `ufl_domain()`
  Return the single geometric integration domain occuring in the base form.
  Fails if multiple domains are found.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.form.Form(integrals)`
  Bases: BaseForm
  Description of a weak form consisting of a sum of integrals over subdomains.

Bases: BaseForm

Description of a weak form consisting of a sum of integrals over subdomains.

- **method** `base_form_operators()`
  Return all BaseFormOperator objects found in form.

- **method** `coefficient_numbering()`
  Return a contiguous numbering of coefficients in a mapping {coefficient:number}.

- **method** `coefficients()`
  Return all Coefficient objects found in form.

- **method** `constant_numbering()`
  Return a contiguous numbering of constants in a mapping {constant:number}.

- **method** `constants()`
  Get constants.

- **method** `domain_numbering()`
  Return a contiguous numbering of domains in a mapping {domain:number}.

- **method** `empty()`
  Returns whether the form has no integrals.

- **method** `equals(other)`
  Evaluate bool(lhs_form == rhs_form).

- **method** `geometric_dimension()`
  Return the geometric dimension shared by all domains and functions in this form.

- **method** `integrals()`
  Return a sequence of all integrals in form.

- **method** `integrals_by_domain(domain)`
  Return a sequence of all integrals with a particular integration domain.

- **method** `integrals_by_type(integral_type)`
  Return a sequence of all integrals with a particular domain type.

- **method** `signature()`
  Signature for use with jit cache (independent of incidental numbering of indices etc).

- **method** `subdomain_data()`
  Returns a mapping on the form {domain:{integral_type: subdomain_data}}.

- **method** `terminal_numbering()`
  Return a contiguous numbering for all counted objects in the form.
  The returned object is mapping from terminal to its number (an integer).
  The numbering is computed per type so Coefficient,
  Constant, etc will each be numbered from zero.

- **method** `ufl_cell()`
  Return the single cell this form is defined on.
  Fails if multiple cells are found.

- **method** `ufl_domains()`
  Return the geometric integration domains occuring in the form.
  NB! This does not include domains of coefficients defined on
  other meshes.
  The return type is a tuple even if only a single domain exists.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.form.FormSum(*args, **kwargs)`
  Bases: BaseForm
  Form sum.
  Description of a weighted sum of variational forms and form-like objects
  components is the list of Forms to be summed
  arg_weights is a list of tuples of component index and weight

Bases: BaseForm

Form sum.

Description of a weighted sum of variational forms and form-like objects
components is the list of Forms to be summed
arg_weights is a list of tuples of component index and weight

- **method** `components()`
  Get components.

- **method** `empty()`
  Returns whether the FormSum has no components.

- **method** `equals(other)`
  Evaluate bool(lhs_form == rhs_form).

- **method** `ufl_domains()`
  Return all domains found in the base form.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **method** `weights()`
  Get weights.

- **class** `class ufl.form.ZeroBaseForm(arguments)`
  Bases: BaseForm
  Description of a zero base form.
  ZeroBaseForm is idempotent with respect to assembly and is mostly
  used for sake of simplifying base-form expressions.

Bases: BaseForm

Description of a zero base form.

ZeroBaseForm is idempotent with respect to assembly and is mostly
used for sake of simplifying base-form expressions.

- **attribute** `form`

- **method** `ufl_domains()`
  Return all domains found in the base form.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **function** `ufl.form.as_form(form)`
  Convert to form if not a form, otherwise return form.

## ufl.formoperators module

Various high level ways to transform a complete Form into a new Form.

- **function** `ufl.formoperators.action(form, coefficient=None, derivatives_expanded=None)`
  Get the action.
  Given a bilinear form, return a linear form
  with an additional coefficient, representing the
  action of the form on the coefficient. This can be
  used for matrix-free methods.
  For formbase objects,coefficient can be any object of the correct type,
  and this function returns an Action object.
  When action is being called multiple times on the same form, expanding derivatives
  become expensive -> derivatives_expanded enables to use caching mechanisms to avoid that.

- **function** `ufl.formoperators.adjoint(form, reordered_arguments=None, derivatives_expanded=None)`
  Get the adjoint.
  Given a combined bilinear form, compute the adjoint form by
  changing the ordering (count) of the test and trial functions, and
  taking the complex conjugate of the result.
  By default, new Argument objects will be created with
  opposite ordering. However, if the adjoint form is to
  be added to other forms later, their arguments must match.
  In that case, the user must provide a tuple *reordered_arguments*=(u2,v2).
  If the form is a baseform instance instead of a Form object, we return an Adjoint
  object instructing the adjoint to be computed at a later point.
  When adjoint is being called multiple times on the same form, expanding derivatives
  become expensive -> derivatives_expanded enables to use caching mechanisms to avoid that.

- **function** `ufl.formoperators.derivative(form, coefficient, argument=None, coefficient_derivatives=None)`
  Compute the Gateaux derivative of form w.r.t. coefficient in direction of argument.
  If the argument is omitted, a new Argument is created
  in the same space as the coefficient, with argument number
  one higher than the highest one in the form.
  The resulting form has one additional Argument
  in the same finite element space as the coefficient.
  A tuple of Coefficient s may be provided in place of
  a single Coefficient, in which case the new Argument
  argument is based on a MixedElement created from this tuple.
  An indexed Coefficient from a mixed space may be provided,
  in which case the argument should be in the corresponding
  subspace of the coefficient space.
  If provided, coefficient_derivatives should be a mapping from
  Coefficient instances to their derivatives w.r.t. coefficient.

- **function** `ufl.formoperators.energy_norm(form, coefficient=None)`
  Get the energy norm.
  Given a bilinear form a and a coefficient f,
  return the functional a(f,f).

- **function** `ufl.formoperators.extract_blocks(form: Form, i: int | None = None, j: int | None = None, replace_argument: bool = True)`
  Extract blocks.
  Given a linear or bilinear form on a mixed space,
  extract the block corresponding to the indices ix, iy.

Extract blocks.

Given a linear or bilinear form on a mixed space,
extract the block corresponding to the indices ix, iy.

- `Example:`
  a = inner(grad(u), grad(v))*dx + div(u)*q*dx + div(v)*p*dx
  extract_blocks(a, 0, 0) -> inner(grad(u), grad(v))*dx
  extract_blocks(a) -> [inner(grad(u), grad(v))*dx, div(v)*p*dx, div(u)*q*dx, 0]

- **function** `ufl.formoperators.functional(form)`
  Extract the functional part of form.

- **function** `ufl.formoperators.lhs(form)`
  Get the left hand side.
  Given a combined bilinear and linear form,
  extract the left hand side (bilinear form part).

Get the left hand side.

Given a combined bilinear and linear form,
extract the left hand side (bilinear form part).

- `Example:`
  a = u*v*dx + f*v*dx
  a = lhs(a) -> u*v*dx

- **function** `ufl.formoperators.rhs(form)`
  Get the right hand side.
  Given a combined bilinear and linear form,
  extract the right hand side (negated linear form part).

Get the right hand side.

Given a combined bilinear and linear form,
extract the right hand side (negated linear form part).

- `Example:`
  a = u*v*dx + f*v*dx
  L = rhs(a) -> -f*v*dx

- **function** `ufl.formoperators.sensitivity_rhs(a, u, L, v)`
  Compute the right hand side for a sensitivity calculation system.
  The derivation behind this computation is as follows.
  Assume a, L to be bilinear and linear forms
  corresponding to the assembled linear system
  Where x is the vector of the discrete function corresponding to u.
  Let v be some scalar variable this equation depends on.
  Then we can write
  and solve this system for fracdxdv, using the same bilinear
  form a and matrix A from the original system.
  Assume the forms are written
  where IL and Ia are integrand expressions.
  Define a Coefficient u representing the solution
  to the equations. Then we can compute fracdbdv
  and fracdAdv from the forms
  and the action of da on u by
  In total, we can build the right hand side of the system
  to compute fracdudv with the single line
  or, using this function,

- **function** `ufl.formoperators.set_list_item(li, i, v)`
  Set an item in a nested list.

- **function** `ufl.formoperators.system(form)`
  Split a form into the left hand side and right hand side.
  See lhs and rhs.

- **function** `ufl.formoperators.zero_lists(shape)`
  Createa list of zeros of the given shape.

## ufl.functionspace module

Types for representing function spaces.

- **class** `class ufl.functionspace.AbstractFunctionSpace`
  Bases: object
  Abstract function space.

Bases: object

Abstract function space.

- **method** `ufl_sub_spaces()`
  Return ufl sub spaces.

- **class** `class ufl.functionspace.BaseFunctionSpace(domain, element, label='')`
  Bases: AbstractFunctionSpace, UFLObject
  Base function space.

Bases: AbstractFunctionSpace, UFLObject

Base function space.

- **property** `property components: dict[tuple[int, ...], int]`
  Get the numbering of the components of the element of this space.

Get the numbering of the components of the element of this space.

- `Returns:`
  A map from the components of the values on a physical cell (eg (0, 1))
  to flat component numbers on the reference cell (eg 1)

- **method** `label()`
  Return label of boundary domains to differentiate restricted and unrestricted.

- **method** `ufl_domain()`
  Return ufl domain.

- **method** `ufl_domains()`
  Return ufl domains.

- **method** `ufl_element()`
  Return ufl element.

- **method** `ufl_sub_spaces()`
  Return ufl sub spaces.

- **property** `property value_shape: tuple[int, ...]`
  Return the shape of the value space on a physical domain.

- **property** `property value_size: int`
  Return the integer product of the value shape on a physical domain.

- **class** `class ufl.functionspace.DualSpace(domain, element, label='')`
  Bases: BaseFunctionSpace, UFLObject
  Representation of a Dual space.

Bases: BaseFunctionSpace, UFLObject

Representation of a Dual space.

- **method** `dual()`
  Get the dual of the space.

- **class** `class ufl.functionspace.FunctionSpace(domain, element, label='')`
  Bases: BaseFunctionSpace, UFLObject
  Representation of a Function space.

Bases: BaseFunctionSpace, UFLObject

Representation of a Function space.

- **method** `dual()`
  Get the dual of the space.

- **class** `class ufl.functionspace.MixedFunctionSpace(*args)`
  Bases: AbstractFunctionSpace, UFLObject
  Mixed function space.

Bases: AbstractFunctionSpace, UFLObject

Mixed function space.

- **method** `dual(*args)`
  Return the dual to this function space.
  If no additional arguments are passed then a MixedFunctionSpace is
  returned whose components are the duals of the originals.
  If additional arguments are passed, these must be integers. In this
  case, the MixedFunctionSpace which is returned will have dual
  components in the positions corresponding to the arguments passed, and
  the original components in the other positions.

- **method** `num_sub_spaces()`
  Return number of subspaces.

- **method** `ufl_domain()`
  Return ufl domain.

- **method** `ufl_domains()`
  Return ufl domains.

- **method** `ufl_element()`
  Return ufl element.

- **method** `ufl_elements()`
  Return ufl elements.

- **method** `ufl_sub_space(i)`
  Return i-th ufl sub space.

- **method** `ufl_sub_spaces()`
  Return ufl sub spaces.

- **class** `class ufl.functionspace.TensorProductFunctionSpace(*function_spaces)`
  Bases: AbstractFunctionSpace, UFLObject
  Tensor product function space.

Bases: AbstractFunctionSpace, UFLObject

Tensor product function space.

- **method** `ufl_sub_spaces()`
  Return ufl sub spaces.

## ufl.geometry module

Types for representing symbolic expressions for geometric quantities.

- **class** `class ufl.geometry.CellCoordinate(domain)`
  Bases: GeometricCellQuantity
  The coordinate in a reference cell.
  In the context of expression integration,
  represents the reference cell coordinate of each quadrature point.
  In the context of expression evaluation in a point in a cell,
  represents that point in the reference coordinate system of the cell.

Bases: GeometricCellQuantity

The coordinate in a reference cell.

In the context of expression integration,
represents the reference cell coordinate of each quadrature point.

In the context of expression evaluation in a point in a cell,
represents that point in the reference coordinate system of the cell.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'X'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.CellDiameter(domain)`
  Bases: GeometricCellQuantity
  The diameter of the cell, i.e., maximal distance of two points in the cell.

Bases: GeometricCellQuantity

The diameter of the cell, i.e., maximal distance of two points in the cell.

- **attribute** `name = 'diameter'`

- **class** `class ufl.geometry.CellEdgeVectors(domain)`
  Bases: GeometricCellQuantity
  The vectors between physical cell vertices for each edge in cell.

Bases: GeometricCellQuantity

The vectors between physical cell vertices for each edge in cell.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'CEV'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.CellFacetJacobian(domain)`
  Bases: GeometricFacetQuantity
  The Jacobian of the mapping from reference facet to reference cell coordinates.
  CFJ_ij = dX_i/dXf_j

Bases: GeometricFacetQuantity

The Jacobian of the mapping from reference facet to reference cell coordinates.

CFJ_ij = dX_i/dXf_j

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'CFJ'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.CellFacetJacobianDeterminant(domain)`
  Bases: GeometricFacetQuantity
  The pseudo-determinant of the CellFacetJacobian.

Bases: GeometricFacetQuantity

The pseudo-determinant of the CellFacetJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'detCFJ'`

- **class** `class ufl.geometry.CellFacetJacobianInverse(domain)`
  Bases: GeometricFacetQuantity
  The pseudo-inverse of the CellFacetJacobian.

Bases: GeometricFacetQuantity

The pseudo-inverse of the CellFacetJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'CFK'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.CellFacetOrigin(domain)`
  Bases: GeometricFacetQuantity
  The reference cell coordinate corresponding to origin of a reference facet.

Bases: GeometricFacetQuantity

The reference cell coordinate corresponding to origin of a reference facet.

- **attribute** `name = 'X0f'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.CellNormal(domain)`
  Bases: GeometricCellQuantity
  The upwards pointing normal vector of the current manifold cell.

Bases: GeometricCellQuantity

The upwards pointing normal vector of the current manifold cell.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'cell_normal'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.geometry.CellOrientation(domain)`
  Bases: GeometricCellQuantity
  The orientation (+1/-1) of the current cell.
  For non-manifold cells (tdim == gdim), this equals the sign
  of the Jacobian determinant, i.e. +1 if the physical cell is
  oriented the same way as the reference cell and -1 otherwise.
  For manifold cells of tdim==gdim-1 this is input data belonging
  to the mesh, used to distinguish between the sides of the manifold.

Bases: GeometricCellQuantity

The orientation (+1/-1) of the current cell.

For non-manifold cells (tdim == gdim), this equals the sign
of the Jacobian determinant, i.e. +1 if the physical cell is
oriented the same way as the reference cell and -1 otherwise.

For manifold cells of tdim==gdim-1 this is input data belonging
to the mesh, used to distinguish between the sides of the manifold.

- **attribute** `name = 'cell_orientation'`

- **class** `class ufl.geometry.CellOrigin(domain)`
  Bases: GeometricCellQuantity
  The spatial coordinate corresponding to origin of a reference cell.

Bases: GeometricCellQuantity

The spatial coordinate corresponding to origin of a reference cell.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'x0'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.CellRidgeJacobian(domain)`
  Bases: GeometricRidgeQuantity
  The Jacobian of the mapping from reference ridge to reference cell coordinates.
  CRJ_ij = dX_i/dXe_j

Bases: GeometricRidgeQuantity

The Jacobian of the mapping from reference ridge to reference cell coordinates.

CRJ_ij = dX_i/dXe_j

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'CRJ'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.CellRidgeJacobianDeterminant(domain)`
  Bases: GeometricRidgeQuantity
  The pseudo-determinant of the CellRidgeJacobian.

Bases: GeometricRidgeQuantity

The pseudo-determinant of the CellRidgeJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'detCRJ'`

- **class** `class ufl.geometry.CellRidgeJacobianInverse(domain)`
  Bases: GeometricRidgeQuantity
  The pseudo-inverse of the RidgeFacetJacobian.

Bases: GeometricRidgeQuantity

The pseudo-inverse of the RidgeFacetJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'CEK'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.CellRidgeOrigin(domain)`
  Bases: GeometricRidgeQuantity
  The reference cell coordinate corresponding to origin of a reference ridge.

Bases: GeometricRidgeQuantity

The reference cell coordinate corresponding to origin of a reference ridge.

- **attribute** `name = 'X0e'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.CellVertices(domain)`
  Bases: GeometricCellQuantity
  Physical cell vertices.

Bases: GeometricCellQuantity

Physical cell vertices.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'CV'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.CellVolume(domain)`
  Bases: GeometricCellQuantity
  The volume of the cell.

Bases: GeometricCellQuantity

The volume of the cell.

- **attribute** `name = 'volume'`

- **class** `class ufl.geometry.Circumradius(domain)`
  Bases: GeometricCellQuantity
  The circumradius of the cell.

Bases: GeometricCellQuantity

The circumradius of the cell.

- **attribute** `name = 'circumradius'`

- **class** `class ufl.geometry.FacetArea(domain)`
  Bases: GeometricFacetQuantity
  The area of the facet.

Bases: GeometricFacetQuantity

The area of the facet.

- **attribute** `name = 'facetarea'`

- **class** `class ufl.geometry.FacetCoordinate(domain)`
  Bases: GeometricFacetQuantity
  The coordinate in a reference cell of a facet.
  In the context of expression integration over a facet,
  represents the reference facet coordinate of each quadrature point.
  In the context of expression evaluation in a point on a facet,
  represents that point in the reference coordinate system of the facet.

Bases: GeometricFacetQuantity

The coordinate in a reference cell of a facet.

In the context of expression integration over a facet,
represents the reference facet coordinate of each quadrature point.

In the context of expression evaluation in a point on a facet,
represents that point in the reference coordinate system of the facet.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'Xf'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.FacetEdgeVectors(domain)`
  Bases: GeometricFacetQuantity
  The vectors between physical cell vertices for each edge in current facet.

Bases: GeometricFacetQuantity

The vectors between physical cell vertices for each edge in current facet.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'FEV'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.FacetJacobian(domain)`
  Bases: GeometricFacetQuantity
  The Jacobian of the mapping from reference facet to spatial coordinates.
  The FacetJacobian is the product of the Jacobian and CellFacetJacobian:

Bases: GeometricFacetQuantity

The Jacobian of the mapping from reference facet to spatial coordinates.

The FacetJacobian is the product of the Jacobian and CellFacetJacobian:

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'FJ'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.FacetJacobianDeterminant(domain)`
  Bases: GeometricFacetQuantity
  The pseudo-determinant of the FacetJacobian.

Bases: GeometricFacetQuantity

The pseudo-determinant of the FacetJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'detFJ'`

- **class** `class ufl.geometry.FacetJacobianInverse(domain)`
  Bases: GeometricFacetQuantity
  The pseudo-inverse of the FacetJacobian.

Bases: GeometricFacetQuantity

The pseudo-inverse of the FacetJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'FK'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.FacetNormal(domain)`
  Bases: GeometricFacetQuantity
  The outwards pointing normal vector of the current facet.

Bases: GeometricFacetQuantity

The outwards pointing normal vector of the current facet.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'n'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.geometry.FacetOrientation(domain)`
  Bases: GeometricFacetQuantity
  The orientation (+1/-1) of the current facet relative to the reference cell.

Bases: GeometricFacetQuantity

The orientation (+1/-1) of the current facet relative to the reference cell.

- **attribute** `name = 'facet_orientation'`

- **class** `class ufl.geometry.FacetOrigin(domain)`
  Bases: GeometricFacetQuantity
  The spatial coordinate corresponding to origin of a reference facet.

Bases: GeometricFacetQuantity

The spatial coordinate corresponding to origin of a reference facet.

- **attribute** `name = 'x0f'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.FacetRidgeJacobian(domain)`
  Bases: GeometricRidgeQuantity
  The Jacobian of the mapping from reference ridge to reference facet coordinates.
  FRJ_ij = dXf_i/dXe_j

Bases: GeometricRidgeQuantity

The Jacobian of the mapping from reference ridge to reference facet coordinates.

FRJ_ij = dXf_i/dXe_j

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'FRJ'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.GeometricCellQuantity(domain)`
  Bases: GeometricQuantity
  Geometric cell quantity.

- **class** `class ufl.geometry.GeometricFacetQuantity(domain)`
  Bases: GeometricQuantity
  Geometric facet quantity.

- **class** `class ufl.geometry.GeometricQuantity(domain)`
  Bases: Terminal
  Geometric quantity.

Bases: Terminal

Geometric quantity.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **method** `ufl_domains()`
  Get the UFL domains.

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.geometry.GeometricRidgeQuantity(domain)`
  Bases: GeometricQuantity
  Geometric ridge quantity.

- **class** `class ufl.geometry.Jacobian(domain)`
  Bases: GeometricCellQuantity
  The Jacobian of the mapping from reference cell to spatial coordinates.

Bases: GeometricCellQuantity

The Jacobian of the mapping from reference cell to spatial coordinates.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'J'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.geometry.JacobianDeterminant(domain)`
  Bases: GeometricCellQuantity
  The determinant of the Jacobian.
  Represents the signed determinant of a square Jacobian or the
  pseudo-determinant of a non-square Jacobian.

Bases: GeometricCellQuantity

The determinant of the Jacobian.

Represents the signed determinant of a square Jacobian or the
pseudo-determinant of a non-square Jacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'detJ'`

- **class** `class ufl.geometry.JacobianInverse(domain)`
  Bases: GeometricCellQuantity
  The inverse of the Jacobian.
  Represents the inverse of a square Jacobian or the pseudo-inverse of
  a non-square Jacobian.

Bases: GeometricCellQuantity

The inverse of the Jacobian.

Represents the inverse of a square Jacobian or the pseudo-inverse of
a non-square Jacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'K'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.geometry.MaxCellEdgeLength(domain)`
  Bases: GeometricCellQuantity
  The maximum edge length of the cell.

Bases: GeometricCellQuantity

The maximum edge length of the cell.

- **attribute** `name = 'maxcelledgelength'`

- **class** `class ufl.geometry.MaxFacetEdgeLength(domain)`
  Bases: GeometricFacetQuantity
  The maximum edge length of the facet.

Bases: GeometricFacetQuantity

The maximum edge length of the facet.

- **attribute** `name = 'maxfacetedgelength'`

- **class** `class ufl.geometry.MinCellEdgeLength(domain)`
  Bases: GeometricCellQuantity
  The minimum edge length of the cell.

Bases: GeometricCellQuantity

The minimum edge length of the cell.

- **attribute** `name = 'mincelledgelength'`

- **class** `class ufl.geometry.MinFacetEdgeLength(domain)`
  Bases: GeometricFacetQuantity
  The minimum edge length of the facet.

Bases: GeometricFacetQuantity

The minimum edge length of the facet.

- **attribute** `name = 'minfacetedgelength'`

- **class** `class ufl.geometry.QuadratureWeight(domain)`
  Bases: GeometricQuantity
  The current quadrature weight.
  Only used inside a quadrature context.

Bases: GeometricQuantity

The current quadrature weight.

Only used inside a quadrature context.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'weight'`

- **class** `class ufl.geometry.ReferenceCellEdgeVectors(domain)`
  Bases: GeometricCellQuantity
  The vectors between reference cell vertices for each edge in cell.

Bases: GeometricCellQuantity

The vectors between reference cell vertices for each edge in cell.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'RCEV'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.ReferenceCellVolume(domain)`
  Bases: GeometricCellQuantity
  The volume of the reference cell.

Bases: GeometricCellQuantity

The volume of the reference cell.

- **attribute** `name = 'reference_cell_volume'`

- **class** `class ufl.geometry.ReferenceFacetEdgeVectors(domain)`
  Bases: GeometricFacetQuantity
  The vectors between reference cell vertices for each edge in current facet.

Bases: GeometricFacetQuantity

The vectors between reference cell vertices for each edge in current facet.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'RFEV'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.ReferenceFacetVolume(domain)`
  Bases: GeometricFacetQuantity
  The volume of the reference cell of the current facet.

Bases: GeometricFacetQuantity

The volume of the reference cell of the current facet.

- **attribute** `name = 'reference_facet_volume'`

- **class** `class ufl.geometry.ReferenceNormal(domain)`
  Bases: GeometricFacetQuantity
  The outwards pointing normal vector of the current facet on the reference cell.

Bases: GeometricFacetQuantity

The outwards pointing normal vector of the current facet on the reference cell.

- **attribute** `name = 'reference_normal'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.ReferenceRidgeVolume(domain)`
  Bases: GeometricRidgeQuantity
  The volume of the reference cell of the current ridge.

Bases: GeometricRidgeQuantity

The volume of the reference cell of the current ridge.

- **attribute** `name = 'reference_ridge_volume'`

- **class** `class ufl.geometry.RidgeCoordinate(domain)`
  Bases: GeometricRidgeQuantity
  The coordinate in a reference cell of a ridge.
  In the context of expression integration over a ridge,
  represents the reference ridge coordinate of each quadrature point.
  In the context of expression evaluation in a point on a ridge,
  represents that point in the reference coordinate system of the ridge.

Bases: GeometricRidgeQuantity

The coordinate in a reference cell of a ridge.

In the context of expression integration over a ridge,
represents the reference ridge coordinate of each quadrature point.

In the context of expression evaluation in a point on a ridge,
represents that point in the reference coordinate system of the ridge.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'Xe'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.RidgeJacobian(domain)`
  Bases: GeometricRidgeQuantity
  The Jacobian of the mapping from reference ridge to spatial coordinates.
  The RidgeJacobian is the product of the Jacobian and CellRidgeJacobian:

Bases: GeometricRidgeQuantity

The Jacobian of the mapping from reference ridge to spatial coordinates.

The RidgeJacobian is the product of the Jacobian and CellRidgeJacobian:

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'RJ'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.RidgeJacobianDeterminant(domain)`
  Bases: GeometricRidgeQuantity
  The pseudo-determinant of the RidgeJacobian.

Bases: GeometricRidgeQuantity

The pseudo-determinant of the RidgeJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'detRJ'`

- **class** `class ufl.geometry.RidgeJacobianInverse(domain)`
  Bases: GeometricRidgeQuantity
  The pseudo-inverse of the RidgeJacobian.

Bases: GeometricRidgeQuantity

The pseudo-inverse of the RidgeJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'EK'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.RidgeOrigin(domain)`
  Bases: GeometricRidgeQuantity
  The spatial coordinate corresponding to origin of a reference ridge.

Bases: GeometricRidgeQuantity

The spatial coordinate corresponding to origin of a reference ridge.

- **attribute** `name = 'x0e'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.geometry.SpatialCoordinate(domain)`
  Bases: GeometricCellQuantity
  The coordinate in a domain.
  In the context of expression integration,
  represents the domain coordinate of each quadrature point.
  In the context of expression evaluation in a point,
  represents the value of that point.

Bases: GeometricCellQuantity

The coordinate in a domain.

In the context of expression integration,
represents the domain coordinate of each quadrature point.

In the context of expression evaluation in a point,
represents the value of that point.

- **method** `count()`
  Count.

- **method** `evaluate(x, mapping, component, index_values)`
  Return the value of the coordinate.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'x'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

## ufl.index_combination_utils module

Utilities for analysing and manipulating free index tuples.

- **function** `ufl.index_combination_utils.create_slice_indices(component, shape, fi)`
  Create slice indices.

- **function** `ufl.index_combination_utils.merge_nonoverlapping_indices(a, b)`
  Merge non-overlapping free indices into one representation.

Merge non-overlapping free indices into one representation.

- `Example:`
  C[i,j,r,s] = outer(A[i,s], B[j,r])
  A, B -> (i,j,r,s), (idim,jdim,rdim,sdim)

- **function** `ufl.index_combination_utils.merge_overlapping_indices(afi, afid, bfi, bfid)`
  Merge overlapping free indices into one free and one repeated representation.

Merge overlapping free indices into one free and one repeated representation.

- `Example:`
  C[j,r] := A[i,j,k] * B[i,r,k]
  A, B -> (j,r), (jdim,rdim), (i,k), (idim,kdim)

- **function** `ufl.index_combination_utils.merge_unique_indices(afi, afid, bfi, bfid)`
  Merge two pairs of (index ids, index dimensions) sequences into one pair without duplicates.
  The id tuples afi, bfi are assumed already sorted by id.
  Given a list of (id, dim) tuples already sorted by id,
  return a unique list with duplicates removed.
  Also checks that the dimensions of duplicates are matching.

- **function** `ufl.index_combination_utils.remove_indices(fi, fid, rfi)`
  Remove indices.

- **function** `ufl.index_combination_utils.unique_sorted_indices(indices)`
  Get unique sorted indices.
  Given a list of (id, dim) tuples already sorted by id,
  return a unique list with duplicates removed.
  Also checks that the dimensions of duplicates are matching.

## ufl.indexed module

This module defines the Indexed class.

- **class** `class ufl.indexed.Indexed(expression, multiindex)`
  Bases: Operator
  Indexed expression.

Bases: Operator

Indexed expression.

- **method** `evaluate(x, mapping, component, index_values, derivatives=())`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

## ufl.indexsum module

This module defines the IndexSum class.

- **class** `class ufl.indexsum.IndexSum(summand, index)`
  Bases: Operator
  Index sum.

Bases: Operator

Index sum.

- **method** `dimension()`
  Get dimension.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **method** `index()`
  Get index.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **property** `property ufl_shape`
  Get UFL shape.

## ufl.integral module

The Integral class.

- **class** `class ufl.integral.Integral(integrand, integral_type, domain, subdomain_id, metadata, subdomain_data)`
  Bases: object
  An integral over a single domain.

Bases: object

An integral over a single domain.

- **method** `integral_type()`
  Return the domain type of this integral.

- **method** `integrand()`
  Return the integrand expression, which is an Expr instance.

- **method** `metadata()`
  Return the compiler metadata this integral has been annotated with.

- **method** `reconstruct(integrand=None, integral_type=None, domain=None, subdomain_id=None, metadata=None, subdomain_data=None)`
  Construct a new Integral object with some properties replaced with new values.

Construct a new Integral object with some properties replaced with new values.

- `Example:`
  <a = Integral instance>
  b = a.reconstruct(expand_compounds(a.integrand()))
  c = a.reconstruct(metadata={‘quadrature_degree’:2})

- **method** `subdomain_data()`
  Return the domain data of this integral.

- **method** `subdomain_id()`
  Return the subdomain id of this integral.

- **method** `ufl_domain()`
  Return the integration domain of this integral.

## ufl.integral_domain module

Integral domains.

- **class** `class ufl.integral_domain.AbstractIntegralDomain`
  Bases: ABC
  Abstract base class for integral domain.

Bases: ABC

Abstract base class for integral domain.

- **property** `abstract property integral_type: str`
  Integral type.

- **class** `class ufl.integral_domain.DSIntegralDomain(coordinate_element_positive_side: AbstractFiniteElement, coordinate_element_negative_side: AbstractFiniteElement, facet_type: AbstractCell)`
  Bases: AbstractIntegralDomain
  Integral domain for dS.

Bases: AbstractIntegralDomain

Integral domain for dS.

- **property** `property integral_type: str`
  Integral type.

- **class** `class ufl.integral_domain.DsIntegralDomain(coordinate_element: AbstractFiniteElement, facet_type: AbstractCell)`
  Bases: AbstractIntegralDomain
  Integral domain for ds.

Bases: AbstractIntegralDomain

Integral domain for ds.

- **property** `property integral_type: str`
  Integral type.

- **class** `class ufl.integral_domain.DxIntegralDomain(coordinate_element: AbstractFiniteElement)`
  Bases: AbstractIntegralDomain
  Integral domain for dx.

Bases: AbstractIntegralDomain

Integral domain for dx.

- **property** `property integral_type: str`
  Integral type.

## ufl.mathfunctions module

This module provides basic mathematical functions.

- **class** `class ufl.mathfunctions.Acos(argument)`
  Bases: MathFunction
  Inverse cosine.

- **class** `class ufl.mathfunctions.Asin(argument)`
  Bases: MathFunction
  Inverse sine.

- **class** `class ufl.mathfunctions.Atan(argument)`
  Bases: MathFunction
  Inverse tangent.

- **class** `class ufl.mathfunctions.Atan2(arg1, arg2)`
  Bases: Operator
  Inverse tangent with two inputs.

Bases: Operator

Inverse tangent with two inputs.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.mathfunctions.BesselFunction(name, nu, argument)`
  Bases: Operator
  Base class for all bessel functions.

Bases: Operator

Base class for all bessel functions.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.mathfunctions.BesselI(nu, argument)`
  Bases: BesselFunction
  Bessel I function.

- **class** `class ufl.mathfunctions.BesselJ(nu, argument)`
  Bases: BesselFunction
  Bessel J function.

- **class** `class ufl.mathfunctions.BesselK(nu, argument)`
  Bases: BesselFunction
  Bessel K function.

- **class** `class ufl.mathfunctions.BesselY(nu, argument)`
  Bases: BesselFunction
  Bessel Y function.

- **class** `class ufl.mathfunctions.Cos(argument)`
  Bases: MathFunction
  Cosine.

- **class** `class ufl.mathfunctions.Cosh(argument)`
  Bases: MathFunction
  Hyperbolic cosine.

- **class** `class ufl.mathfunctions.Erf(argument)`
  Bases: MathFunction
  Erf function.

Bases: MathFunction

Erf function.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.mathfunctions.Exp(argument)`
  Bases: MathFunction
  Exponentiation..

- **class** `class ufl.mathfunctions.Ln(argument)`
  Bases: MathFunction
  Natural logarithm.

Bases: MathFunction

Natural logarithm.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **class** `class ufl.mathfunctions.MathFunction(name, argument)`
  Bases: Operator
  Base class for all unary scalar math functions.

Bases: Operator

Base class for all unary scalar math functions.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.mathfunctions.Sin(argument)`
  Bases: MathFunction
  Sine.

- **class** `class ufl.mathfunctions.Sinh(argument)`
  Bases: MathFunction
  Hyperbolic sine.

- **class** `class ufl.mathfunctions.Sqrt(argument)`
  Bases: MathFunction
  Square root.

- **class** `class ufl.mathfunctions.Tan(argument)`
  Bases: MathFunction
  Tangent.

- **class** `class ufl.mathfunctions.Tanh(argument)`
  Bases: MathFunction
  Hyperbolic tangent.

## ufl.matrix module

This module defines the Matrix class.

- **class** `class ufl.matrix.Matrix(row_space, column_space, count=None)`
  Bases: BaseForm, Counted
  An assemble linear operator between two function spaces.

Bases: BaseForm, Counted

An assemble linear operator between two function spaces.

- **method** `equals(other)`
  Check equality.

- **method** `ufl_function_spaces()`
  Get the tuple of function spaces of this coefficient.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

## ufl.measure module

The Measure class.

- **class** `class ufl.measure.Measure(integral_type, domain=None, subdomain_id='everywhere', metadata=None, subdomain_data=None)`
  Bases: object
  Representation of an integration measure.
  The Measure object holds information about integration properties
  to be transferred to a Form on multiplication with a scalar
  expression.

Bases: object

Representation of an integration measure.

The Measure object holds information about integration properties
to be transferred to a Form on multiplication with a scalar
expression.

- **method** `integral_type()`
  Return the domain type.
  Valid domain types are “cell”, “exterior_facet”, “interior_facet”, etc.

- **method** `metadata()`
  Return the integral metadata.
  This data is not interpreted by UFL.
  It is passed to the form compiler which can ignore it or use
  it to compile each integral of a form in a different way.

- **method** `reconstruct(integral_type=None, subdomain_id=None, domain=None, metadata=None, subdomain_data=None)`
  Construct a new Measure object with some properties replaced with new values.

Construct a new Measure object with some properties replaced with new values.

- `Example:`
  <dm = Measure instance>
  b = dm.reconstruct(subdomain_id=2)
  c = dm.reconstruct(metadata={ “quadrature_degree”: 3 })

- `Used by the call operator, so this is equivalent:`
  b = dm(2)
  c = dm(0, { “quadrature_degree”: 3 })

- **method** `subdomain_data()`
  Return the integral subdomain_data.
  This data is not interpreted by
  UFL.  Its intension is to give a context in which the domain
  id is interpreted.

- **method** `subdomain_id()`
  Return the domain id of this measure (integer).

- **method** `ufl_domain()`
  Return the domain associated with this measure.
  This may be None or a Domain object.

- **class** `class ufl.measure.MeasureProduct(*measures)`
  Bases: object
  Represents a product of measures.
  This is a notational intermediate object to handle the notation
  This is work in progress and not functional. It needs support
  in other parts of ufl and the rest of the code generation chain.

Bases: object

Represents a product of measures.

This is a notational intermediate object to handle the notation

This is work in progress and not functional. It needs support
in other parts of ufl and the rest of the code generation chain.

- **method** `sub_measures()`
  Return submeasures.

- **class** `class ufl.measure.MeasureSum(*measures)`
  Bases: object
  Represents a sum of measures.

Bases: object

Represents a sum of measures.

- `This is a notational intermediate object to translate the notation`
  f*(ds(1)+ds(3))

- `into`
  f*ds(1) + f*ds(3)

- **function** `ufl.measure.as_integral_type(integral_type)`
  Map short name to long name and require a valid one.

- **function** `ufl.measure.integral_types()`
  Return a tuple of all domain type strings.

- **function** `ufl.measure.measure_names()`
  Return a tuple of all measure name strings.

- **function** `ufl.measure.register_integral_type(integral_type, measure_name)`
  Register an integral type.

## ufl.objects module

Utility objects for pretty syntax in user code.

## ufl.operators module

Operators.

This module extends the form language with free function operators,
which are either already available as member functions on UFL objects
or defined as compound operators involving basic operations on the UFL
objects.

- **function** `ufl.operators.And(left, right)`
  A boolean expression (left and right) for use with conditional.

- **function** `ufl.operators.Dn(f)`
  Take the directional derivative of f in the facet normal direction.
  The facet normal is Dn(f) := dot(grad(f), n).

- **function** `ufl.operators.Dx(f, *i)`
  Take the partial derivative of f with respect to spatial variable number i.
  Equivalent to f.dx(*i).

- **function** `ufl.operators.Not(condition)`
  A boolean expression (not condition) for use with conditional.

- **function** `ufl.operators.Or(left, right)`
  A boolean expression (left or right) for use with conditional.

- **function** `ufl.operators.acos(f)`
  Take the inverse cosine of f.

- **function** `ufl.operators.asin(f)`
  Take the inverse sine of f.

- **function** `ufl.operators.atan(f)`
  Take the inverse tangent of f.

- **function** `ufl.operators.atan2(f1, f2)`
  Take the inverse tangent with two the arguments f1 and f2.

- **function** `ufl.operators.avg(v)`
  Take the average of v across a facet.

- **function** `ufl.operators.bessel_I(nu, f)`
  Regular modified cylindrical Bessel function.

- **function** `ufl.operators.bessel_J(nu, f)`
  Cylindrical Bessel function of the first kind.

- **function** `ufl.operators.bessel_K(nu, f)`
  Irregular modified cylindrical Bessel function.

- **function** `ufl.operators.bessel_Y(nu, f)`
  Cylindrical Bessel function of the second kind.

- **function** `ufl.operators.cell_avg(f)`
  Take the average of v over a cell.

- **function** `ufl.operators.cofac(A)`
  Take the cofactor of A.

- **function** `ufl.operators.conditional(condition, true_value, false_value)`
  A conditional expression.
  This takes the value of true_value
  when condition evaluates to true and false_value otherwise.

- **function** `ufl.operators.conj(f)`
  The complex conjugate of f.

- **function** `ufl.operators.conjugate(f)`
  The complex conjugate of f.

- **function** `ufl.operators.cos(f)`
  Take the cosine of f.

- **function** `ufl.operators.cosh(f)`
  Take the hyperbolic cosine of f.

- **function** `ufl.operators.cross(a, b)`
  Take the cross product of a and b.

- **function** `ufl.operators.curl(f)`
  Take the curl of f.

- **function** `ufl.operators.det(A)`
  Take the determinant of A.

- **function** `ufl.operators.dev(A)`
  Take the deviatoric part of A.

- **function** `ufl.operators.diag(A)`
  Diagonal ranl-2 tensor.
  Take the diagonal part of rank 2 tensor A or make a diagonal rank 2
  tensor from a rank 1 tensor.
  Always returns a rank 2 tensor. See also diag_vector.

- **function** `ufl.operators.diag_vector(A)`
  Take the diagonal part of rank 2 tensor A and return as a vector.
  See also diag.

- **function** `ufl.operators.diff(f, v)`
  Take the derivative of f with respect to the variable v.
  If f is a form, diff is applied to each integrand.

- **function** `ufl.operators.div(f)`
  Take the divergence of f.

Take the divergence of f.

- `This operator follows the div convention where`
  div(v) = v[i].dx(i)
  div(T)[:] = T[:,i].dx(i)

for vector expressions v, and
arbitrary rank tensor expressions T.

See also: nabla_div()

- **function** `ufl.operators.dot(a, b)`
  Take the dot product of a and b.
  This won’t take the complex conjugate of the second argument.

- **function** `ufl.operators.elem_div(A, B)`
  Take the elementwise division of tensors A and B with the same shape.

- **function** `ufl.operators.elem_mult(A, B)`
  Take the elementwise multiplication of tensors A and B with the same shape.

- **function** `ufl.operators.elem_op(op, *args)`
  Apply element-wise operations.
  Take the element-wise application of operator op on scalar values
  from one or more tensor arguments.

- **function** `ufl.operators.elem_op_items(op_ind, indices, *args)`
  Elem op items.

- **function** `ufl.operators.elem_pow(A, B)`
  Take the elementwise power of tensors A and B with the same shape.

- **function** `ufl.operators.eq(left, right)`
  A boolean expression (left == right) for use with conditional.

- **function** `ufl.operators.erf(f)`
  Take the error function of f.

- **function** `ufl.operators.exp(f)`
  Take the exponential of f.

- **function** `ufl.operators.exterior_derivative(f)`
  Take the exterior derivative of f.
  The exterior derivative uses the element Sobolev space to
  determine whether id, grad, curl or div should be used.
  Note that this uses the grad and div operators,
  as opposed to nabla_grad and nabla_div.

- **function** `ufl.operators.facet_avg(f)`
  Take the average of v over a facet.

- **function** `ufl.operators.ge(left, right)`
  A boolean expression (left >= right) for use with conditional.

- **function** `ufl.operators.grad(f)`
  Take the gradient of f.

Take the gradient of f.

- `This operator follows the grad convention where`
  grad(s)[i] = s.dx(i)
  grad(v)[i,j] = v[i].dx(j)
  grad(T)[:,i] = T[:].dx(i)

for scalar expressions s, vector expressions v,
and arbitrary rank tensor expressions T.

See also: nabla_grad()

- **function** `ufl.operators.gt(left, right)`
  A boolean expression (left > right) for use with conditional.

- **function** `ufl.operators.imag(f)`
  The imaginary part of f.

- **function** `ufl.operators.inner(a, b)`
  Take the inner product of a and b.
  The complex conjugate of the second argument is taken.

- **function** `ufl.operators.inv(A)`
  Take the inverse of A.

- **function** `ufl.operators.jump(v, n=None)`
  Take the jump of v across a facet.

- **function** `ufl.operators.le(left, right)`
  A boolean expression (left <= right) for use with conditional.

- **function** `ufl.operators.ln(f)`
  Take the natural logarithm of f.

- **function** `ufl.operators.lt(left, right)`
  A boolean expression (left < right) for use with conditional.

- **function** `ufl.operators.max_value(x, y)`
  Take the maximum of x and y.

- **function** `ufl.operators.min_value(x, y)`
  Take the minimum of x and y.

- **function** `ufl.operators.nabla_div(f)`
  Take the divergence of f.

Take the divergence of f.

- `This operator follows the div convention where`
  nabla_div(v) = v[i].dx(i)
  nabla_div(T)[:] = T[i,:].dx(i)

for vector expressions v, and
arbitrary rank tensor expressions T.

See also: div()

- **function** `ufl.operators.nabla_grad(f)`
  Take the gradient of f.

Take the gradient of f.

- `This operator follows the grad convention where`
  nabla_grad(s)[i] = s.dx(i)
  nabla_grad(v)[i,j] = v[j].dx(i)
  nabla_grad(T)[i,:] = T[:].dx(i)

for scalar expressions s, vector expressions v,
and arbitrary rank tensor expressions T.

See also: grad()

- **function** `ufl.operators.ne(left, right)`
  A boolean expression (left != right) for use with conditional.

- **function** `ufl.operators.outer(*operands)`
  Take the outer product of two or more operands.
  The complex conjugate of the first argument is taken.

- **function** `ufl.operators.perp(v)`
  Take the perp of v.
  I.e. (−v1,+v0).

- **function** `ufl.operators.rank(f)`
  The rank of f.

- **function** `ufl.operators.real(f)`
  The real part of f.

- **function** `ufl.operators.rot(f)`
  Take the curl of f.

- **function** `ufl.operators.shape(f)`
  The shape of f.

- **function** `ufl.operators.sign(x)`
  Return the sign of x.
  This returns +1 if x is positive, -1 if x is negative, and 0 if x is 0.

- **function** `ufl.operators.sin(f)`
  Take the sine of f.

- **function** `ufl.operators.sinh(f)`
  Take the hyperbolic sine of f.

- **function** `ufl.operators.skew(A)`
  Take the skew symmetric part of A.

- **function** `ufl.operators.sqrt(f)`
  Take the square root of f.

- **function** `ufl.operators.sym(A)`
  Take the symmetric part of A.

- **function** `ufl.operators.tan(f)`
  Take the tangent of f.

- **function** `ufl.operators.tanh(f)`
  Take the hyperbolic tangent of f.

- **function** `ufl.operators.tr(A)`
  Take the trace of A.

- **function** `ufl.operators.transpose(A)`
  Take the transposed of tensor A.

- **function** `ufl.operators.variable(e)`
  Define a variable representing the given expression.
  See also diff().

## ufl.permutation module

This module provides utility functions for computing permutations and generating index lists.

- **function** `ufl.permutation.build_component_numbering(shape, symmetry)`
  Build a numbering of components within the given value shape.
  This takes into consideration a symmetry mapping which leaves the
  mapping noncontiguous. Returns a dict { component -> numbering }
  and an ordered list of components [ numbering -> component ].  The
  dict contains all components while the list only contains the ones
  not mapped by the symmetry mapping.

- **function** `ufl.permutation.compute_indices(shape)`
  Compute all index combinations for given shape.

## ufl.precedence module

Precedence handling.

- **function** `ufl.precedence.assign_precedences(precedence_list)`
  Given a precedence list, assign ints to class._precedence.

- **function** `ufl.precedence.build_precedence_list()`
  Build precedence list.

- **function** `ufl.precedence.build_precedence_mapping(precedence_list)`
  Given a precedence list, build a dict with class->int mappings.
  Utility function used by some external code.

- **function** `ufl.precedence.parstr(child, parent, pre='(', post=')', format=<class 'str'>)`
  Parstr.

## ufl.protocols module

Protocols.

- **function** `ufl.protocols.id_or_none(obj)`
  Returns None if the object is None, obj.ufl_id() if available, or id(obj) if not.
  This allows external libraries to implement an alternative
  to id(obj) in the ufl_id() function, such that ufl can identify
  objects as the same without knowing about their types.

## ufl.pullback module

Pull back and push forward maps.

- **class** `class ufl.pullback.AbstractPullback`
  Bases: ABC
  An abstract pull back.

Bases: ABC

An abstract pull back.

- **method** `apply(expr: Expr, domain: AbstractDomain | None = None) → Expr`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `abstract property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `abstractmethod physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.pullback.ContravariantPiola`
  Bases: AbstractPullback
  The contravariant Piola pull back.

Bases: AbstractPullback

The contravariant Piola pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.pullback.CovariantContravariantPiola`
  Bases: AbstractPullback
  The covariant contravariant Piola pull back.

Bases: AbstractPullback

The covariant contravariant Piola pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element.

Get the physical value shape when this pull back is applied to an element.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.pullback.CovariantPiola`
  Bases: AbstractPullback
  The covariant Piola pull back.

Bases: AbstractPullback

The covariant Piola pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.pullback.CustomPullback`
  Bases: AbstractPullback
  Custom pull back.
  This should probably be removed.

Bases: AbstractPullback

Custom pull back.

This should probably be removed.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.pullback.DoubleContravariantPiola`
  Bases: AbstractPullback
  The double contravariant Piola pull back.

Bases: AbstractPullback

The double contravariant Piola pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.pullback.DoubleCovariantPiola`
  Bases: AbstractPullback
  The double covariant Piola pull back.

Bases: AbstractPullback

The double covariant Piola pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.pullback.IdentityPullback`
  Bases: AbstractPullback
  The identity pull back.

Bases: AbstractPullback

The identity pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.pullback.L2Piola`
  Bases: AbstractPullback
  The L2 Piola pull back.

Bases: AbstractPullback

The L2 Piola pull back.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.pullback.MixedPullback(element: _AbstractFiniteElement)`
  Bases: AbstractPullback
  Pull back for a mixed element.

Bases: AbstractPullback

Pull back for a mixed element.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **exception** `exception ufl.pullback.NonStandardPullbackException`
  Bases: BaseException
  Exception to raise if a map is non-standard.

- **class** `class ufl.pullback.PhysicalPullback`
  Bases: AbstractPullback
  Physical pull back.
  This should probably be removed.

Bases: AbstractPullback

Physical pull back.

This should probably be removed.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.pullback.SymmetricPullback(element: _AbstractFiniteElement, symmetry: dict[tuple[int, ...], int])`
  Bases: AbstractPullback
  Pull back for an element with symmetry.

Bases: AbstractPullback

Pull back for an element with symmetry.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.pullback.UndefinedPullback`
  Bases: AbstractPullback
  Undefined pull back.
  This should probably be removed.

Bases: AbstractPullback

Undefined pull back.

This should probably be removed.

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

## ufl.referencevalue module

Representation of the reference value of a function.

- **class** `class ufl.referencevalue.ReferenceValue(f)`
  Bases: Operator
  Representation of the reference cell value of a form argument.

Bases: Operator

Representation of the reference cell value of a form argument.

- **method** `evaluate(x, mapping, component, index_values, derivatives=())`
  Get child from mapping and return the component asked for.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **property** `property ufl_shape`
  Get the UFL shape.

## ufl.restriction module

Restriction operations.

- **class** `class ufl.restriction.NegativeRestricted(expression)`
  Bases: Restricted
  Negative restriction.

- **class** `class ufl.restriction.PositiveRestricted(expression)`
  Bases: Restricted
  Positive restriction.

- **class** `class ufl.restriction.Restricted(expression)`
  Bases: Operator
  Restriction.

Bases: Operator

Restriction.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **method** `side()`
  Get the side.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

## ufl.sobolevspace module

Sobolev spaces.

This module defines a symbolic heirarchy of Sobolev spaces to enable
symbolic reasoning about the spaces in which finite elements lie.

- **class** `class ufl.sobolevspace.DirectionalSobolevSpace(orders)`
  Bases: SobolevSpace
  Directional Sobolev space.
  Symbolic representation of a Sobolev space with varying smoothness
  in different spatial directions.

- **class** `class ufl.sobolevspace.SobolevSpace(name, parents=None)`
  Bases: object
  Symbolic representation of a Sobolev space.
  This implements a subset of the methods of a Python set so that
  finite elements and other Sobolev spaces can be tested for
  inclusion.

## ufl.sorting module

Sorting.

This module contains a sorting rule for expr objects that
is more robust w.r.t. argument numbering than using repr.

- **function** `ufl.sorting.cmp_expr(a, b)`
  Replacement for cmp(a, b), removed in Python 3, for Expr objects.

- **function** `ufl.sorting.sorted_expr(sequence)`
  Return a canonically sorted list of Expr objects in sequence.

- **function** `ufl.sorting.sorted_expr_sum(seq)`
  Sorted expr sum.

## ufl.split_functions module

Algorithm for splitting a Coefficient or Argument into subfunctions.

- **function** `ufl.split_functions.split(v)`
  Split a coefficient or argument.
  If v is a Coefficient or Argument in a mixed space, returns a tuple
  with the function components corresponding to the subelements.

## ufl.tensoralgebra module

Compound tensor algebra operations.

- **class** `class ufl.tensoralgebra.Cofactor(A)`
  Bases: CompoundTensorOperator
  Cofactor.

Bases: CompoundTensorOperator

Cofactor.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.tensoralgebra.CompoundTensorOperator(operands)`
  Bases: Operator
  Compount tensor operator.

Bases: Operator

Compount tensor operator.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.tensoralgebra.Cross(a, b)`
  Bases: CompoundTensorOperator
  Cross.

Bases: CompoundTensorOperator

Cross.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = (3,)`

- **class** `class ufl.tensoralgebra.Determinant(A)`
  Bases: CompoundTensorOperator
  Determinant.

Bases: CompoundTensorOperator

Determinant.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.tensoralgebra.Deviatoric(A)`
  Bases: CompoundTensorOperator
  Deviatoric.

Bases: CompoundTensorOperator

Deviatoric.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.tensoralgebra.Dot(a, b)`
  Bases: CompoundTensorOperator
  Dot.

Bases: CompoundTensorOperator

Dot.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.tensoralgebra.Inner(a, b)`
  Bases: CompoundTensorOperator
  Inner.

Bases: CompoundTensorOperator

Inner.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.tensoralgebra.Inverse(A)`
  Bases: CompoundTensorOperator
  Inverse.

Bases: CompoundTensorOperator

Inverse.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.tensoralgebra.Outer(a, b)`
  Bases: CompoundTensorOperator
  Outer.

Bases: CompoundTensorOperator

Outer.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.tensoralgebra.Perp(A)`
  Bases: CompoundTensorOperator
  Perp.

Bases: CompoundTensorOperator

Perp.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **attribute** `ufl_shape: tuple[int, ...] = (2,)`

- **class** `class ufl.tensoralgebra.Skew(A)`
  Bases: CompoundTensorOperator
  Skew.

Bases: CompoundTensorOperator

Skew.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.tensoralgebra.Sym(A)`
  Bases: CompoundTensorOperator
  Sym.

Bases: CompoundTensorOperator

Sym.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`

- **class** `class ufl.tensoralgebra.Trace(A)`
  Bases: CompoundTensorOperator
  Trace.

Bases: CompoundTensorOperator

Trace.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...] = ()`

- **class** `class ufl.tensoralgebra.Transposed(A)`
  Bases: CompoundTensorOperator
  Transposed tensor.

Bases: CompoundTensorOperator

Transposed tensor.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

## ufl.tensors module

Classes used to group scalar expressions into expressions with rank > 0.

- **class** `class ufl.tensors.ComponentTensor(expression, indices)`
  Bases: Operator
  Maps the free indices of a scalar valued expression to tensor axes.

Bases: Operator

Maps the free indices of a scalar valued expression to tensor axes.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **method** `indices()`
  Get indices.

- **attribute** `ufl_free_indices: tuple[int, ...]`

- **attribute** `ufl_index_dimensions`

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.tensors.ListTensor(*expressions)`
  Bases: Operator
  Wraps a list of expressions into a tensor valued expression of one higher rank.

Bases: Operator

Wraps a list of expressions into a tensor valued expression of one higher rank.

- **method** `evaluate(x, mapping, component, index_values, derivatives=())`
  Evaluate.

- **property** `property ufl_free_indices`

- **property** `property ufl_index_dimensions`

- **property** `property ufl_shape`
  Get the UFL shape.

- **function** `ufl.tensors.as_matrix(expressions, indices=None)`
  As as_tensor(), but limited to rank 2 tensors.

- **function** `ufl.tensors.as_scalar(expression)`
  As scalar.

As scalar.

- `Given a scalar or tensor valued expression A, returns either of the tuples::`
  (a,b) = (A, ())
  (a,b) = (A[indices], indices)

such that a is always a scalar valued expression.

- **function** `ufl.tensors.as_scalars(*expressions)`
  As scalars.

As scalars.

- `Given multiple scalar or tensor valued expressions A, returns either of the tuples::`
  (a,b) = (A, ())
  (a,b) = ([A[0][indices], …, A[-1][indices]], indices)

such that a is always a list of scalar valued expressions.

- **function** `ufl.tensors.as_tensor(expressions, indices=None)`
  Make a tensor valued expression.
  This works in two different ways, by using indices or lists.
  1) Returns A such that A [indices] = expressions.
  If indices are provided, expressions must be a scalar
  valued expression with all the provided indices among
  its free indices. This operator will then map each of these
  indices to a tensor axis, thereby making a tensor valued
  expression from a scalar valued expression with free indices.
  2) Returns A such that A[k,...] = expressions*[k].
  If no indices are provided, *expressions must be a list
  or tuple of expressions. The expressions can also consist
  of recursively nested lists to build higher rank tensors.

- **function** `ufl.tensors.as_vector(expressions, index=None)`
  As as_tensor(), but limited to rank 1 tensors.

- **function** `ufl.tensors.from_numpy_to_lists(expressions)`
  Convert Numpy array to lists.

- **function** `ufl.tensors.numpy2nestedlists(arr)`
  Convert Numpy array to a nested list.

- **function** `ufl.tensors.unit_indexed_tensor(shape, component)`
  Unit indexed tensor.

- **function** `ufl.tensors.unit_list(i, n)`
  Create a list of zeros where the ith entry is 1.

- **function** `ufl.tensors.unit_list2(i, j, n)`
  Creage a two dimensional list of zeros where the (i,j)th entry is 1.

- **function** `ufl.tensors.unit_matrices(d)`
  A tuple of constant unit matrices in all directions with dimension d.

- **function** `ufl.tensors.unit_matrix(i, j, d)`
  A constant unit matrix in direction i,*j* with dimension d.

- **function** `ufl.tensors.unit_vector(i, d)`
  A constant unit vector in direction i with dimension d.

- **function** `ufl.tensors.unit_vectors(d)`
  A tuple of constant unit vectors in all directions with dimension d.

- **function** `ufl.tensors.unwrap_list_tensor(lt)`
  Unwrap a list tensor.

## ufl.variable module

Define the Variable and Label classes.

These are used to label expressions as variables for differentiation.

- **class** `class ufl.variable.Label(count=None)`
  Bases: Terminal, Counted
  Label.

Bases: Terminal, Counted

Label.

- **method** `is_cellwise_constant()`
  Return true if the object is constant on each cell.

- **method** `ufl_domains()`
  Return tuple of domains related to this terminal object.

- **property** `property ufl_free_indices`
  Get the UFL free indices.

- **property** `property ufl_index_dimensions`
  Get the UFL index dimensions.

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.variable.Variable(expression, label=None)`
  Bases: Operator
  A Variable is a representative for another expression.
  It will be used by the end-user mainly for defining
  a quantity to differentiate w.r.t. using diff.
  Example:

Bases: Operator

A Variable is a representative for another expression.

It will be used by the end-user mainly for defining
a quantity to differentiate w.r.t. using diff.
Example:

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **method** `expression()`
  Get expression.

- **method** `label()`
  Get label.

- **method** `ufl_domains()`
  Get the UFL domains.

- **attribute** `ufl_free_indices: tuple[int, ...] = ()`

- **attribute** `ufl_index_dimensions = ()`

- **property** `property ufl_shape`

## Module contents

UFL: The Unified Form Language.

The Unified Form Language is an embedded domain specific language
for definition of variational forms intended for finite element
discretization. More precisely, it defines a fixed interface for choosing
finite element spaces and defining expressions for weak forms in a
notation close to the mathematical one.

This Python module contains the language as well as algorithms to work
with it.

Classes and algorithms are considered implementation details and
should not be used in form definitions.

For more details on the language, see

and

The development version can be found in the repository at

A very brief overview of the language contents follows:

- **class** `class ufl.AbstractCell`
  Bases: UFLObject
  A base class for all cells.

Bases: UFLObject

A base class for all cells.

- **method** `abstractmethod cellname() → str`
  Return the cellname of the cell.

- **method** `edge_types() → tuple[AbstractCell, ...]`
  Get the unique edge types.

- **method** `edges() → tuple[AbstractCell, ...]`
  Get the edges.

- **method** `face_types() → tuple[AbstractCell, ...]`
  Get the unique face types.

- **method** `faces() → tuple[AbstractCell, ...]`
  Get the faces.

- **method** `facet_types() → tuple[AbstractCell, ...]`
  Get the unique facet types.
  Facets are entities of dimension tdim-1.

- **method** `facets() → tuple[AbstractCell, ...]`
  Get the facets.
  Facets are entities of dimension tdim-1.

- **method** `abstractmethod has_simplex_facets() → bool`
  Return True if all the facets of this cell are simplex cells.

- **method** `abstractmethod is_simplex() → bool`
  Return True if this is a simplex cell.

- **method** `num_edges() → int`
  Get the number of edges.

- **method** `num_faces() → int`
  Get the number of faces.

- **method** `num_facets() → int`
  Get the number of facets.
  Facets are entities of dimension tdim-1.

- **method** `num_peaks() → int`
  Get the number of peaks.
  Peaks are entities of dimension tdim-3.

- **method** `num_ridges() → int`
  Get the number of ridges.
  Ridges are entities of dimension tdim-2.

- **method** `abstractmethod num_sub_entities(dim: int) → int`
  Get the number of sub-entities of the given dimension.

- **method** `num_vertices() → int`
  Get the number of vertices.

- **method** `peak_types() → tuple[AbstractCell, ...]`
  Get the unique peak types.
  Peaks are entities of dimension tdim-3.

- **method** `peaks() → tuple[AbstractCell, ...]`
  Get the peaks.
  Peaks are entities of dimension tdim-3.

- **method** `abstractmethod reconstruct(**kwargs: Any) → AbstractCell`
  Reconstruct this cell, overwriting properties by those in kwargs.

- **method** `ridge_types() → tuple[AbstractCell, ...]`
  Get the unique ridge types.
  Ridges are entities of dimension tdim-2.

- **method** `ridges() → tuple[AbstractCell, ...]`
  Get the ridges.
  Ridges are entities of dimension tdim-2.

- **method** `abstractmethod sub_entities(dim: int) → tuple[AbstractCell, ...]`
  Get the sub-entities of the given dimension.

- **method** `abstractmethod sub_entity_types(dim: int) → tuple[AbstractCell, ...]`
  Get the unique sub-entity types of the given dimension.

- **method** `abstractmethod topological_dimension() → int`
  Return the dimension of the topology of this cell.

- **method** `vertex_types() → tuple[AbstractCell, ...]`
  Get the unique vertices types.

- **method** `vertices() → tuple[AbstractCell, ...]`
  Get the vertices.

- **class** `class ufl.AbstractDomain(topological_dimension, geometric_dimension)`
  Bases: object
  Symbolic representation of a geometric domain.
  Domain has only a geometric and a topological dimension.

Bases: object

Symbolic representation of a geometric domain.

Domain has only a geometric and a topological dimension.

- **method** `can_make_function_space(element: AbstractFiniteElement) → bool`
  Check whether this mesh can make a function space with element.

- **method** `geometric_dimension()`
  Return the dimension of the space this domain is embedded in.

- **method** `iterable_like(element: AbstractFiniteElement) → Iterable[Mesh] | MeshSequence`
  Return iterable object that is iterable like element.

- **property** `property meshes`
  Return the component meshes.

- **method** `topological_dimension()`
  Return the dimension of the topology of this domain.

- **class** `class ufl.AbstractFiniteElement`
  Bases: ABC
  Base class for all finite elements.
  To make your element library compatible with UFL, you should make a
  subclass of AbstractFiniteElement and provide implementions of all
  the abstract methods and properties. All methods and properties that
  are not marked as abstract are implemented here and should not need
  to be overwritten in your subclass.
  An example of how the methods in your subclass could be implemented
  can be found in Basix; see
  https://github.com/FEniCS/basix/blob/main/python/basix/ufl.py

Bases: ABC

Base class for all finite elements.

To make your element library compatible with UFL, you should make a
subclass of AbstractFiniteElement and provide implementions of all
the abstract methods and properties. All methods and properties that
are not marked as abstract are implemented here and should not need
to be overwritten in your subclass.

An example of how the methods in your subclass could be implemented
can be found in Basix; see
https://github.com/FEniCS/basix/blob/main/python/basix/ufl.py

- **property** `abstract property cell: Cell`
  Return the cell of the finite element.

- **property** `abstract property embedded_subdegree: int`
  Degree of the maximum degree Lagrange space that is spanned by this element.
  This returns the degree of the highest degree Lagrange space
  such that the polynomial space of the Lagrange space is a
  subspace of this element’s polynomial space. If this element’s
  polynomial space does not include the constant function, this
  function should return -1.
  Note that on a simplex cells, the polynomial space of Lagrange
  space is a complete polynomial space, but on other cells this is
  not true. For example, on quadrilateral cells, the degree 1
  Lagrange space includes the degree 2 polynomial xy.

- **property** `abstract property embedded_superdegree: int | None`
  Degree of the minimum degree Lagrange space that spans this element.
  This returns the degree of the lowest degree Lagrange space such
  that the polynomial space of the Lagrange space is a superspace
  of this element’s polynomial space. If this element contains
  basis functions that are not in any Lagrange space, this
  function should return None.
  Note that on a simplex cells, the polynomial space of Lagrange
  space is a complete polynomial space, but on other cells this is
  not true. For example, on quadrilateral cells, the degree 1
  Lagrange space includes the degree 2 polynomial xy.

- **method** `is_cellwise_constant() → bool`
  Check whether this element is spatially constant over each cell.

- **property** `property num_sub_elements: int`
  Return number of sub-elements.
  This function does not recurse: ie it does not count the sub-elements of
  sub-elements.

- **property** `abstract property pullback: AbstractPullback`
  Return the pullback for this element.

- **property** `abstract property reference_value_shape: tuple[int, ...]`
  Return the shape of the value space on the reference cell.

- **property** `property reference_value_size: int`
  Return the integer product of the reference value shape.

- **property** `abstract property sobolev_space: SobolevSpace`
  Return the underlying Sobolev space.

- **property** `abstract property sub_elements: Sequence`
  Return list of sub-elements.
  This function does not recurse: ie it does not extract the sub-elements
  of sub-elements.

- **class** `class ufl.AbstractPullback`
  Bases: ABC
  An abstract pull back.

Bases: ABC

An abstract pull back.

- **method** `apply(expr: Expr, domain: AbstractDomain | None = None) → Expr`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `abstract property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `abstractmethod physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **class** `class ufl.Action(*args, **kw)`
  Bases: BaseForm
  UFL base form type: respresents the action of an object on another.

Bases: BaseForm

UFL base form type: respresents the action of an object on another.

- `For example:`
  res = Ax

A would be the first argument, left and x would be the second argument,
right.

Action objects will result when the action of an assembled object
(e.g. a Matrix) is taken. This delays the evaluation of the action until
assembly occurs.

- **method** `equals(other)`
  Check if two Actions are equal.

- **method** `left()`
  Get left.

- **method** `right()`
  Get right.

- **method** `ufl_domains()`
  Return all domains found in the base form.

- **method** `ufl_function_spaces()`
  Get the tuple of function spaces of the underlying form.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.Adjoint(*args, **kw)`
  Bases: BaseForm
  UFL base form type: represents the adjoint of an object.
  Adjoint objects will result when the adjoint of an assembled object
  (e.g. a Matrix) is taken. This delays the evaluation of the adjoint until
  assembly occurs.

Bases: BaseForm

UFL base form type: represents the adjoint of an object.

Adjoint objects will result when the adjoint of an assembled object
(e.g. a Matrix) is taken. This delays the evaluation of the adjoint until
assembly occurs.

- **method** `equals(other)`
  Check if two Adjoints are equal.

- **method** `form()`
  Return the form.

- **method** `ufl_domains()`
  Return all domains found in the base form.

- **method** `ufl_function_spaces()`
  Get the tuple of function spaces of the underlying form.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **function** `ufl.And(left, right)`
  A boolean expression (left and right) for use with conditional.

- **class** `class ufl.Argument(*args, **kw)`
  Bases: FormArgument, BaseArgument
  UFL value: Representation of an argument to a form.

Bases: FormArgument, BaseArgument

UFL value: Representation of an argument to a form.

- **method** `ufl_domains()`
  Return UFL domains.

- **function** `ufl.Arguments(function_space, number)`
  Create an Argument in a mixed space.
  Returns a tuple with the function components corresponding to the subelements.

- **class** `class ufl.BaseForm`
  Bases: object
  Description of an object containing arguments.

Bases: object

Description of an object containing arguments.

- **method** `arguments()`
  Return all Argument objects found in form.

- **method** `coefficients()`
  Return all Coefficient objects found in form.

- **method** `empty()`
  Returns whether the BaseForm has no components.

- **method** `geometric_quantities()`
  Return all GeometricQuantity objects found in form.

- **method** `ufl_domain()`
  Return the single geometric integration domain occuring in the base form.
  Fails if multiple domains are found.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.Cell(cellname: str)`
  Bases: AbstractCell
  Representation of a named finite element cell with known structure.

Bases: AbstractCell

Representation of a named finite element cell with known structure.

- **method** `cellname() → str`
  Return the cellname of the cell.

- **method** `has_simplex_facets() → bool`
  Return True if all the facets of this cell are simplex cells.

- **method** `is_simplex() → bool`
  Return True if this is a simplex cell.

- **method** `num_sub_entities(dim: int) → int`
  Get the number of sub-entities of the given dimension.

- **method** `reconstruct(**kwargs: Any) → Cell`
  Reconstruct this cell, overwriting properties by those in kwargs.

- **method** `sub_entities(dim: int) → tuple[AbstractCell, ...]`
  Get the sub-entities of the given dimension.

- **method** `sub_entity_types(dim: int) → tuple[AbstractCell, ...]`
  Get the unique sub-entity types of the given dimension.

- **method** `topological_dimension() → int`
  Return the dimension of the topology of this cell.

- **class** `class ufl.CellDiameter(domain)`
  Bases: GeometricCellQuantity
  The diameter of the cell, i.e., maximal distance of two points in the cell.

Bases: GeometricCellQuantity

The diameter of the cell, i.e., maximal distance of two points in the cell.

- **attribute** `name = 'diameter'`

- **class** `class ufl.CellNormal(domain)`
  Bases: GeometricCellQuantity
  The upwards pointing normal vector of the current manifold cell.

Bases: GeometricCellQuantity

The upwards pointing normal vector of the current manifold cell.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'cell_normal'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.CellVolume(domain)`
  Bases: GeometricCellQuantity
  The volume of the cell.

Bases: GeometricCellQuantity

The volume of the cell.

- **attribute** `name = 'volume'`

- **class** `class ufl.Circumradius(domain)`
  Bases: GeometricCellQuantity
  The circumradius of the cell.

Bases: GeometricCellQuantity

The circumradius of the cell.

- **attribute** `name = 'circumradius'`

- **class** `class ufl.Coargument(*args, **kw)`
  Bases: BaseForm, BaseArgument
  UFL value: Representation of an argument to a form in a dual space.

Bases: BaseForm, BaseArgument

UFL value: Representation of an argument to a form in a dual space.

- **method** `arguments(outer_form=None)`
  Return all Argument objects found in form.

- **method** `equals(other)`
  Check equality.

- **method** `ufl_domain()`
  Return the UFL domain.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.Coefficient(*args, **kw)`
  Bases: FormArgument, BaseCoefficient
  UFL form argument type: Representation of a form coefficient.

Bases: FormArgument, BaseCoefficient

UFL form argument type: Representation of a form coefficient.

- **method** `ufl_domains()`
  Get the UFL domains.

- **function** `ufl.Coefficients(function_space)`
  Create a Coefficient in a mixed space.
  Returns a tuple with the function components corresponding to the subelements.

- **class** `class ufl.Cofunction(*args, **kw)`
  Bases: BaseCoefficient, BaseForm
  UFL form argument type: Representation of a form coefficient from a dual space.

Bases: BaseCoefficient, BaseForm

UFL form argument type: Representation of a form coefficient from a dual space.

- **method** `equals(other)`
  Check equality.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.Constant(domain, shape=(), count=None)`
  Bases: Terminal, Counted
  Constant.

Bases: Terminal, Counted

Constant.

- **method** `is_cellwise_constant()`
  Return True if the function is cellwise constant.

- **method** `ufl_domain()`
  Get the UFL domain.

- **method** `ufl_domains()`
  Get the UFL domains.

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.DSIntegralDomain(coordinate_element_positive_side: AbstractFiniteElement, coordinate_element_negative_side: AbstractFiniteElement, facet_type: AbstractCell)`
  Bases: AbstractIntegralDomain
  Integral domain for dS.

Bases: AbstractIntegralDomain

Integral domain for dS.

- **property** `property integral_type: str`
  Integral type.

- **function** `ufl.Dn(f)`
  Take the directional derivative of f in the facet normal direction.
  The facet normal is Dn(f) := dot(grad(f), n).

- **class** `class ufl.DsIntegralDomain(coordinate_element: AbstractFiniteElement, facet_type: AbstractCell)`
  Bases: AbstractIntegralDomain
  Integral domain for ds.

Bases: AbstractIntegralDomain

Integral domain for ds.

- **property** `property integral_type: str`
  Integral type.

- **function** `ufl.Dx(f, *i)`
  Take the partial derivative of f with respect to spatial variable number i.
  Equivalent to f.dx(*i).

- **class** `class ufl.DxIntegralDomain(coordinate_element: AbstractFiniteElement)`
  Bases: AbstractIntegralDomain
  Integral domain for dx.

Bases: AbstractIntegralDomain

Integral domain for dx.

- **property** `property integral_type: str`
  Integral type.

- **class** `class ufl.ExternalOperator(*operands, function_space, derivatives=None, argument_slots=())`
  Bases: BaseFormOperator
  External operator.

Bases: BaseFormOperator

External operator.

- **method** `assemble(*args, **kwargs)`
  Assemble the external operator.

- **method** `grad()`
  Returns the symbolic grad of the external operator.

- **method** `ufl_element()`
  Shortcut to get the finite element of the function space of the external operator.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.FacetArea(domain)`
  Bases: GeometricFacetQuantity
  The area of the facet.

Bases: GeometricFacetQuantity

The area of the facet.

- **attribute** `name = 'facetarea'`

- **class** `class ufl.FacetNormal(domain)`
  Bases: GeometricFacetQuantity
  The outwards pointing normal vector of the current facet.

Bases: GeometricFacetQuantity

The outwards pointing normal vector of the current facet.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'n'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.Form(integrals)`
  Bases: BaseForm
  Description of a weak form consisting of a sum of integrals over subdomains.

Bases: BaseForm

Description of a weak form consisting of a sum of integrals over subdomains.

- **method** `base_form_operators()`
  Return all BaseFormOperator objects found in form.

- **method** `coefficient_numbering()`
  Return a contiguous numbering of coefficients in a mapping {coefficient:number}.

- **method** `coefficients()`
  Return all Coefficient objects found in form.

- **method** `constant_numbering()`
  Return a contiguous numbering of constants in a mapping {constant:number}.

- **method** `constants()`
  Get constants.

- **method** `domain_numbering()`
  Return a contiguous numbering of domains in a mapping {domain:number}.

- **method** `empty()`
  Returns whether the form has no integrals.

- **method** `equals(other)`
  Evaluate bool(lhs_form == rhs_form).

- **method** `geometric_dimension()`
  Return the geometric dimension shared by all domains and functions in this form.

- **method** `integrals()`
  Return a sequence of all integrals in form.

- **method** `integrals_by_domain(domain)`
  Return a sequence of all integrals with a particular integration domain.

- **method** `integrals_by_type(integral_type)`
  Return a sequence of all integrals with a particular domain type.

- **method** `signature()`
  Signature for use with jit cache (independent of incidental numbering of indices etc).

- **method** `subdomain_data()`
  Returns a mapping on the form {domain:{integral_type: subdomain_data}}.

- **method** `terminal_numbering()`
  Return a contiguous numbering for all counted objects in the form.
  The returned object is mapping from terminal to its number (an integer).
  The numbering is computed per type so Coefficient,
  Constant, etc will each be numbered from zero.

- **method** `ufl_cell()`
  Return the single cell this form is defined on.
  Fails if multiple cells are found.

- **method** `ufl_domains()`
  Return the geometric integration domains occuring in the form.
  NB! This does not include domains of coefficients defined on
  other meshes.
  The return type is a tuple even if only a single domain exists.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.FormSum(*args, **kwargs)`
  Bases: BaseForm
  Form sum.
  Description of a weighted sum of variational forms and form-like objects
  components is the list of Forms to be summed
  arg_weights is a list of tuples of component index and weight

Bases: BaseForm

Form sum.

Description of a weighted sum of variational forms and form-like objects
components is the list of Forms to be summed
arg_weights is a list of tuples of component index and weight

- **method** `components()`
  Get components.

- **method** `empty()`
  Returns whether the FormSum has no components.

- **method** `equals(other)`
  Evaluate bool(lhs_form == rhs_form).

- **method** `ufl_domains()`
  Return all domains found in the base form.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **method** `weights()`
  Get weights.

- **class** `class ufl.FunctionSpace(domain, element, label='')`
  Bases: BaseFunctionSpace, UFLObject
  Representation of a Function space.

Bases: BaseFunctionSpace, UFLObject

Representation of a Function space.

- **method** `dual()`
  Get the dual of the space.

- **class** `class ufl.Identity(dim)`
  Bases: ConstantValue
  Representation of an identity matrix.

Bases: ConstantValue

Representation of an identity matrix.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.Index(count=None)`
  Bases: IndexBase, Counted
  UFL value: An index with no value assigned.
  Used to represent free indices in Einstein indexing notation.

- **class** `class ufl.Integral(integrand, integral_type, domain, subdomain_id, metadata, subdomain_data)`
  Bases: object
  An integral over a single domain.

Bases: object

An integral over a single domain.

- **method** `integral_type()`
  Return the domain type of this integral.

- **method** `integrand()`
  Return the integrand expression, which is an Expr instance.

- **method** `metadata()`
  Return the compiler metadata this integral has been annotated with.

- **method** `reconstruct(integrand=None, integral_type=None, domain=None, subdomain_id=None, metadata=None, subdomain_data=None)`
  Construct a new Integral object with some properties replaced with new values.

Construct a new Integral object with some properties replaced with new values.

- `Example:`
  <a = Integral instance>
  b = a.reconstruct(expand_compounds(a.integrand()))
  c = a.reconstruct(metadata={‘quadrature_degree’:2})

- **method** `subdomain_data()`
  Return the domain data of this integral.

- **method** `subdomain_id()`
  Return the subdomain id of this integral.

- **method** `ufl_domain()`
  Return the integration domain of this integral.

- **class** `class ufl.Interpolate(expr, v)`
  Bases: BaseFormOperator
  Symbolic representation of the interpolation operator.

Bases: BaseFormOperator

Symbolic representation of the interpolation operator.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.Jacobian(domain)`
  Bases: GeometricCellQuantity
  The Jacobian of the mapping from reference cell to spatial coordinates.

Bases: GeometricCellQuantity

The Jacobian of the mapping from reference cell to spatial coordinates.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'J'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.JacobianDeterminant(domain)`
  Bases: GeometricCellQuantity
  The determinant of the Jacobian.
  Represents the signed determinant of a square Jacobian or the
  pseudo-determinant of a non-square Jacobian.

Bases: GeometricCellQuantity

The determinant of the Jacobian.

Represents the signed determinant of a square Jacobian or the
pseudo-determinant of a non-square Jacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'detJ'`

- **class** `class ufl.JacobianInverse(domain)`
  Bases: GeometricCellQuantity
  The inverse of the Jacobian.
  Represents the inverse of a square Jacobian or the pseudo-inverse of
  a non-square Jacobian.

Bases: GeometricCellQuantity

The inverse of the Jacobian.

Represents the inverse of a square Jacobian or the pseudo-inverse of
a non-square Jacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'K'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.Label(count=None)`
  Bases: Terminal, Counted
  Label.

Bases: Terminal, Counted

Label.

- **method** `is_cellwise_constant()`
  Return true if the object is constant on each cell.

- **method** `ufl_domains()`
  Return tuple of domains related to this terminal object.

- **property** `property ufl_free_indices`
  Get the UFL free indices.

- **property** `property ufl_index_dimensions`
  Get the UFL index dimensions.

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.Matrix(row_space, column_space, count=None)`
  Bases: BaseForm, Counted
  An assemble linear operator between two function spaces.

Bases: BaseForm, Counted

An assemble linear operator between two function spaces.

- **method** `equals(other)`
  Check equality.

- **method** `ufl_function_spaces()`
  Get the tuple of function spaces of this coefficient.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **class** `class ufl.MaxCellEdgeLength(domain)`
  Bases: GeometricCellQuantity
  The maximum edge length of the cell.

Bases: GeometricCellQuantity

The maximum edge length of the cell.

- **attribute** `name = 'maxcelledgelength'`

- **class** `class ufl.MaxFacetEdgeLength(domain)`
  Bases: GeometricFacetQuantity
  The maximum edge length of the facet.

Bases: GeometricFacetQuantity

The maximum edge length of the facet.

- **attribute** `name = 'maxfacetedgelength'`

- **class** `class ufl.Measure(integral_type, domain=None, subdomain_id='everywhere', metadata=None, subdomain_data=None)`
  Bases: object
  Representation of an integration measure.
  The Measure object holds information about integration properties
  to be transferred to a Form on multiplication with a scalar
  expression.

Bases: object

Representation of an integration measure.

The Measure object holds information about integration properties
to be transferred to a Form on multiplication with a scalar
expression.

- **method** `integral_type()`
  Return the domain type.
  Valid domain types are “cell”, “exterior_facet”, “interior_facet”, etc.

- **method** `metadata()`
  Return the integral metadata.
  This data is not interpreted by UFL.
  It is passed to the form compiler which can ignore it or use
  it to compile each integral of a form in a different way.

- **method** `reconstruct(integral_type=None, subdomain_id=None, domain=None, metadata=None, subdomain_data=None)`
  Construct a new Measure object with some properties replaced with new values.

Construct a new Measure object with some properties replaced with new values.

- `Example:`
  <dm = Measure instance>
  b = dm.reconstruct(subdomain_id=2)
  c = dm.reconstruct(metadata={ “quadrature_degree”: 3 })

- `Used by the call operator, so this is equivalent:`
  b = dm(2)
  c = dm(0, { “quadrature_degree”: 3 })

- **method** `subdomain_data()`
  Return the integral subdomain_data.
  This data is not interpreted by
  UFL.  Its intension is to give a context in which the domain
  id is interpreted.

- **method** `subdomain_id()`
  Return the domain id of this measure (integer).

- **method** `ufl_domain()`
  Return the domain associated with this measure.
  This may be None or a Domain object.

- **class** `class ufl.Mesh(coordinate_element, ufl_id=None, cargo=None)`
  Bases: AbstractDomain, UFLObject
  Symbolic representation of a mesh.

Bases: AbstractDomain, UFLObject

Symbolic representation of a mesh.

- **method** `can_make_function_space(element: AbstractFiniteElement) → bool`
  Check whether this mesh can make a function space with element.

- **method** `is_piecewise_linear_simplex_domain()`
  Check if the domain is a piecewise linear simplex.

- **method** `iterable_like(element: AbstractFiniteElement) → Iterable[Mesh]`
  Return iterable object that is iterable like element.

- **property** `property meshes`
  Return the component meshes.

- **method** `ufl_cargo()`
  Return carried object that will not be used by UFL.

- **method** `ufl_cell()`
  Get the cell.

- **method** `ufl_coordinate_element()`
  Get the coordinate element.

- **method** `ufl_id()`
  Return the ufl_id of this object.

- **class** `class ufl.MeshSequence(meshes: Sequence[Mesh])`
  Bases: AbstractDomain, UFLObject
  Symbolic representation of a mixed mesh.
  This class represents a collection of meshes that, along with
  a MixedElement, represent a mixed function space defined on
  multiple domains. This abstraction allows for defining the
  mixed function space with the conventional FunctionSpace
  class and integrating multi-domain problems seamlessly.
  Currently, all component meshes must have the same cell type (and
  thus the same topological dimension).
  Currently, one can only perform cell integrations when
  MeshSequence is used.

Bases: AbstractDomain, UFLObject

Symbolic representation of a mixed mesh.

This class represents a collection of meshes that, along with
a MixedElement, represent a mixed function space defined on
multiple domains. This abstraction allows for defining the
mixed function space with the conventional FunctionSpace
class and integrating multi-domain problems seamlessly.

Currently, all component meshes must have the same cell type (and
thus the same topological dimension).

Currently, one can only perform cell integrations when
MeshSequence is used.

- **method** `can_make_function_space(element: AbstractFiniteElement) → bool`
  Check whether this mesh can make a function space with element.

- **method** `iterable_like(element: AbstractFiniteElement) → MeshSequence`
  Return iterable object that is iterable like element.

- **property** `property meshes`
  Return the component meshes.

- **method** `ufl_cell()`
  Get the cell.

- **class** `class ufl.MeshView(mesh, topological_dimension, ufl_id=None)`
  Bases: AbstractDomain, UFLObject
  Symbolic representation of a mesh.

Bases: AbstractDomain, UFLObject

Symbolic representation of a mesh.

- **method** `is_piecewise_linear_simplex_domain()`
  Check if the domain is a piecewise linear simplex.

- **method** `ufl_cell()`
  Get the cell.

- **method** `ufl_id()`
  Return the ufl_id of this object.

- **method** `ufl_mesh()`
  Get the mesh.

- **class** `class ufl.MinCellEdgeLength(domain)`
  Bases: GeometricCellQuantity
  The minimum edge length of the cell.

Bases: GeometricCellQuantity

The minimum edge length of the cell.

- **attribute** `name = 'mincelledgelength'`

- **class** `class ufl.MinFacetEdgeLength(domain)`
  Bases: GeometricFacetQuantity
  The minimum edge length of the facet.

Bases: GeometricFacetQuantity

The minimum edge length of the facet.

- **attribute** `name = 'minfacetedgelength'`

- **class** `class ufl.MixedFunctionSpace(*args)`
  Bases: AbstractFunctionSpace, UFLObject
  Mixed function space.

Bases: AbstractFunctionSpace, UFLObject

Mixed function space.

- **method** `dual(*args)`
  Return the dual to this function space.
  If no additional arguments are passed then a MixedFunctionSpace is
  returned whose components are the duals of the originals.
  If additional arguments are passed, these must be integers. In this
  case, the MixedFunctionSpace which is returned will have dual
  components in the positions corresponding to the arguments passed, and
  the original components in the other positions.

- **method** `num_sub_spaces()`
  Return number of subspaces.

- **method** `ufl_domain()`
  Return ufl domain.

- **method** `ufl_domains()`
  Return ufl domains.

- **method** `ufl_element()`
  Return ufl element.

- **method** `ufl_elements()`
  Return ufl elements.

- **method** `ufl_sub_space(i)`
  Return i-th ufl sub space.

- **method** `ufl_sub_spaces()`
  Return ufl sub spaces.

- **class** `class ufl.MixedPullback(element: _AbstractFiniteElement)`
  Bases: AbstractPullback
  Pull back for a mixed element.

Bases: AbstractPullback

Pull back for a mixed element.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **function** `ufl.Not(condition)`
  A boolean expression (not condition) for use with conditional.

- **function** `ufl.Or(left, right)`
  A boolean expression (left or right) for use with conditional.

- **class** `class ufl.PermutationSymbol(dim)`
  Bases: ConstantValue
  Representation of a permutation symbol.
  This is also known as the Levi-Civita symbol, antisymmetric symbol,
  or alternating symbol.

Bases: ConstantValue

Representation of a permutation symbol.

This is also known as the Levi-Civita symbol, antisymmetric symbol,
or alternating symbol.

- **method** `evaluate(x, mapping, component, index_values)`
  Evaluate.

- **attribute** `ufl_shape: tuple[int, ...]`

- **class** `class ufl.RidgeJacobian(domain)`
  Bases: GeometricRidgeQuantity
  The Jacobian of the mapping from reference ridge to spatial coordinates.
  The RidgeJacobian is the product of the Jacobian and CellRidgeJacobian:

Bases: GeometricRidgeQuantity

The Jacobian of the mapping from reference ridge to spatial coordinates.

The RidgeJacobian is the product of the Jacobian and CellRidgeJacobian:

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'RJ'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.RidgeJacobianDeterminant(domain)`
  Bases: GeometricRidgeQuantity
  The pseudo-determinant of the RidgeJacobian.

Bases: GeometricRidgeQuantity

The pseudo-determinant of the RidgeJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'detRJ'`

- **class** `class ufl.RidgeJacobianInverse(domain)`
  Bases: GeometricRidgeQuantity
  The pseudo-inverse of the RidgeJacobian.

Bases: GeometricRidgeQuantity

The pseudo-inverse of the RidgeJacobian.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'EK'`

- **property** `property ufl_shape`
  Get the UFL shape.

- **class** `class ufl.SpatialCoordinate(domain)`
  Bases: GeometricCellQuantity
  The coordinate in a domain.
  In the context of expression integration,
  represents the domain coordinate of each quadrature point.
  In the context of expression evaluation in a point,
  represents the value of that point.

Bases: GeometricCellQuantity

The coordinate in a domain.

In the context of expression integration,
represents the domain coordinate of each quadrature point.

In the context of expression evaluation in a point,
represents the value of that point.

- **method** `count()`
  Count.

- **method** `evaluate(x, mapping, component, index_values)`
  Return the value of the coordinate.

- **method** `is_cellwise_constant()`
  Return whether this expression is spatially constant over each cell.

- **attribute** `name = 'x'`

- **property** `property ufl_shape`
  Return the number of coordinates defined (i.e. the geometric dimension of the domain).

- **class** `class ufl.SymmetricPullback(element: _AbstractFiniteElement, symmetry: dict[tuple[int, ...], int])`
  Bases: AbstractPullback
  Pull back for an element with symmetry.

Bases: AbstractPullback

Pull back for an element with symmetry.

- **method** `apply(expr, domain=None)`
  Apply the pull back.

Apply the pull back.

- `Args:`
  expr: A function on a physical cell
  domain: The domain on which the function is defined

Returns: The function pulled back to the reference cell

- **property** `property is_identity: bool`
  Is this pull back the identity (or the identity applied to mutliple components).

- **method** `physical_value_shape(element, domain) → tuple[int, ...]`
  Get the physical value shape when this pull back is applied to an element on a domain.

Get the physical value shape when this pull back is applied to an element on a domain.

- `Args:`
  element: The element that the pull back is applied to
  domain: The domain

- `Returns:`
  The value shape when the pull back is applied to the given element

- **function** `ufl.TensorConstant(domain, count=None)`
  Tensor constant.

- **class** `class ufl.TensorProductCell(*cells: AbstractCell)`
  Bases: AbstractCell
  Tensor product cell.

Bases: AbstractCell

Tensor product cell.

- **method** `cellname() → str`
  Return the cellname of the cell.

- **method** `has_simplex_facets() → bool`
  Return True if all the facets of this cell are simplex cells.

- **method** `is_simplex() → bool`
  Return True if this is a simplex cell.

- **method** `num_sub_entities(dim: int) → int`
  Get the number of sub-entities of the given dimension.

- **method** `reconstruct(**kwargs: Any) → AbstractCell`
  Reconstruct this cell, overwriting properties by those in kwargs.

- **method** `sub_cells() → tuple[AbstractCell, ...]`
  Return list of cell factors.

- **method** `sub_entities(dim: int) → tuple[AbstractCell, ...]`
  Get the sub-entities of the given dimension.

- **method** `sub_entity_types(dim: int) → tuple[AbstractCell, ...]`
  Get the unique sub-entity types of the given dimension.

- **method** `topological_dimension() → int`
  Return the dimension of the topology of this cell.

- **function** `ufl.TestFunction(function_space, part=None)`
  UFL value: Create a test function argument to a form.

- **function** `ufl.TestFunctions(function_space)`
  Create a TestFunction in a mixed space.
  Returns a tuple with the function components corresponding to the
  subelements.

- **function** `ufl.TrialFunction(function_space, part=None)`
  UFL value: Create a trial function argument to a form.

- **function** `ufl.TrialFunctions(function_space)`
  Create a TrialFunction in a mixed space.
  Returns a tuple with the function components corresponding to the
  subelements.

- **function** `ufl.VectorConstant(domain, count=None)`
  Vector constant.

- **class** `class ufl.ZeroBaseForm(arguments)`
  Bases: BaseForm
  Description of a zero base form.
  ZeroBaseForm is idempotent with respect to assembly and is mostly
  used for sake of simplifying base-form expressions.

Bases: BaseForm

Description of a zero base form.

ZeroBaseForm is idempotent with respect to assembly and is mostly
used for sake of simplifying base-form expressions.

- **attribute** `form`

- **method** `ufl_domains()`
  Return all domains found in the base form.

- **attribute** `ufl_operands: tuple[FormArgument, ...]`

- **function** `ufl.acos(f)`
  Take the inverse cosine of f.

- **function** `ufl.action(form, coefficient=None, derivatives_expanded=None)`
  Get the action.
  Given a bilinear form, return a linear form
  with an additional coefficient, representing the
  action of the form on the coefficient. This can be
  used for matrix-free methods.
  For formbase objects,coefficient can be any object of the correct type,
  and this function returns an Action object.
  When action is being called multiple times on the same form, expanding derivatives
  become expensive -> derivatives_expanded enables to use caching mechanisms to avoid that.

- **function** `ufl.adjoint(form, reordered_arguments=None, derivatives_expanded=None)`
  Get the adjoint.
  Given a combined bilinear form, compute the adjoint form by
  changing the ordering (count) of the test and trial functions, and
  taking the complex conjugate of the result.
  By default, new Argument objects will be created with
  opposite ordering. However, if the adjoint form is to
  be added to other forms later, their arguments must match.
  In that case, the user must provide a tuple *reordered_arguments*=(u2,v2).
  If the form is a baseform instance instead of a Form object, we return an Adjoint
  object instructing the adjoint to be computed at a later point.
  When adjoint is being called multiple times on the same form, expanding derivatives
  become expensive -> derivatives_expanded enables to use caching mechanisms to avoid that.

- **function** `ufl.as_cell(cell: AbstractCell | str | tuple[AbstractCell, ...]) → AbstractCell`
  Convert any valid object to a Cell or return cell if it is already a Cell.
  Allows an already valid cell, a known cellname string, or a tuple of cells for a product cell.

- **function** `ufl.as_matrix(expressions, indices=None)`
  As as_tensor(), but limited to rank 2 tensors.

- **function** `ufl.as_tensor(expressions, indices=None)`
  Make a tensor valued expression.
  This works in two different ways, by using indices or lists.
  1) Returns A such that A [indices] = expressions.
  If indices are provided, expressions must be a scalar
  valued expression with all the provided indices among
  its free indices. This operator will then map each of these
  indices to a tensor axis, thereby making a tensor valued
  expression from a scalar valued expression with free indices.
  2) Returns A such that A[k,...] = expressions*[k].
  If no indices are provided, *expressions must be a list
  or tuple of expressions. The expressions can also consist
  of recursively nested lists to build higher rank tensors.

- **function** `ufl.as_ufl(expression)`
  Converts expression to an Expr if possible.

- **function** `ufl.as_vector(expressions, index=None)`
  As as_tensor(), but limited to rank 1 tensors.

- **function** `ufl.asin(f)`
  Take the inverse sine of f.

- **function** `ufl.atan(f)`
  Take the inverse tangent of f.

- **function** `ufl.atan2(f1, f2)`
  Take the inverse tangent with two the arguments f1 and f2.

- **function** `ufl.avg(v)`
  Take the average of v across a facet.

- **function** `ufl.bessel_I(nu, f)`
  Regular modified cylindrical Bessel function.

- **function** `ufl.bessel_J(nu, f)`
  Cylindrical Bessel function of the first kind.

- **function** `ufl.bessel_K(nu, f)`
  Irregular modified cylindrical Bessel function.

- **function** `ufl.bessel_Y(nu, f)`
  Cylindrical Bessel function of the second kind.

- **function** `ufl.cell_avg(f)`
  Take the average of v over a cell.

- **function** `ufl.cofac(A)`
  Take the cofactor of A.

- **function** `ufl.conditional(condition, true_value, false_value)`
  A conditional expression.
  This takes the value of true_value
  when condition evaluates to true and false_value otherwise.

- **function** `ufl.conj(f)`
  The complex conjugate of f.

- **function** `ufl.cos(f)`
  Take the cosine of f.

- **function** `ufl.cosh(f)`
  Take the hyperbolic cosine of f.

- **function** `ufl.cross(a, b)`
  Take the cross product of a and b.

- **function** `ufl.curl(f)`
  Take the curl of f.

- **function** `ufl.derivative(form, coefficient, argument=None, coefficient_derivatives=None)`
  Compute the Gateaux derivative of form w.r.t. coefficient in direction of argument.
  If the argument is omitted, a new Argument is created
  in the same space as the coefficient, with argument number
  one higher than the highest one in the form.
  The resulting form has one additional Argument
  in the same finite element space as the coefficient.
  A tuple of Coefficient s may be provided in place of
  a single Coefficient, in which case the new Argument
  argument is based on a MixedElement created from this tuple.
  An indexed Coefficient from a mixed space may be provided,
  in which case the argument should be in the corresponding
  subspace of the coefficient space.
  If provided, coefficient_derivatives should be a mapping from
  Coefficient instances to their derivatives w.r.t. coefficient.

- **function** `ufl.det(A)`
  Take the determinant of A.

- **function** `ufl.dev(A)`
  Take the deviatoric part of A.

- **function** `ufl.diag(A)`
  Diagonal ranl-2 tensor.
  Take the diagonal part of rank 2 tensor A or make a diagonal rank 2
  tensor from a rank 1 tensor.
  Always returns a rank 2 tensor. See also diag_vector.

- **function** `ufl.diag_vector(A)`
  Take the diagonal part of rank 2 tensor A and return as a vector.
  See also diag.

- **function** `ufl.diff(f, v)`
  Take the derivative of f with respect to the variable v.
  If f is a form, diff is applied to each integrand.

- **function** `ufl.div(f)`
  Take the divergence of f.

Take the divergence of f.

- `This operator follows the div convention where`
  div(v) = v[i].dx(i)
  div(T)[:] = T[:,i].dx(i)

for vector expressions v, and
arbitrary rank tensor expressions T.

See also: nabla_div()

- **function** `ufl.dot(a, b)`
  Take the dot product of a and b.
  This won’t take the complex conjugate of the second argument.

- **function** `ufl.elem_div(A, B)`
  Take the elementwise division of tensors A and B with the same shape.

- **function** `ufl.elem_mult(A, B)`
  Take the elementwise multiplication of tensors A and B with the same shape.

- **function** `ufl.elem_op(op, *args)`
  Apply element-wise operations.
  Take the element-wise application of operator op on scalar values
  from one or more tensor arguments.

- **function** `ufl.elem_pow(A, B)`
  Take the elementwise power of tensors A and B with the same shape.

- **function** `ufl.energy_norm(form, coefficient=None)`
  Get the energy norm.
  Given a bilinear form a and a coefficient f,
  return the functional a(f,f).

- **function** `ufl.eq(left, right)`
  A boolean expression (left == right) for use with conditional.

- **function** `ufl.erf(f)`
  Take the error function of f.

- **function** `ufl.exp(f)`
  Take the exponential of f.

- **function** `ufl.exterior_derivative(f)`
  Take the exterior derivative of f.
  The exterior derivative uses the element Sobolev space to
  determine whether id, grad, curl or div should be used.
  Note that this uses the grad and div operators,
  as opposed to nabla_grad and nabla_div.

- **function** `ufl.extract_blocks(form: Form, i: int | None = None, j: int | None = None, replace_argument: bool = True)`
  Extract blocks.
  Given a linear or bilinear form on a mixed space,
  extract the block corresponding to the indices ix, iy.

Extract blocks.

Given a linear or bilinear form on a mixed space,
extract the block corresponding to the indices ix, iy.

- `Example:`
  a = inner(grad(u), grad(v))*dx + div(u)*q*dx + div(v)*p*dx
  extract_blocks(a, 0, 0) -> inner(grad(u), grad(v))*dx
  extract_blocks(a) -> [inner(grad(u), grad(v))*dx, div(v)*p*dx, div(u)*q*dx, 0]

- **function** `ufl.facet_avg(f)`
  Take the average of v over a facet.

- **function** `ufl.functional(form)`
  Extract the functional part of form.

- **function** `ufl.ge(left, right)`
  A boolean expression (left >= right) for use with conditional.

- **function** `ufl.grad(f)`
  Take the gradient of f.

Take the gradient of f.

- `This operator follows the grad convention where`
  grad(s)[i] = s.dx(i)
  grad(v)[i,j] = v[i].dx(j)
  grad(T)[:,i] = T[:].dx(i)

for scalar expressions s, vector expressions v,
and arbitrary rank tensor expressions T.

See also: nabla_grad()

- **function** `ufl.gt(left, right)`
  A boolean expression (left > right) for use with conditional.

- **function** `ufl.imag(f)`
  The imaginary part of f.

- **function** `ufl.indices(n)`
  Return a tuple of n new Index objects.

- **function** `ufl.inner(a, b)`
  Take the inner product of a and b.
  The complex conjugate of the second argument is taken.

- **function** `ufl.integral_types()`
  Return a tuple of all domain type strings.

- **function** `ufl.interpolate(expr, v)`
  Create symbolic representation of the interpolation operator.

Create symbolic representation of the interpolation operator.

- `Args:`

- `expr:`
  a UFL expression to interpolate.

- `v:`
  the FunctionSpace to interpolate into or the Coargument
  defined on the dual of the FunctionSpace to interpolate into.

- **function** `ufl.inv(A)`
  Take the inverse of A.

- **function** `ufl.jump(v, n=None)`
  Take the jump of v across a facet.

- **function** `ufl.le(left, right)`
  A boolean expression (left <= right) for use with conditional.

- **function** `ufl.lhs(form)`
  Get the left hand side.
  Given a combined bilinear and linear form,
  extract the left hand side (bilinear form part).

Get the left hand side.

Given a combined bilinear and linear form,
extract the left hand side (bilinear form part).

- `Example:`
  a = u*v*dx + f*v*dx
  a = lhs(a) -> u*v*dx

- **function** `ufl.ln(f)`
  Take the natural logarithm of f.

- **function** `ufl.lt(left, right)`
  A boolean expression (left < right) for use with conditional.

- **function** `ufl.max_value(x, y)`
  Take the maximum of x and y.

- **function** `ufl.min_value(x, y)`
  Take the minimum of x and y.

- **function** `ufl.nabla_div(f)`
  Take the divergence of f.

Take the divergence of f.

- `This operator follows the div convention where`
  nabla_div(v) = v[i].dx(i)
  nabla_div(T)[:] = T[i,:].dx(i)

for vector expressions v, and
arbitrary rank tensor expressions T.

See also: div()

- **function** `ufl.nabla_grad(f)`
  Take the gradient of f.

Take the gradient of f.

- `This operator follows the grad convention where`
  nabla_grad(s)[i] = s.dx(i)
  nabla_grad(v)[i,j] = v[j].dx(i)
  nabla_grad(T)[i,:] = T[:].dx(i)

for scalar expressions s, vector expressions v,
and arbitrary rank tensor expressions T.

See also: grad()

- **function** `ufl.ne(left, right)`
  A boolean expression (left != right) for use with conditional.

- **function** `ufl.outer(*operands)`
  Take the outer product of two or more operands.
  The complex conjugate of the first argument is taken.

- **function** `ufl.perp(v)`
  Take the perp of v.
  I.e. (−v1,+v0).

- **function** `ufl.product(sequence)`
  Return the product of all elements in a sequence.

- **function** `ufl.rank(f)`
  The rank of f.

- **function** `ufl.real(f)`
  The real part of f.

- **function** `ufl.register_integral_type(integral_type, measure_name)`
  Register an integral type.

- **function** `ufl.replace(e, mapping)`
  Replace subexpressions in expression.

Replace subexpressions in expression.

- `Params:`
  e: An Expr or Form
  mapping: A dict with from:to replacements to perform

- `Returns:`
  The expression with replacements performed

- **function** `ufl.rhs(form)`
  Get the right hand side.
  Given a combined bilinear and linear form,
  extract the right hand side (negated linear form part).

Get the right hand side.

Given a combined bilinear and linear form,
extract the right hand side (negated linear form part).

- `Example:`
  a = u*v*dx + f*v*dx
  L = rhs(a) -> -f*v*dx

- **function** `ufl.rot(f)`
  Take the curl of f.

- **function** `ufl.sensitivity_rhs(a, u, L, v)`
  Compute the right hand side for a sensitivity calculation system.
  The derivation behind this computation is as follows.
  Assume a, L to be bilinear and linear forms
  corresponding to the assembled linear system
  Where x is the vector of the discrete function corresponding to u.
  Let v be some scalar variable this equation depends on.
  Then we can write
  and solve this system for fracdxdv, using the same bilinear
  form a and matrix A from the original system.
  Assume the forms are written
  where IL and Ia are integrand expressions.
  Define a Coefficient u representing the solution
  to the equations. Then we can compute fracdbdv
  and fracdAdv from the forms
  and the action of da on u by
  In total, we can build the right hand side of the system
  to compute fracdudv with the single line
  or, using this function,

- **function** `ufl.shape(f)`
  The shape of f.

- **function** `ufl.sign(x)`
  Return the sign of x.
  This returns +1 if x is positive, -1 if x is negative, and 0 if x is 0.

- **function** `ufl.sin(f)`
  Take the sine of f.

- **function** `ufl.sinh(f)`
  Take the hyperbolic sine of f.

- **function** `ufl.skew(A)`
  Take the skew symmetric part of A.

- **function** `ufl.split(v)`
  Split a coefficient or argument.
  If v is a Coefficient or Argument in a mixed space, returns a tuple
  with the function components corresponding to the subelements.

- **function** `ufl.sqrt(f)`
  Take the square root of f.

- **function** `ufl.sym(A)`
  Take the symmetric part of A.

- **function** `ufl.system(form)`
  Split a form into the left hand side and right hand side.
  See lhs and rhs.

- **function** `ufl.tan(f)`
  Take the tangent of f.

- **function** `ufl.tanh(f)`
  Take the hyperbolic tangent of f.

- **function** `ufl.tr(A)`
  Take the trace of A.

- **function** `ufl.transpose(A)`
  Take the transposed of tensor A.

- **function** `ufl.unit_matrices(d)`
  A tuple of constant unit matrices in all directions with dimension d.

- **function** `ufl.unit_matrix(i, j, d)`
  A constant unit matrix in direction i,*j* with dimension d.

- **function** `ufl.unit_vector(i, d)`
  A constant unit vector in direction i with dimension d.

- **function** `ufl.unit_vectors(d)`
  A tuple of constant unit vectors in all directions with dimension d.

- **function** `ufl.variable(e)`
  Define a variable representing the given expression.
  See also diff().

- **function** `ufl.zero(*shape)`
  UFL literal constant: Return a zero tensor with the given shape.