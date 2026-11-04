"""Conservative, source-located data flow over official notebook code cells.

Only documented APIs become graph endpoints. Analysis observations are kept
separately so the API graph can aggregate evidence without adding call nodes.
Unknown dynamic receivers are reported, not guessed from a method name.
"""

import ast
from dataclasses import dataclass, replace
import json
from pathlib import Path
import re

from .signatures import type_at, type_names


@dataclass(frozen=True)
class Value:
    producer: str | None = None
    call: str | None = None
    return_path: tuple = ()
    type: object = None
    symbol: str | None = None
    receiver: object = None
    items: tuple | None = None
    literal: object = None
    literal_known: bool = False


UNKNOWN = Value()


def signature_candidates(node, call):
    candidates = []
    keywords = {k.arg for k in call.keywords if k.arg is not None}
    for i, signature in enumerate(node.get("signatures", [])):
        parameters = signature.get("parameters", [])
        names = {p["name"] for p in parameters}
        generic = any(p["kind"].startswith("var_") for p in parameters)
        extra = set(node.get("additional_parameter_docs", {}))
        positional = [p for p in parameters
                      if p["kind"] in ("positional_only", "positional_or_keyword")]
        if not generic and (not keywords <= names or len(call.args) > len(positional)):
            continue
        if not generic:
            supplied = {p["name"] for p in positional[:len(call.args)]} | keywords
            required = {p["name"] for p in parameters
                        if p["kind"] not in ("var_positional", "var_keyword")
                        and p["default"]["state"] == "absent"}
            if not required <= supplied:
                continue
        candidates.append((i, signature, positional, names | extra))
    return candidates


