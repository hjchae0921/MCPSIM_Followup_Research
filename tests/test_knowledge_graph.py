"""Normalization, identity, port flows and bounded declaration expansion."""

import ast
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from knowledge_graph.documents import parse_document
from knowledge_graph.signatures import type_expression
from knowledge_graph.tutorials import Analyzer
from knowledge_graph.build import Graph, add_usage, build, declaration_graph, merge_records, validate
from knowledge_graph.identity import Resolver
from knowledge_graph.search import expand_one_hop as expand, search_documents


ROOT = Path(__file__).resolve().parents[1]


def records_from(text):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "example.md"
        path.write_text(text)
        records, report = parse_document(path)
    if report["diagnostics"]:
        raise ValueError(report["diagnostics"])
    return records


def make_graph(text):
    records = records_from(text)
    resolver = Resolver(records)
    apis = merge_records(records, resolver)
    return declaration_graph(apis, records, resolver), apis, resolver


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.records = records_from("# example\n\n***class*example.Space(*x: int*)**\n\n> A space.\n\n"
                                    "**example.space(*x: int*) → Space**\n\n> Construct a space.\n")
        self.resolver = Resolver(self.records)

    def test_short_and_qualified_type_share_identity(self):
        a = self.resolver.type(type_expression("Space"), "example")
        b = self.resolver.type(type_expression("example.Space"), "example")
        self.assertEqual(a, b)

    def test_function_and_class_are_not_case_folded(self):
        self.assertEqual(self.resolver.name("space", "example"), "example.space")
        self.assertEqual(self.resolver.name("Space", "example"), "example.Space")
        self.assertNotEqual(self.resolver.name("space", "example"), self.resolver.name("Space", "example"))

    def test_union_order_optional_and_typing_spelling(self):
        a = self.resolver.type(type_expression("typing.Optional[typing.List[int]]"), "example")
        b = self.resolver.type(type_expression("None | list[int] | list[int]"), "example")
        self.assertEqual(a, b)

    def test_sphinx_short_reference_marker_is_not_a_different_type(self):
        a = self.resolver.type(type_expression("~example.Space"), "example")
        b = self.resolver.type(type_expression("example.Space"), "example")
        self.assertEqual(a, b)
        self.assertTrue(any(e["rule"] == "sphinx_reference_marker" for e in self.resolver.events))

    def test_qualified_external_name_is_not_guessed_by_basename(self):
        self.assertEqual(self.resolver.name("external.Space", "example"), "external.Space")

    def test_explicit_alias_merges_into_target_without_duplicating_its_contract(self):
        records = deepcopy(self.records)
        alias = {"node": {"id": "example.Alias", "kind": "alias", "description": "alias of `Space`",
                          "source": {"file": "example.md", "line": 99}},
                 "module": "example", "anchors": {}, "owner": None, "bases": [], "parameter_docs": []}
        records.insert(0, alias)
        resolver = Resolver(records)
        apis = merge_records(records, resolver)
        self.assertEqual(resolver.canonical_api("example.Alias"), "example.Space")
        self.assertNotIn("example.Alias", apis)
        self.assertEqual(apis["example.Space"]["kind"], "class")
        self.assertNotIn("alias of", apis["example.Space"]["description"])

    def test_explicit_type_link_avoids_unrelated_same_short_name(self):
        expression = type_expression("[Space](https://docs.test/#outside.Space)")
        self.assertEqual(self.resolver.type(expression, "example")["name"], "outside.Space")

    def test_ambiguous_bare_type_remains_unresolved(self):
        records = deepcopy(self.records)
        other = deepcopy(records[0])
        other["node"]["id"] = "example.other.Space"
        records.append(other)
        resolver = Resolver(records)
        self.assertEqual(resolver.name("Space", "example.third"), "Space")
        self.assertEqual(len(resolver.uncertainties), 1)


