"""Compact, reversible coder views of the normalized API graph."""

from copy import deepcopy
import json

from knowledge_graph.signatures import type_expression
from .signatures import type_text


FORMAT = "normalized-api"
PORT_KINDS = {"argument", "return"}
REFERENCE = """API graph reference:
- nodes is grouped by node kind. id and edge endpoints are local references;
  api is the qualified library symbol used to derive imports and identify APIs.
  Access methods and properties through their owning objects.
- HAS_ARGUMENT and HAS_RETURN connect declarations to callables; HAS_MEMBER
  identifies class members. position and parameter_kind preserve argument order
  and positional/keyword conventions; variants groups alternative call contracts.
- edge_relations and edge_columns describe the edge rows. type_format and
  default_format describe type annotations and defaults. In particular, no
  default and a Python None default remain distinct.
- description and notes preserve documented semantics. FEEDS records observed
  value transfer, not all possible type-compatible calls.
"""


def id_map(fragment):
    """Audit sidecar only; long declaration IDs are not sent to the coder."""
    return {"n" + str(i): node["id"] for i, node in enumerate(fragment["nodes"])}


def compact_type(value):
    if not isinstance(value, dict):
        return deepcopy(value)
    try:
        text = type_text(value)
        if type_expression(text) == value:
            return text
    except (KeyError, TypeError, ValueError):
        pass
    return deepcopy(value)


def encode(fragment):
    """Preserve every node/edge field except the spelling of structural IDs."""
    if not isinstance(fragment.get("nodes"), list) or not isinstance(fragment.get("edges"), list):
        raise ValueError("Expected normalized node and edge lists")
    original = [n["id"] for n in fragment["nodes"]]
    if len(original) != len(set(original)):
        raise ValueError("Duplicate graph node IDs")
    mapping = {value: "n" + str(i) for i, value in enumerate(original)}
    groups = {}
    for source in fragment["nodes"]:
        node = deepcopy(source)
        kind = node.pop("kind")
        if "api" in node:
            raise ValueError("Canonical nodes must not contain an extra api identity")
        if kind not in PORT_KINDS:
            node["api"] = node["id"]
        node["id"] = mapping[node["id"]]
        if "type" in node:
            node["type"] = compact_type(node["type"])
        default = node.get("default")
        if default == {"state": "absent"}:
            node["default"] = None
        elif (isinstance(default, dict) and set(default) == {"state", "expression"}
              and default["state"] == "specified" and isinstance(default["expression"], str)):
            node["default"] = default["expression"]
        groups.setdefault(kind, []).append(node)
    relations = sorted({e["kind"] for e in fragment["edges"]})
    relation_ids = {value: i for i, value in enumerate(relations)}
    edges = []
    for edge in fragment["edges"]:
        if edge["src"] not in mapping or edge["dst"] not in mapping:
            raise ValueError("Dangling graph edge")
        attributes = {k: deepcopy(v) for k, v in edge.items() if k not in ("kind", "src", "dst")}
        row = [relation_ids[edge["kind"]], mapping[edge["src"]], mapping[edge["dst"]]]
        if attributes:
            row.append(attributes)
        edges.append(row)
    return {
        "format": FORMAT, "nodes": groups, "edge_relations": relations,
        "edge_columns": ["relation_index", "src", "dst", "optional_attributes"], "edges": edges,
        "type_format": "String: Python type annotation; object: preserved structured type.",
        "default_format": "null: no default; string: Python default expression (including None); missing: undocumented; object: preserved state.",
    }


def decode(payload, *, original_ids=None):
    """Decode declarations; optionally restore original IDs from an audit sidecar."""
    if payload.get("format") != FORMAT:
        raise ValueError("Unknown compact API graph format")
    ordered, ids = [], set()
    for kind, group in payload["nodes"].items():
        for source in group:
            node = deepcopy(source)
            local = node["id"]
            if local in ids:
                raise ValueError("Duplicate compact node ID")
            ids.add(local)
            node["kind"] = kind
            if isinstance(node.get("type"), str):
                node["type"] = type_expression(node["type"])
            if "default" in node:
                if node["default"] is None:
                    node["default"] = {"state": "absent"}
                elif isinstance(node["default"], str):
                    node["default"] = {"state": "specified", "expression": node["default"]}
            if original_ids is not None:
                node["id"] = original_ids[local]
                if kind not in PORT_KINDS:
                    if node.pop("api") != node["id"]:
                        raise ValueError("API identity and ID map disagree")
            ordered.append((int(local.removeprefix("n")), node))
    edges = []
    for row in payload["edges"]:
        if len(row) not in (3, 4) or row[1] not in ids or row[2] not in ids:
            raise ValueError("Invalid compact edge")
        if not 0 <= row[0] < len(payload["edge_relations"]):
            raise ValueError("Invalid relation index")
        attrs = deepcopy(row[3]) if len(row) == 4 else {}
        if set(attrs) & {"kind", "src", "dst"}:
            raise ValueError("An edge attribute overrides its endpoints")
        src, dst = row[1:3]
        if original_ids is not None:
            src, dst = original_ids[src], original_ids[dst]
        edges.append({"kind": payload["edge_relations"][row[0]], "src": src, "dst": dst, **attrs})
    return {"nodes": [node for _, node in sorted(ordered)], "edges": edges}


def dumps(fragment):
    return json.dumps(encode(fragment), ensure_ascii=False, separators=(",", ":"))