class Analyzer:
    def __init__(self, nodes, inheritance=()):
        self.nodes = {n["id"]: n for n in nodes}
        self.parents = {}
        for edge in inheritance:
            if edge["kind"] == "INHERITS":
                self.parents.setdefault(edge["src"], []).append(edge["dst"])
        self.calls, self.flows, self.unresolved = [], [], []
        self.file = ""
        self.cell = 0
        self.environment = {}

    def owner_types(self, value):
        if value.symbol in self.nodes and self.nodes[value.symbol]["kind"] == "class":
            return [value.symbol]
        return [name for name in type_names(value.type)
                if name in self.nodes and self.nodes[name]["kind"] == "class"]

    def member(self, value, name):
        pending = self.owner_types(value)
        seen, matches = set(), set()
        while pending:
            owner = pending.pop()
            if owner in seen:
                continue
            seen.add(owner)
            candidate = owner + "." + name
            if candidate in self.nodes:
                matches.add(candidate)
            else:
                pending.extend(self.parents.get(owner, []))
        return next(iter(matches)) if len(matches) == 1 else None

    def location(self, node):
        return {"file": self.file, "cell": self.cell, "line": node.lineno,
                "column": node.col_offset, "end_line": getattr(node, "end_lineno", node.lineno),
                "end_column": getattr(node, "end_col_offset", node.col_offset)}

    def project(self, value, index):
        if value.items is not None and isinstance(index, int):
            if -len(value.items) <= index < len(value.items):
                return value.items[index]
            return UNKNOWN
        projected = type_at(value.type, (index,))
        if projected is None and isinstance(index, int):
            for owner in self.owner_types(value):
                node = self.nodes[owner]
                if any(base.rsplit(".", 1)[-1] == "NamedTuple"
                       for base in node.get("external_bases", [])):
                    signatures = node.get("signatures", [])
                    if len(signatures) == 1:
                        p = [p for p in signatures[0]["parameters"] if p.get("position") == index]
                        field = self.nodes.get(owner + "." + p[0]["name"]) if p else None
                        if field:
                            projected = field.get("value_type")
        return replace(value, return_path=value.return_path + (index,),
                       type=projected, literal_known=False)

    def sources(self, value, path=()):
        if value.items is not None:
            for i, item in enumerate(value.items):
                yield from self.sources(item, path + (i,))
        elif value.producer:
            yield value, path

    def observe_flow(self, source, destination, role, target, argument_path=()):
        self.flows.append({"src": source.producer, "dst": destination["api"], "kind": "FEEDS",
                           "role": role, "source_return_path": list(source.return_path),
                           "target": target, "argument_path": list(argument_path),
                           "evidence": {"producer_call": source.call,
                                        "consumer_call": destination["id"]}})

    def literal(self, expression):
        try:
            value = ast.literal_eval(expression)
            if len(repr(value)) <= 1200:
                if isinstance(value, tuple):
                    return {"kind": "tuple", "items": [self.literal(ast.Constant(v))
                            if not isinstance(v, (tuple, list, dict)) else self.literal_value(v)
                            for v in value]}
                return self.literal_value(value)
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
            pass
        return None

    def literal_value(self, value):
        if isinstance(value, tuple):
            return {"kind": "tuple", "items": [self.literal_value(v) for v in value]}
        if isinstance(value, list):
            return {"kind": "list", "items": [self.literal_value(v) for v in value]}
        if isinstance(value, dict):
            return {"kind": "dict", "items": [
                [self.literal_value(k), self.literal_value(v)] for k, v in value.items()]}
        if value is Ellipsis:
            return {"kind": "ellipsis"}
        if isinstance(value, (str, int, float, bool)) or value is None:
            return {"kind": "literal", "value": value}
        return None

    def expression(self, node, env):
        if node is None:
            return UNKNOWN
        if isinstance(node, ast.Name):
            return env.get(node.id, UNKNOWN)
        if isinstance(node, ast.Constant):
            return Value(literal=node.value, literal_known=True)
        if isinstance(node, (ast.Tuple, ast.List)):
            return Value(items=tuple(self.expression(item, env) for item in node.elts))
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            scoped = dict(env)
            for generator in node.generators:
                self.expression(generator.iter, scoped)
                self.assign(generator.target, UNKNOWN, scoped)
                for condition in generator.ifs:
                    self.expression(condition, scoped)
            if isinstance(node, ast.DictComp):
                self.expression(node.key, scoped)
                self.expression(node.value, scoped)
            else:
                self.expression(node.elt, scoped)
            return UNKNOWN
        if isinstance(node, ast.NamedExpr):
            value = self.expression(node.value, env)
            self.assign(node.target, value, env)
            return value
        if isinstance(node, ast.Attribute):
            receiver = self.expression(node.value, env)
            if receiver.symbol:
                qualified = receiver.symbol + "." + node.attr
                return Value(symbol=qualified)
            api = self.member(receiver, node.attr)
            if api:
                if self.nodes[api]["kind"] in ("property", "field"):
                    record = self.new_call(api, node, operation="attribute_read")
                    for source, path in self.sources(receiver):
                        self.observe_flow(source, record, "receiver", None, path)
                    return Value(api, record["id"], type=self.nodes[api].get("value_type"))
                return Value(symbol=api, receiver=receiver)
            return UNKNOWN
        if isinstance(node, ast.Subscript):
            value = self.expression(node.value, env)
            if isinstance(node.slice, ast.Slice):
                try:
                    bounds = [ast.literal_eval(n) if n is not None else None
                              for n in [node.slice.lower, node.slice.upper, node.slice.step]]
                    if any(b is not None and not isinstance(b, int) for b in bounds):
                        return UNKNOWN
                    count = None
                    if value.items is not None:
                        count = len(value.items)
                    elif (value.type and value.type.get("kind") == "generic"
                          and value.type.get("base", "").rsplit(".", 1)[-1].lower() == "tuple"
                          and not any(t.get("kind") == "ellipsis"
                                      for t in value.type["arguments"])):
                        count = len(value.type["arguments"])
                    if count is not None:
                        indices = list(range(count))[slice(*bounds)]
                        return Value(items=tuple(self.project(value, i) for i in indices))
                except (ValueError, TypeError):
                    pass
                return UNKNOWN
            try:
                index = ast.literal_eval(node.slice)
                if isinstance(index, (int, str)):
                    return self.project(value, index)
            except (ValueError, TypeError):
                pass
            return UNKNOWN
        if isinstance(node, ast.Call):
            return self.call(node, env)
        if isinstance(node, ast.Lambda):
            scoped = dict(env)
            self.clear_arguments(node.args, scoped)
            self.expression(node.body, scoped)
            return UNKNOWN
        # Arithmetic/operator results are not mislabeled as unchanged API return values.
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                self.expression(child, env)
        return UNKNOWN

    def new_call(self, api, expression, operation="call"):
        location = self.location(expression)
        identifier = (self.file + ":" + str(self.cell) + ":"
                      + str(expression.lineno) + ":" + str(expression.col_offset) + ":"
                      + str(getattr(expression, "end_lineno", expression.lineno)) + ":"
                      + str(getattr(expression, "end_col_offset", expression.col_offset))
                      + ":" + operation)
        record = {"id": identifier, "api": api, "operation": operation,
                  "source": location, "arguments": []}
        self.calls.append(record)
        return record

    def call(self, node, env):
        function = self.expression(node.func, env)
        values = [self.expression(arg.value if isinstance(arg, ast.Starred) else arg, env)
                  for arg in node.args]
        keyword_values = [(kw, self.expression(kw.value, env)) for kw in node.keywords]
        api = function.symbol
        if api not in self.nodes:
            # An external/library or user-defined call is not resolved by basename guessing.
            if isinstance(node.func, ast.Attribute):
                if api:
                    root = api.split(".")[0]
                    known_root = any(key.startswith(root + ".") for key in self.nodes)
                    category = ("outside_documented_api" if known_root
                                else "external_library_call")
                else:
                    category = "unresolved_receiver"
                self.unresolved.append({"category": category,
                                        "expression": ast.unparse(node.func),
                                        "resolved_name": api,
                                        "source": self.location(node)})
            return UNKNOWN
        record = self.new_call(api, node)
        candidates = signature_candidates(self.nodes[api], node)
        record["signature_indices"] = [c[0] for c in candidates]
        if not candidates and self.nodes[api].get("signatures"):
            self.unresolved.append({"category": "signature_binding_unresolved", "api": api,
                                    "source": self.location(node)})
        if function.receiver is not None:
            receiver = function.receiver
            for source, path in self.sources(receiver):
                self.observe_flow(source, record, "receiver", None, path)
        for i, (expression, value) in enumerate(zip(node.args, values)):
            names = {positional[i]["name"] for _, _, positional, _ in candidates
                     if i < len(positional)}
            target = {"passing": "positional", "position": i}
            if len(names) == 1 and all(i < len(c[2]) for c in candidates):
                target["parameter"] = next(iter(names))
                del target["position"]  # The declaration already records this order.
            if isinstance(expression, ast.Starred):
                target["passing"] = "starred"
            self.argument(record, expression, value, target)
        for keyword, value in keyword_values:
            target = {"passing": "keyword" if keyword.arg else "unpacked_keywords"}
            if keyword.arg:
                target["parameter"] = keyword.arg
            self.argument(record, keyword.value, value, target)
        if self.nodes[api]["kind"] == "class":
            returned = {"kind": "name", "name": api}
        else:
            returns = [c[1].get("returns", {}).get("type") for c in candidates]
            returned = returns[0] if returns and all(r == returns[0] for r in returns) else None
        return Value(api, record["id"], type=returned)

    def argument(self, record, expression, value, target):
        observed = {"target": target}
        literal = self.literal(expression)
        if literal is not None:
            observed["literal"] = literal
        elif value.symbol in self.nodes:
            observed["api_reference"] = value.symbol
        record["arguments"].append(observed)
        for source, path in self.sources(value):
            self.observe_flow(source, record, "argument", target, path)

    @staticmethod
    def clear_arguments(arguments, env):
        for arg in [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs,
                    arguments.vararg, arguments.kwarg]:
            if arg is not None:
                env[arg.arg] = UNKNOWN

    def assign(self, target, value, env):
        if isinstance(target, ast.Name):
            env[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            for index, element in enumerate(target.elts):
                self.assign(element, self.project(value, index), env)
        elif isinstance(target, ast.Starred):
            self.assign(target.value, UNKNOWN, env)

    def statements(self, statements, env):
        for node in statements:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    env[name] = Value(symbol=alias.name if alias.asname else name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        env[alias.asname or alias.name] = Value(
                            symbol=(node.module + "." if node.module else "") + alias.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = self.expression(node.value, env)
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    self.assign(target, value, env)
            elif isinstance(node, ast.AugAssign):
                self.expression(node.value, env)
                self.assign(node.target, UNKNOWN, env)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scoped = dict(env)
                self.clear_arguments(node.args, scoped)
                self.statements(node.body, scoped)
                env[node.name] = UNKNOWN
            elif isinstance(node, ast.ClassDef):
                self.statements(node.body, dict(env))
                env[node.name] = UNKNOWN
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                self.expression(node.iter, env)
                scoped = dict(env)
                self.assign(node.target, UNKNOWN, scoped)
                self.statements(node.body, scoped)
                self.statements(node.orelse, dict(env))
                for key in set(env) | set(scoped):
                    if scoped.get(key) != env.get(key):
                        env[key] = UNKNOWN
            elif isinstance(node, ast.If):
                self.expression(node.test, env)
                first, second = dict(env), dict(env)
                self.statements(node.body, first)
                self.statements(node.orelse, second)
                for key in set(first) | set(second):
                    env[key] = first.get(key, UNKNOWN) if first.get(key) == second.get(key) else UNKNOWN
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    value = self.expression(item.context_expr, env)
                    if item.optional_vars:
                        self.assign(item.optional_vars, value, env)
                self.statements(node.body, env)
            elif isinstance(node, ast.Try):
                self.statements(node.body, dict(env))
                for handler in node.handlers:
                    self.statements(handler.body, dict(env))
                self.statements(node.orelse, dict(env))
                self.statements(node.finalbody, env)
            elif isinstance(node, ast.While):
                self.expression(node.test, env)
                self.statements(node.body, dict(env))
                self.statements(node.orelse, dict(env))
            else:
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.expr):
                        self.expression(child, env)

    def notebook(self, path):
        notebook = json.loads(Path(path).read_text(encoding="utf-8"))
        self.file = Path(path).name
        self.environment = {}
        tasks = []
        headings, narrative, markdown_cells = [], [], []
        for index, cell in enumerate(notebook.get("cells", [])):
            source = cell.get("source", "")
            source = "".join(source) if isinstance(source, list) else source
            if cell.get("cell_type") == "markdown":
                narrative.append(source)
                markdown_cells.append(index)
                for line in source.splitlines():
                    match = re.match(r"^(#{1,6})\s+(.+)$", line)
                    if match:
                        level, title = len(match[1]), match[2].strip()
                        headings = [h for h in headings if h["level"] < level]
                        headings.append({"level": level, "title": title, "cell": index})
                continue
            if cell.get("cell_type") != "code":
                continue
            self.cell = index
            start = len(self.calls)
            try:
                tree = ast.parse(source)
            except SyntaxError as error:
                self.unresolved.append({"category": "unparsed_code_cell", "file": self.file,
                                        "cell": index, "line": error.lineno,
                                        "message": error.msg})
                narrative, markdown_cells = [], []
                continue
            self.statements(tree.body, self.environment)
            calls = self.calls[start:]
            if calls:
                tasks.append({"id": self.file + ":cell:" + str(index),
                              "headings": [h["title"] for h in headings],
                              "description": "\n\n".join(narrative),
                              "markdown_cells": markdown_cells,
                              "code_source": {"file": self.file, "cell": index},
                              "call_ids": [c["id"] for c in calls]})
            narrative, markdown_cells = [], []
        return tasks