class DeclarationTests(unittest.TestCase):
    def test_function_has_no_inline_parameters_or_returns(self):
        graph, _, _ = make_graph("# example\n\n**example.f(*x: int = 2*) → int**\n\n> Compute a value.\n")
        node = graph.nodes["example.f"]
        self.assertFalse(set(node) & {"parameters", "signatures", "returns", "args"})
        argument = next(n for n in graph.nodes.values() if n["kind"] == "argument")
        self.assertEqual(argument["position"], 0)
        self.assertEqual(argument["type"], {"kind": "name", "name": "int"})
        for edge in graph.edges.values():
            self.assertFalse(set(edge) & {"position", "type", "default", "description"})
        self.assertEqual(validate(graph), [])

    def test_identical_argument_names_on_different_apis_are_distinct(self):
        graph, _, _ = make_graph("# example\n\n**example.f(*x: int*)**\n\n> First.\n\n"
                                 "**example.g(*x: int*)**\n\n> Second.\n")
        args = [n for n in graph.nodes.values() if n["kind"] == "argument"]
        self.assertEqual(len(args), 2)
        self.assertNotEqual(args[0]["id"], args[1]["id"])

    def test_overloads_share_unchanged_return_without_losing_variant_membership(self):
        graph, _, _ = make_graph("# example\n\n**example.f(*x: int*) → int**\n\n"
                                 "**example.f(*x: float*) → int**\n\n> Compute.\n")
        returns = [n for n in graph.nodes.values() if n["kind"] == "return"]
        self.assertEqual(len(returns), 1)
        edge = next(e for e in graph.edges.values() if e["kind"] == "HAS_RETURN")
        self.assertEqual(edge["variants"], [0, 1])
        self.assertEqual(len([n for n in graph.nodes.values() if n["kind"] == "argument"]), 2)

    def test_duplicate_records_do_not_duplicate_ports(self):
        records = records_from("# example\n\n**example.f(*x: int*) → int**\n\n> Compute.\n")
        resolver = Resolver(records)
        records += deepcopy(records)
        graph = declaration_graph(merge_records(records, resolver), records, resolver)
        self.assertEqual(len(graph.nodes), 3)
        self.assertEqual(len(graph.edges), 2)

    def test_real_function_constructor_body_inputs_remain_partial(self):
        records, _ = parse_document(ROOT / "api_md/dolfinx.fem.md")
        resolver = Resolver(records)
        graph = declaration_graph(merge_records(records, resolver), records, resolver)
        v = next(graph.nodes[key] for key in graph.ports["dolfinx.fem.Function"]
                 if graph.nodes[key].get("name") == "V")
        self.assertEqual(v["declaration"], "documentation_only")
        self.assertNotIn("position", v)
        self.assertNotIn("default", v)
        self.assertNotIn("additional_parameter_docs", graph.nodes["dolfinx.fem.Function"])

    def test_validator_rejects_inline_duplicates_and_edge_repetition(self):
        graph, _, _ = make_graph("# example\n\n**example.f(*x: int*)**\n\n> Compute.\n")
        graph.nodes["example.f"]["parameters"] = []
        next(iter(graph.edges.values()))["position"] = 0
        categories = {e["category"] for e in validate(graph)}
        self.assertIn("duplicate_inline_declaration", categories)
        self.assertIn("duplicated_declaration_on_edge", categories)


