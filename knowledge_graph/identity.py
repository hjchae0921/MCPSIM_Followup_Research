"""Resolve documented identities conservatively; never merge APIs by similarity."""

from copy import deepcopy
import html
import json
import re
import unicodedata

from knowledge_graph.signatures import type_expression


def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def prose_key(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", html.unescape(value))).strip()


def unique_paragraphs(value):
    parts = {}
    for paragraph in value.split("\n\n"):
        if key := prose_key(paragraph):
            parts.setdefault(key, paragraph.strip())
    return "\n\n".join(parts.values())


TYPING_NAMES = {"typing.List": "list", "typing.Tuple": "tuple", "typing.Dict": "dict",
                "typing.Set": "set", "typing.FrozenSet": "frozenset",
                "typing.Type": "type", "typing.Callable": "collections.abc.Callable"}


class Resolver:
    def __init__(self, records):
        self.nodes = {r["node"]["id"]: r["node"] for r in records}
        self.aliases, self.events, self.uncertainties = {}, [], []
        # Only an explicit alias declaration can merge two qualified API identities.
        for record in records:
            node = record["node"]
            if node["kind"] != "alias":
                continue
            match = re.fullmatch(r"alias of\s+`?([\w.]+)`?", node.get("description", "").strip())
            if match:
                target = self.name(match[1], record["module"], record["anchors"], log=False)
                if target in self.nodes and target != node["id"]:
                    self.aliases[node["id"]] = target

    def canonical_api(self, name):
        seen = set()
        while name in self.aliases and name not in seen:
            seen.add(name)
            name = self.aliases[name]
        return name

    def name(self, spelling, module, anchors=None, *, log=True):
        original = spelling
        spelling = html.unescape(spelling).strip().strip("`").lstrip("~")
        anchors = anchors or {}
        if spelling in self.nodes:
            result, rule = self.canonical_api(spelling), "exact_documented_identity"
        elif spelling in TYPING_NAMES:
            result, rule = TYPING_NAMES[spelling], "python_typing_alias"
        elif "." not in spelling and module + "." + spelling in self.nodes:
            result, rule = self.canonical_api(module + "." + spelling), "same_module_identity"
        elif "." not in spelling and spelling in anchors:
            result, rule = self.canonical_api(anchors[spelling]), "explicit_document_link"
        elif "." not in spelling:
            candidates = [key for key, n in self.nodes.items()
                          if n["kind"] == "class" and key.split(".")[0] == module.split(".")[0]
                          and key.rsplit(".", 1)[-1] == spelling]
            if len(candidates) == 1:
                result, rule = self.canonical_api(candidates[0]), "unique_class_in_library"
            else:
                result, rule = spelling, "unchanged"
                if len(candidates) > 1 and log:
                    item = {"spelling": original, "module": module, "candidates": sorted(candidates)}
                    if item not in self.uncertainties:
                        self.uncertainties.append(item)
        else:
            result, rule = spelling, "unchanged"
        if log and result != original:
            event = {"spelling": original, "canonical": result, "context_module": module, "rule": rule}
            if event not in self.events:
                self.events.append(event)
        return result

    def type(self, expression, module, anchors=None):
        if expression is None:
            return None
        value = deepcopy(expression)
        kind = value["kind"]
        if kind == "unparsed":
            text = value["text"]
            cleaned = re.sub(r"(?<![\w.])~(?=[A-Za-z_]\w*\.)", "", text)
            if cleaned != text:
                parsed = type_expression(cleaned)
                if parsed and parsed["kind"] != "unparsed":
                    event = {"spelling": text, "canonical": cleaned, "context_module": module,
                             "rule": "sphinx_reference_marker"}
                    if event not in self.events:
                        self.events.append(event)
                    return self.type(parsed, module, anchors)
        elif kind == "name":
            value["name"] = self.name(value["name"], module, anchors)
        elif kind == "generic":
            base = value["base"].lstrip("~")
            children = [self.type(x, module, anchors) for x in value["arguments"]]
            if base in ("typing.Optional", "typing.Union"):
                if base == "typing.Optional":
                    children.append({"kind": "none"})
                value = {"kind": "union", "options": children}
            else:
                value = {"kind": "generic", "base": self.name(value["base"], module, anchors),
                         "arguments": children}
        elif kind == "union":
            value["options"] = [self.type(x, module, anchors) for x in value["options"]]
        elif kind == "argument_list":
            value["items"] = [self.type(x, module, anchors) for x in value["items"]]
        if value["kind"] == "union":
            options = []
            for child in value["options"]:
                options.extend(child["options"] if child["kind"] == "union" else [child])
            distinct = {stable(child): child for child in options}
            ordered = [distinct[key] for key in sorted(distinct)]
            value = ordered[0] if len(ordered) == 1 else {"kind": "union", "options": ordered}
        return value

    def record(self, record):
        result = deepcopy(record)
        node = result["node"]
        node["id"] = self.canonical_api(node["id"])
        module, anchors = record["module"], record["anchors"]
        for signature in node.get("signatures", []):
            for p in signature["parameters"]:
                if "type" in p:
                    p["type"] = self.type(p["type"], module, anchors)
            if "type" in signature.get("returns", {}):
                signature["returns"]["type"] = self.type(signature["returns"]["type"], module, anchors)
        if "value_type" in node:
            node["value_type"] = self.type(node["value_type"], module, anchors)
        for field in ("additional_parameter_docs", "unmatched_parameter_notes"):
            for p in node.get(field, {}).values():
                if "type" in p:
                    p["type"] = self.type(p["type"], module, anchors)
        if result["owner"]:
            result["owner"] = self.canonical_api(result["owner"])
        return result
