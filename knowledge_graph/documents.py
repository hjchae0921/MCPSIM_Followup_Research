"""Extract source-located API records from the supplied Markdown conventions."""

from dataclasses import dataclass
from pathlib import Path
import re

from markdown_it import MarkdownIt

from .signatures import BT, clean_links, parse_signature, type_expression, unmark

CLASS = re.compile(r"^\*\*\*class\*([\w.]+)(?:\((.*)\))?\*\*\s*$")
FUNCTION = re.compile(r"^\*\*([\w.]+)\((.*?)\)\s*(?:→\s*(.*?))?\*\*\s*$")
ALIAS = re.compile(r"^\*\*([\w.]+)\*\*\s*$")
PROPERTY = re.compile(r"^\*\*\*property\*([A-Za-z_]\w*)(?:\*:\s*(.*?)\*)?\*\*\s*$")
FIELD = re.compile(r"^\*{2,3}([A-Za-z_]\w*)\*:\s*(.*?)\*{2,3}\s*$")
ENUM = re.compile(r"^\*{2,3}([A-Za-z_]\w*)\*=\s*(.*?)\*{2,3}\s*$")
PLAIN = re.compile(r"^##\s+([\w.]+)\((.*)\)\s*(?:→\s*(.+?))?\s*$")
SECTION = re.compile(
    r"^(?:#{1,6}\s*)?\*{0,2}"
    r"(Parameters|Arguments|Args|Returns|Return type|Raises|Notes?|Warnings?|Examples?|"
    r"References|See also)\*{0,2}(?::\*{0,2}\s*(.*))?$", re.I)
PARAM = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*)?([A-Za-z_]\w*(?:,\s*[A-Za-z_]\w*)*)"
    r"(?:\*\*)?\s*(?:\(([^)]*)\))?\s*[–—-]\s*(.*)$")
MODIFIERS = re.compile(r"^(?:(?:abstractmethod|abstract|staticmethod|classmethod|property|class)\s+)+")


@dataclass
class Header:
    line: int
    kind: str
    api: str
    arguments: str | None = None
    returns: str | None = None
    owner: str | None = None
    literal: bool = False
    value: str | None = None


def without_quote(line):
    return re.sub(r"^(?:>\s?)+", "", line)


def module_name(path, text):
    match = re.search(r"(?m)^#\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)", text)
    return match[1] if match else Path(path).stem


def _c_header(kind, signature, line, owner):
    signature = MODIFIERS.sub("", signature.strip())
    returns, arguments, value = None, None, None
    if "→" in signature:
        signature, returns = [s.strip() for s in signature.split("→", 1)]
    if "(" in signature:
        name, arguments = signature.split("(", 1)
        arguments = arguments.rsplit(")", 1)[0]
    elif "=" in signature:
        name, value = [s.strip() for s in signature.split("=", 1)]
    elif ":" in signature:
        name, returns = [s.strip() for s in signature.split(":", 1)]
    else:
        name = signature.strip()
    if kind in ("class", "exception", "function"):
        return Header(line, "class" if kind == "exception" else kind,
                      name.strip(), arguments, returns, literal=True)
    if owner:
        return Header(line, "field" if kind == "attribute" else kind,
                      owner + "." + name.strip(), arguments, returns,
                      owner, True, value)
    return None


def headers(text, module):
    """Recognize declarations only outside Markdown code blocks."""
    lines = text.splitlines()
    tokens = MarkdownIt().parse(text)
    protected = set()
    for token in tokens:
        if token.type in ("fence", "code_block") and token.map:
            protected.update(range(*token.map))
    c_bullet = re.compile(r"^- \*\*(class|function|method|property|attribute|exception)\*\* "
                          + re.escape(BT) + r"(.+?)" + re.escape(BT) + r"\s*$")
    form_c = any(c_bullet.match(line) for line in lines)
    result, owner = [], None
    for i, line in enumerate(lines):
        if i in protected:
            continue
        if form_c:
            if line.startswith("## "):
                owner = None
            match = c_bullet.match(line)
            if match:
                head = _c_header(match[1], match[2], i, owner)
                if match[1] in ("class", "exception", "function"):
                    owner = head.api if head.kind == "class" else None
                if head:
                    result.append(head)
            continue
        match = CLASS.match(line)
        if match:
            owner = match[1]
            result.append(Header(i, "class", owner, match[2]))
            continue
        match = FUNCTION.match(line)
        if match and match[1].startswith(module + "."):
            owner = None
            result.append(Header(i, "function", match[1], match[2], match[3]))
            continue
        match = PLAIN.match(line)
        if match and match[1].startswith(module + "."):
            owner = None
            result.append(Header(i, "function", match[1], match[2], match[3], literal=True))
            continue
        match = ALIAS.match(line)
        if match and match[1].startswith(module + "."):
            owner = None
            result.append(Header(i, "alias", match[1]))
            continue
        if not owner or not line.startswith(">"):
            continue
        content = without_quote(line)
        match = PROPERTY.match(content)
        if match:
            result.append(Header(i, "property", owner + "." + match[1],
                                 returns=match[2], owner=owner))
            continue
        match = FIELD.match(content)
        if match:
            result.append(Header(i, "field", owner + "." + match[1],
                                 returns=match[2], owner=owner))
            continue
        match = ENUM.match(content)
        if match:
            result.append(Header(i, "field", owner + "." + match[1],
                                 owner=owner, value=match[2]))
            continue
        match = FUNCTION.match(content)
        if match and "." not in match[1]:
            result.append(Header(i, "method", owner + "." + match[1],
                                 match[2], match[3], owner))
    return result


