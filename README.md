# Follow up research of MCP SIM

## Files and folders

```text
web/                       Web server, conversation interface and mesh viewer
problem_selection_agent/   Physics selection, formulation and library lookup
functionspace_agent/       Unknown fields, internal states and finite element spaces
material_agent/            Material regions, parameter values and units
boundary_condition_agent/  Boundary/source selection, values and mesh inspection
solver_agent/              Installed PETSc capabilities and solver settings
common/                    Shared schemas, validation, units and model clients
codegen/                   Stage cards, code generation, execution and contours
coder/                     Model requests and generated-code execution
knowledge_graph/           API document parsing, graph construction and retrieval
  assets/                  Prepared API graph and embedding indexes
api_md/                    API reference documents used to build the graph
demos/                     Official tutorial notebooks used for data-flow analysis
library/                   Saved physics specifications and formulations
prompt_templates/          Five-stage coding prompts
benchmarks/                Six tagged geometries, mesh files and input requests
tests/                     Offline regression tests
scripts/                   Installation and benchmark validation
environment.yml            DOLFINx environment
requirements.txt           Python application dependencies
```

## Installation

```bash
git clone https://github.com/hjchae0921/MCPSIM_Followup_Research.git
cd MCPSIM_Followup_Research
conda env create -f environment.yml
conda activate mcpsim-followup
```

Set API credentials in the shell used to start the application:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

OpenAI is used for formulation generation and query embeddings. OpenRouter is
used when an OpenRouter model is selected. Local `.openai_key` and
`.openrouter_key` files are also supported and are excluded from Git.

## Run the application

```bash
python -B -m web.app --host 127.0.0.1 --port 7861
```

Open <http://localhost:7861/>. Load a benchmark `model.msh`, select its coordinate
length unit, and enter the corresponding `request.txt`. Review and confirm the
physics specification, formulation, function spaces, material parameters,
boundary/source conditions and solver settings. Then preview the five coding
cards and start code generation and execution. Select the model and reasoning
setting from the sidebar controls.

The coding stages are mesh, function space, weak form, boundary conditions and
solve. Retrieval uses the top three API declarations for each numbered Procedure
item and expands their immediate structural neighbors once. Generated sources,
retrieval records, execution logs and contour images are available in the run
panel. Runtime sessions and generated results are stored under `data/`.

## Benchmarks

All six supplied meshes use millimeters.

| Problem | Folder |
|---|---|
| Steady heat transfer | `benchmarks/01_heat_sink/` |
| Linear elasticity | `benchmarks/02_tensile_specimen/` |
| Thermoelasticity | `benchmarks/06_fixed_i_beam/` |
| Piezoelectricity | `benchmarks/08_piezoelectric_cantilever/` |
| Thermoelectricity | `benchmarks/07_teg/` |
| Hyperelasticity | `benchmarks/04_rubber_bellows/` |

Each folder contains `request.txt`, `model.msh`, `geometry.py`, `geometry.json`
and `geometry.brep`. The complete request list is in `benchmarks/prompts.txt`.

```bash
python scripts/validate_benchmarks.py
python benchmarks/01_heat_sink/geometry.py --help
```

## Validation and graph preparation

```bash
python scripts/check_installation.py
python -B -m unittest discover -s tests -t .
python -B -m knowledge_graph.index
```

The prepared graph and embeddings are included. To rebuild from the supplied
reference documents and tutorial notebooks, then create matching embeddings:

```bash
python -B -m knowledge_graph.build
python -B -m knowledge_graph.index --embed
```

The rebuild command parses local files. The `--embed` command sends embedding
requests using `OPENAI_API_KEY`.
