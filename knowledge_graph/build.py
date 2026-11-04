"""Build normalized declarations directly from immutable API Markdown/tutorials."""

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .documents import parse_document
from .tutorials import Analyzer
from .identity import Resolver, prose_key, stable, unique_paragraphs


ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
API_KINDS = {"function", "class", "method", "property", "field", "alias"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def merge_records(records, resolver):
    """Intermediate parser records are not persisted as a second authoritative graph."""
    merged = {}
    for original in records:
        record = resolver.record(original)
        node = record["node"]
        identifier = node["id"]
        if node["kind"] == "alias" and identifier != original["node"]["id"]:
            # The alias's target contract is declared in its own record. Never
            # replace a class/function contract with an alias's description.
            continue
        if identifier not in merged:
            merged[identifier] = deepcopy(node)
            merged[identifier]["sources"] = [node["source"]]
            merged[identifier]["signatures"] = []
        target = merged[identifier]
        if target["kind"] != node["kind"] and node["kind"] != "alias":
            raise ValueError("Conflicting declared kinds for " + identifier)
        if node["source"] not in target["sources"]:
            target["sources"].append(node["source"])
        for signature in node.get("signatures", []):
            data = {k: v for k, v in signature.items() if k != "source"}
            if not any({k: v for k, v in s.items() if k != "source"} == data
                       for s in target["signatures"]):
                target["signatures"].append(deepcopy(signature))
        for field in ("description", "notes", "raises"):
            text = "\n\n".join(filter(None, [target.get(field, ""), node.get(field, "")]))
            if text:
                target[field] = unique_paragraphs(text)
        for base in record["bases"]:
            name = resolver.name(base["target"] or base["name"], record["module"], record["anchors"])
            if name not in resolver.nodes:
                target.setdefault("external_bases", [])
                if name not in target["external_bases"]:
                    target["external_bases"].append(name)
    return merged


class Graph:
    def __init__(self):
        self.nodes, self.edges = {}, {}
        self.ports = defaultdict(list)
        self.issues = []

    def edge(self, kind, src, dst, **attributes):
        relation = {"kind": kind, "src": src, "dst": dst, **attributes}
        body = {k: v for k, v in relation.items() if k not in ("evidence", "variants")}
        key = stable(body)
        if key not in self.edges:
            self.edges[key] = relation
        else:
            for field in ("variants", "evidence"):
                if field in relation:
                    current = self.edges[key].setdefault(field, [])
                    for item in relation[field]:
                        if item not in current:
                            current.append(item)
        return self.edges[key]

    def port(self, api, kind, specification, sources, *, variant=None):
        data = deepcopy(specification)
        data.pop("documentation_source", None)
        data.pop("source", None)
        if kind == "argument" and "kind" in data:
            data["parameter_kind"] = data.pop("kind")
        identifier = api + "::" + kind + ":" + hashlib.sha256(stable(data).encode()).hexdigest()[:16]
        if identifier not in self.nodes:
            self.nodes[identifier] = {"id": identifier, "kind": kind, **data, "sources": []}
        for source in sources:
            if source not in self.nodes[identifier]["sources"]:
                self.nodes[identifier]["sources"].append(source)
        relation = "HAS_ARGUMENT" if kind == "argument" else "HAS_RETURN"
        edge = self.edge(relation, api, identifier, **({"variants": [variant]} if variant is not None else {}))
        if identifier not in self.ports[api]:
            self.ports[api].append(identifier)
        return identifier, edge


def declaration_graph(apis, records, resolver):
    graph = Graph()
    for identifier, node in apis.items():
        kept = {key: deepcopy(node[key]) for key in (
            "id", "kind", "description", "notes", "raises", "value", "declaration_completeness", "sources")
                if key in node}
        if "value_type" in node:
            kept["type"] = deepcopy(node["value_type"])
        graph.nodes[identifier] = kept
        if node["kind"] == "alias":
            graph.issues.append({"category": "unresolved_alias_declaration", "api": identifier,
                                 "description": node.get("description", "")})
        for index, signature in enumerate(node.get("signatures", [])):
            variant = index if len(node["signatures"]) > 1 else None
            for parameter in signature["parameters"]:
                sources = [signature["source"]]
                if parameter.get("documentation_source"):
                    sources.append(parameter["documentation_source"])
                graph.port(identifier, "argument", parameter, sources, variant=variant)
            if signature.get("returns"):
                graph.port(identifier, "return", signature["returns"], [signature["source"]], variant=variant)
            if signature.get("receiver"):
                kept["receiver_name"] = signature["receiver"]
        for name, p in node.get("additional_parameter_docs", {}).items():
            graph.port(identifier, "argument", {"name": name,
                       **{k: v for k, v in p.items() if k != "source"},
                       "declaration": "documentation_only"}, [p["source"]])
        if node.get("unmatched_parameter_notes"):
            graph.issues.append({"category": "unmatched_parameter_documentation", "api": identifier,
                                 "notes": deepcopy(node["unmatched_parameter_notes"])})
        for field in ("examples", "other_sections"):
            if node.get(field):
                graph.issues.append({"category": "auxiliary_document_context", "api": identifier,
                                     field: node[field]})

    for record in records:
        node, owner = record["node"], record["owner"]
        identifier = resolver.canonical_api(node["id"])
        owner = resolver.canonical_api(owner) if owner else None
        if owner in graph.nodes:
            graph.edge("HAS_MEMBER", owner, identifier)
        for base in record["bases"]:
            name = resolver.name(base["target"] or base["name"], record["module"], record["anchors"])
            if name in graph.nodes:
                graph.edge("INHERITS", identifier, name, evidence=[base["source"]])
            else:
                graph.issues.append({"category": "external_base", "api": identifier,
                                     "name": name, "source": base["source"]})
    return graph


def port_candidates(graph, api, kind, variants=None):
    result = []
    for edge in graph.edges.values():
        if edge["src"] == api and edge["kind"] == kind:
            if variants and edge.get("variants") and not set(edge["variants"]) & set(variants):
                continue
            result.append(edge["dst"])
    return result


def add_usage(graph, apis, analyzer, resolver):
    calls = {call["id"]: call for call in analyzer.calls}
    unresolved = []
    for flow in analyzer.flows:
        source = resolver.canonical_api(flow["src"])
        target = resolver.canonical_api(flow["dst"])
        proof = flow["evidence"]
        producer, consumer = calls[proof["producer_call"]], calls[proof["consumer_call"]]
        if apis[source]["kind"] in ("class", "property", "field"):
            origin = source
        else:
            returns = port_candidates(graph, source, "HAS_RETURN", producer.get("signature_indices"))
            if not returns:
                # An observed produced value does not invent an undocumented return type.
                origin, _ = graph.port(source, "return", {"declaration": "not_documented"},
                                       [producer["source"]])
            elif len(returns) == 1:
                origin = returns[0]
            else:
                unresolved.append({"category": "ambiguous_return_contract", **flow})
                continue
        attributes = {"role": flow["role"], "evidence": [proof]}
        if flow["source_return_path"]:
            attributes["source_path"] = flow["source_return_path"]
        if flow["argument_path"]:
            attributes["target_path"] = flow["argument_path"]
        if flow["role"] == "receiver":
            destination = target
        else:
            supplied = flow["target"]
            candidates = port_candidates(graph, target, "HAS_ARGUMENT", consumer.get("signature_indices"))
            if "parameter" in supplied:
                candidates = [p for p in candidates if graph.nodes[p].get("name") == supplied["parameter"]]
            elif "position" in supplied:
                candidates = [p for p in candidates if graph.nodes[p].get("position") == supplied["position"]]
            else:
                candidates = []
            if len(candidates) != 1:
                unresolved.append({"category": "argument_port_unresolved", **flow})
                continue
            destination = candidates[0]
        graph.edge("FEEDS", origin, destination, **attributes)
    return unresolved


def validate(graph):
    errors = []
    edges = list(graph.edges.values())
    for edge in edges:
        if edge["src"] not in graph.nodes or edge["dst"] not in graph.nodes:
            errors.append({"category": "dangling_edge", "edge": edge})
        if edge["kind"] in ("HAS_ARGUMENT", "HAS_RETURN", "HAS_MEMBER"):
            forbidden = set(edge) - {"kind", "src", "dst", "variants"}
            if forbidden:
                errors.append({"category": "duplicated_declaration_on_edge", "edge": edge})
    meanings = defaultdict(list)
    owners = defaultdict(set)
    for edge in edges:
        if edge["kind"] in ("HAS_ARGUMENT", "HAS_RETURN"):
            owners[edge["dst"]].add(edge["src"])
    owner = {key: next(iter(values)) for key, values in owners.items()}
    for key, values in owners.items():
        if len(values) != 1:
            errors.append({"category": "multiple_port_owners", "port": key, "owners": sorted(values)})
    for node in graph.nodes.values():
        if node["kind"] in API_KINDS:
            bad = set(node) & {"args", "arguments", "parameters", "returns", "signatures", "members",
                               "methods", "properties", "bases", "owner", "value_type", "required"}
            if bad:
                errors.append({"category": "duplicate_inline_declaration", "api": node["id"], "fields": sorted(bad)})
        elif node["kind"] in ("argument", "return"):
            if node["id"] not in owner:
                errors.append({"category": "orphan_port", "port": node["id"]})
            body = {k: v for k, v in node.items() if k not in ("id", "sources")}
            meanings[owner.get(node["id"]), stable(body)].append(node["id"])
    for key, ids in meanings.items():
        if len(ids) > 1:
            errors.append({"category": "duplicate_semantic_port", "owner": key[0], "ids": ids})
    return errors


def build(documents=ROOT / "api_md", demos=ROOT / "demos", output=HERE / "assets"):
    documents, demos, output = map(Path, (documents, demos, output))
    inputs = [*sorted(documents.glob("*.md")), *sorted(demos.glob("*.ipynb"))]
    protected = inputs
    before = {str(p.resolve()): digest(p) for p in protected if p.is_file()}
    records, reports = [], []
    for path in sorted(documents.glob("*.md")):
        extracted, report = parse_document(path)
        records.extend(extracted)
        reports.append(report)
    resolver = Resolver(records)
    apis = merge_records(records, resolver)
    graph = declaration_graph(apis, records, resolver)
    inheritance = [e for e in graph.edges.values() if e["kind"] == "INHERITS"]
    analyzer = Analyzer(list(apis.values()), inheritance)
    for path in sorted(demos.glob("*.ipynb")):
        analyzer.notebook(path)
    unresolved = add_usage(graph, apis, analyzer, resolver)
    errors = validate(graph)
    errors.extend(x for report in reports for x in report["diagnostics"])
    if {name: digest(name) for name in before} != before:
        errors.append({"category": "protected_input_changed"})
    output.mkdir(parents=True, exist_ok=True)
    payload = {"schema": "api_declarations", "nodes": [graph.nodes[k] for k in sorted(graph.nodes)],
               "edges": sorted(graph.edges.values(), key=stable)}
    descriptions = defaultdict(list)
    for node in graph.nodes.values():
        if node["kind"] in API_KINDS and node.get("description"):
            descriptions[prose_key(node["description"])].append(node["id"])
    candidates = [{"description": key, "api_ids": ids, "action": "kept_distinct"}
                  for key, ids in sorted(descriptions.items()) if len(ids) > 1]
    report = {"passed": not errors, "node_count": len(graph.nodes), "edge_count": len(graph.edges),
              "node_kinds": dict(Counter(n["kind"] for n in graph.nodes.values())),
              "edge_kinds": dict(Counter(e["kind"] for e in graph.edges.values())),
              "searchable_api_declarations": sum(n["kind"] in ("function", "class", "method", "property", "field") for n in graph.nodes.values()),
              "tutorials": len(list(demos.glob("*.ipynb"))), "observed_calls": len(analyzer.calls),
              "observed_flows": len(analyzer.flows), "unresolved_flow_observations": len(unresolved),
              "protected_files_unchanged": not any(e["category"] == "protected_input_changed" for e in errors),
              "protected_file_count": len(before), "normalization_events": len(resolver.events),
              "document_reports": reports, "errors": errors}
    write_json(output / "api_graph.json", payload)
    write_json(output / "validation_report.json", report)
    write_json(output / "identity_report.json", {"api_aliases": resolver.aliases,
               "normalizations": resolver.events, "ambiguous_names": resolver.uncertainties,
               "same_description_distinct_apis": candidates,
               "policy": "Do not case-fold API identities, guess qualified aliases or merge similar descriptions."})
    write_json(output / "uncertainties.json", {"source_context": graph.issues,
               "unmapped_flows": unresolved, "code_analysis": analyzer.unresolved})
    write_json(output / "usage_evidence.json", {"calls": analyzer.calls})
    write_json(output / "manifest.json", {"schema": "api_declarations",
               "input_sha256": before, "llm_calls": 0, "embedding_calls": 0,
               "builder_sha256": {str(p.relative_to(ROOT)): digest(p)
                                  for p in sorted(HERE.glob("*.py"))},
               "scope": "Same six public API modules and their class members; original documents unchanged."})
    from .search import search_documents
    with (output / "search_documents.jsonl").open("w") as stream:
        for row in search_documents(payload):
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    if errors:
        raise ValueError("Graph validation failed: " + str(output / "validation_report.json"))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--documents", type=Path, default=ROOT / "api_md")
    parser.add_argument("--demos", type=Path, default=ROOT / "demos")
    parser.add_argument("--output", type=Path, default=HERE / "assets")
    options = parser.parse_args()
    result = build(options.documents, options.demos, options.output)
    print(json.dumps({k: result[k] for k in ("passed", "node_count", "edge_count", "node_kinds",
                     "edge_kinds", "searchable_api_declarations", "normalization_events", "unresolved_flow_observations")}))