def _prose(lines):
    paragraphs, current = [], []
    for line in [*lines, ""]:
        if line.strip():
            current.append(line.strip())
        elif current:
            paragraph = " ".join(current)
            if paragraph not in paragraphs:
                paragraphs.append(paragraph)
            current = []
    # Sphinx's summary listing sometimes repeats the first paragraph verbatim.
    paragraphs = [p for i, p in enumerate(paragraphs)
                  if not any(i != j and q.startswith(p + " ") for j, q in enumerate(paragraphs))]
    return "\n\n".join(paragraphs)


def parse_body(lines, source, start_line=1):
    result = {"description": [], "notes": [], "parameter_docs": {},
              "returns_description": [], "return_type": [], "raises": [],
              "examples": [], "bases": [], "other_sections": {}}
    section, current_parameter, fence = "description", None, None
    example_start = None
    for offset, raw in enumerate(lines):
        text = without_quote(raw)
        line_number = start_line + offset
        if text.lstrip().startswith(BT * 3):
            if fence is None:
                fence = text.lstrip().split()[0]
                example_start = line_number
            else:
                result["examples"].append({"file": source, "line": example_start,
                                           "end_line": line_number})
                fence = None
            continue
        if fence:
            continue
        base = re.match(r"^\s*Bases:\s*(.+)$", text)
        if base:
            clean, anchors = clean_links(base[1])
            for item in clean.split(","):
                name = item.strip().strip(BT).strip()
                if name:
                    result["bases"].append({"name": name, "target": anchors.get(name),
                                            "source": {"file": source, "line": line_number}})
            continue
        clean, _ = clean_links(text)
        match = SECTION.match(clean.strip())
        if match:
            label = match[1].lower()
            current_parameter = None
            if label in ("parameters", "arguments", "args"):
                section = "parameter_docs"
            elif label == "returns":
                section = "returns_description"
            elif label == "return type":
                section = "return_type"
            elif label in ("note", "notes", "warning", "warnings"):
                section = "notes"
            elif label in ("example", "examples"):
                section = "examples"
                example_start = line_number
            elif label == "raises":
                section = "raises"
            else:
                section = label
                result["other_sections"].setdefault(label, [])
            clean = match[2] or ""
            if not clean:
                continue
        if section == "parameter_docs":
            match = PARAM.match(clean.strip())
            if match:
                names, stated_type, description = match.groups()
                current_parameter = []
                for name in re.split(r",\s*", names):
                    result["parameter_docs"][name] = {
                        "description": description,
                        "source": {"file": source, "line": line_number}}
                    if stated_type:
                        result["parameter_docs"][name]["type"] = type_expression(stated_type)
                    current_parameter.append(name)
            elif clean.strip() and current_parameter:
                for name in current_parameter:
                    result["parameter_docs"][name]["description"] += " " + clean.strip()
            continue
        if section == "examples":
            if clean.strip():
                result["examples"].append({"file": source, "line": line_number,
                                           "end_line": line_number, "text": clean.strip()})
            continue
        if section in result and isinstance(result[section], list):
            result[section].append(clean)
        else:
            result["other_sections"].setdefault(section, []).append(clean)
    for key in ["description", "notes", "returns_description", "return_type", "raises"]:
        result[key] = _prose(result[key])
    result["other_sections"] = {k: _prose(v) for k, v in result["other_sections"].items()
                                if _prose(v)}
    return result