class RetrievalTests(unittest.TestCase):
    TEXT = ("# example\n\n***class*example.Space(*size: int*)**\n\n> A space.\n\n"
            "> **collapse(*flag: bool = False*) → int**\n\n> > Collapse subspaces.\n\n"
            "> ***property*mesh*: int***\n\n> > Attached mesh.\n\n"
            "**example.create(*x: int*) → Space**\n\n> Construct a space.\n\n"
            "**example.consume(*space: Space*) → int**\n\n> Consume it.\n")

    def setUp(self):
        self.graph, self.apis, self.resolver = make_graph(self.TEXT)

    def payload(self):
        return {"nodes": list(self.graph.nodes.values()), "edges": list(self.graph.edges.values())}

    def test_callable_and_member_declarations_are_separate_search_records(self):
        rows=search_documents(self.payload())
        self.assertEqual({r["id"] for r in rows},{"example.Space","example.create","example.consume","example.Space.collapse","example.Space.mesh"})
        owner=next(r["text"] for r in rows if r["id"]=="example.Space")
        member=next(r["text"] for r in rows if r["id"]=="example.Space.collapse")
        self.assertNotIn("Collapse subspaces",owner)
        self.assertIn("Collapse subspaces",member)

    def test_constructor_description_is_not_lost_after_first_paragraph(self):
        payload = self.payload()
        for node in payload['nodes']:
            if node['kind'] == 'class':
                node['description'] += '\n\nInitialize an instance on the chosen domain.'
        before = deepcopy(payload)
        text = next(r['text'] for r in search_documents(payload) if r['id'] == 'example.Space')
        self.assertIn('A space.', text)
        self.assertIn('Initialize an instance on the chosen domain.', text)
        self.assertEqual(payload, before)

    def test_real_function_initialization_paragraph_reaches_search_index(self):
        records, _ = parse_document(ROOT / 'api_md/dolfinx.fem.md')
        resolver = Resolver(records)
        graph = declaration_graph(merge_records(records, resolver), records, resolver)
        payload = {'nodes': list(graph.nodes.values()), 'edges': list(graph.edges.values())}
        row = next(r for r in search_documents(payload) if r['id'] == 'dolfinx.fem.Function')
        self.assertIn('Initialize a finite element Function.', row['text'])
        self.assertIn('a vector holding the degrees-of-freedom.', row['text'])

    def test_function_one_hop_does_not_follow_return_flow(self):
        a = next(k for k in self.graph.ports["example.create"] if self.graph.nodes[k]["kind"] == "return")
        b = next(k for k in self.graph.ports["example.consume"] if self.graph.nodes[k]["kind"] == "argument")
        self.graph.edge("FEEDS", a, b, role="argument")
        fragment = expand(self.payload(), {"example.create"})
        self.assertNotIn("example.consume", {n["id"] for n in fragment["nodes"]})
        self.assertNotIn(b, {n["id"] for n in fragment["nodes"]})

    def test_class_does_not_expand_methods_to_a_second_hop(self):
        fragment=expand(self.payload(),{"example.Space"})
        ids={n["id"] for n in fragment["nodes"]}
        self.assertTrue(set(self.graph.ports["example.Space"])<=ids)
        self.assertNotIn("example.Space.collapse",ids)
        self.assertNotIn("example.Space.mesh",ids)
        self.assertNotIn("example.create",ids)

    def test_both_seeds_keep_cross_flow_without_extra_growth(self):
        a = next(k for k in self.graph.ports["example.create"] if self.graph.nodes[k]["kind"] == "return")
        b = next(k for k in self.graph.ports["example.consume"] if self.graph.nodes[k]["kind"] == "argument")
        self.graph.edge("FEEDS", a, b, role="argument")
        fragment = expand(self.payload(), {"example.create", "example.consume"})
        self.assertTrue(any(e["kind"] == "FEEDS" for e in fragment["edges"]))

    def test_method_seed_keeps_its_owner_and_call_contract(self):
        fragment=expand(self.payload(),{"example.Space.collapse"})
        ids={n["id"] for n in fragment["nodes"]}
        self.assertIn("example.Space",ids)
        self.assertTrue(set(self.graph.ports["example.Space.collapse"])<=ids)
        self.assertNotIn("example.Space.mesh",ids)
        self.assertFalse(set(self.graph.ports["example.Space"])&ids)

    def test_tutorial_flows_connect_ports_once(self):
        a = Analyzer(list(self.apis.values()))
        a.file, a.cell = "test.ipynb", 0
        a.statements(ast.parse("from example import create, consume\nx = create(1)\ny = consume(x)\nz = consume(x)\n").body, {})
        unresolved = add_usage(self.graph, self.apis, a, self.resolver)
        self.assertEqual(unresolved, [])
        flows = [e for e in self.graph.edges.values() if e["kind"] == "FEEDS"]
        self.assertEqual(len(flows), 1)
        self.assertEqual(self.graph.nodes[flows[0]["src"]]["kind"], "return")
        self.assertEqual(self.graph.nodes[flows[0]["dst"]]["kind"], "argument")
        self.assertEqual(len(flows[0]["evidence"]), 2)

    def test_tutorial_import_aliases_do_not_create_new_api_nodes(self):
        a = Analyzer(list(self.apis.values()))
        a.file, a.cell = "test.ipynb", 0
        source = ("import example as ex\nfrom example import create as make, consume\n"
                  "x = make(1)\ny = ex.create(2)\nconsume(x)\nconsume(y)\n")
        a.statements(ast.parse(source).body, {})
        self.assertEqual([c["api"] for c in a.calls].count("example.create"), 2)
        self.assertEqual(add_usage(self.graph, self.apis, a, self.resolver), [])
        flows = [e for e in self.graph.edges.values() if e["kind"] == "FEEDS"]
        self.assertEqual(len(flows), 1)
        self.assertEqual(len(flows[0]["evidence"]), 2)
        self.assertFalse(any("make" in n or n.startswith("ex.") for n in self.graph.nodes))


class BuildTests(unittest.TestCase):
    def test_rebuild_is_deterministic_and_original_documents_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            docs, demos = base / "docs", base / "demos"
            docs.mkdir(); demos.mkdir()
            source = docs / "example.md"
            text = "# example\n\n**example.f(*x: int*) → int**\n\n> Compute.\n"
            source.write_text(text)
            first = build(docs, demos, base / "first")
            second = build(docs, demos, base / "second")
            self.assertTrue(first["passed"] and second["passed"])
            self.assertEqual(source.read_text(), text)
            self.assertEqual((base / "first/api_graph.json").read_bytes(),
                             (base / "second/api_graph.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