def _in_scope(header, module):
    if header.owner:
        return header.owner.rsplit(".", 1)[0] == module
    return header.api.rsplit(".", 1)[0] == module


def parse_document(path, source_root=None):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    module = module_name(path, text)
    source = path.relative_to(source_root).as_posix() if source_root else path.name
    lines = text.splitlines()
    heads = headers(text, module)
    groups = []
    for head in heads:
        if (groups and groups[-1][-1].api == head.api
                and all(not line.strip() for line in lines[groups[-1][-1].line + 1:head.line])):
            groups[-1].append(head)
        else:
            groups.append([head])
    records, diagnostics, source_issues, scoped = [], [], [], 0
    for i, group in enumerate(groups):
        head = group[0]
        if not _in_scope(head, module):
            scoped += len(group)
            continue
        end = groups[i + 1][0].line if i + 1 < len(groups) else len(lines)
        for boundary in range(group[-1].line + 1, end):
            if re.fullmatch(r"##\s+(?:[\w.]+\s+module|Module contents)\s*", lines[boundary]):
                end = boundary
                break
        body = parse_body(lines[group[-1].line + 1:end], source, group[-1].line + 2)
        signatures = []
        for alternative in group:
            if alternative.arguments is None:
                continue
            try:
                signature = parse_signature(alternative.arguments, alternative.returns,
                                            literal=alternative.literal)
            except ValueError as error:
                diagnostics.append({"category": "signature_parse_error", "api": head.api,
                                    "file": source, "line": alternative.line + 1,
                                    "message": str(error)})
                signature = {"parameters": [], "unparsed_declaration": True}
            signature["source"] = {"file": source, "line": alternative.line + 1}
            for parameter in signature["parameters"]:
                name = parameter["name"]
                doc = body["parameter_docs"].get(name)
                if doc:
                    if doc["description"]:
                        parameter["description"] = doc["description"]
                    parameter["documentation_source"] = doc["source"]
                    if "type" not in parameter and "type" in doc:
                        parameter["type"] = doc["type"]
            if "returns" not in signature and body["return_type"]:
                signature["returns"] = {"type": type_expression(body["return_type"])}
            if body["returns_description"]:
                signature.setdefault("returns", {})["description"] = body["returns_description"]
            signatures.append(signature)
        if not signatures and body["parameter_docs"]:
            signatures.append({"parameters": [], "completeness": "partial",
                               "source": {"file": source, "line": head.line + 1}})
        node = {"id": head.api, "kind": head.kind,
                "source": {"file": source, "line": head.line + 1, "end_line": end}}
        declared_names = {p["name"] for s in signatures for p in s["parameters"]}
        additional = {name: doc for name, doc in body["parameter_docs"].items()
                      if name not in declared_names}
        if additional:
            variadic_wrapper = (any(p["kind"].startswith("var_") for s in signatures
                                    for p in s["parameters"])
                                and all(p["kind"].startswith("var_") for s in signatures
                                        for p in s["parameters"]))
            undeclared_header = head.arguments is None
            if variadic_wrapper or undeclared_header:
                node["additional_parameter_docs"] = additional
                node["declaration_completeness"] = "partial"
            else:
                node["unmatched_parameter_notes"] = additional
                source_issues.append({
                    "category": "parameter_doc_mismatch", "api": head.api,
                    "names": sorted(additional), "source": node["source"]})
        if body["description"]:
            node["description"] = body["description"]
        if signatures:
            node["signatures"] = signatures
        elif head.returns:
            node["value_type"] = type_expression(
                unmark(head.returns, head.literal, remove_links=False))
        if head.value is not None:
            node["value"] = unmark(head.value, head.literal)
        for name in ["notes", "raises", "examples", "other_sections"]:
            if body[name]:
                node[name] = body[name]
        if head.kind in ("function", "class", "alias"):
            package, name = head.api.rsplit(".", 1)
            node["import"] = "from " + package + " import " + name
        _, anchors = clean_links("\n".join(lines[head.line:end]))
        for alternative in group:
            _, declared = clean_links((alternative.arguments or "") + " "
                                      + (alternative.returns or ""))
            anchors.update(declared)
        records.append({"node": node, "owner": head.owner, "bases": body["bases"],
                        "anchors": anchors, "module": module,
                        "parameter_docs": list(body["parameter_docs"])})
    return records, {"module": module, "file": source, "declaration_headers": len(heads),
                     "outside_public_module_scope": scoped, "entries": len(records),
                     "diagnostics": diagnostics, "source_issues": source_issues}
