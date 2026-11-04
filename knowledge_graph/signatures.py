"""Parse documented call contracts without importing the documented packages."""

import html
import re

BT = chr(96)
LINK = re.compile(r"\[([^\[\]]+)\]\(([^)]+)\)")


def clean_links(text):
    """Retain link labels and resolve explicit API anchors separately."""
    anchors = {}

    def replace(match):
        label, url = match.groups()
        if "#" in url:
            target = url.rsplit("#", 1)[1]
            if re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+", target):
                anchors[label.strip(BT)] = target
        return label

    previous = None
    while previous != text:
        previous, text = text, LINK.sub(replace, text)
    return html.unescape(text), anchors


def unmark(text, literal=False, remove_links=True):
    if remove_links:
        text, _ = clean_links(text)
    else:
        text = html.unescape(text)
    if not literal:
        text = text.replace("*, *", ", ")
        if text.startswith("*"):
            text = text[1:]
        if text.endswith("*"):
            text = text[:-1]
    return text.strip().strip(BT).strip()


def split_top(text, separator=","):
    """Split outside balanced containers and strings; reject malformed input."""
    result, buffer, stack = [], [], []
    quote = None
    escaped = False
    pairs = {")": "(", "]": "[", "}": "{"}
    for char in text:
        if quote:
            buffer.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char in "([{":
            stack.append(char)
        elif char in ")]}":
            if not stack or stack.pop() != pairs[char]:
                raise ValueError("Unbalanced delimiter in documented expression")
        if char == separator and not stack and not quote:
            result.append("".join(buffer).strip())
            buffer = []
        else:
            buffer.append(char)
    if stack or quote:
        raise ValueError("Unterminated container or string in documented expression")
    result.append("".join(buffer).strip())
    return result


def type_expression(text):
    """Preserve union/container structure; unfamiliar syntax remains explicit text."""
    if not text:
        return None
    text = unmark(text, literal=True, remove_links=False)

    def type_link(match):
        label, url = match.groups()
        target = url.rsplit("#", 1)[-1] if "#" in url else ""
        if re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+", target):
            return target
        return label

    previous = None
    while previous != text:
        previous, text = text, LINK.sub(type_link, text)
    try:
        parts = split_top(text, "|")
        if len(parts) > 1:
            return {"kind": "union", "options": [type_expression(p) for p in parts]}
        if text.startswith("[") and text.endswith("]"):
            return {"kind": "argument_list",
                    "items": [type_expression(p) for p in split_top(text[1:-1]) if p]}
        opening = text.find("[")
        if opening > 0 and text.endswith("]"):
            base = text[:opening].strip()
            if re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", base):
                return {"kind": "generic", "base": base,
                        "arguments": [type_expression(p)
                                      for p in split_top(text[opening + 1:-1]) if p]}
        if text == "...":
            return {"kind": "ellipsis"}
        if text == "None":
            return {"kind": "none"}
        if re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", text):
            return {"kind": "name", "name": text}
    except ValueError:
        pass
    return {"kind": "unparsed", "text": text}


def type_names(expression):
    """Yield names from a structured type expression, without flattening its storage."""
    if not expression:
        return
    if expression["kind"] == "name":
        yield expression["name"]
    elif expression["kind"] == "generic":
        yield expression["base"]
        for child in expression["arguments"]:
            yield from type_names(child)
    elif expression["kind"] in ("union", "argument_list"):
        for child in expression.get("options", expression.get("items", [])):
            yield from type_names(child)


def type_at(expression, path):
    """Project a documented tuple return; other projections remain unknown."""
    for index in path:
        if (not expression or expression.get("kind") != "generic"
                or expression.get("base", "").rsplit(".", 1)[-1].lower() != "tuple"):
            return None
        args = expression["arguments"]
        if len(args) == 2 and args[1].get("kind") == "ellipsis":
            expression = args[0]
        elif isinstance(index, int) and -len(args) <= index < len(args):
            expression = args[index]
        else:
            return None
    return expression


def parse_signature(raw, return_text=None, literal=False):
    parameters = []
    keyword_only = False
    position = 0
    receiver = None
    text = unmark(raw or "", literal=literal, remove_links=False)
    for token in split_top(text):
        if not token:
            continue
        if token == "/":
            for parameter in parameters:
                if parameter["kind"] == "positional_or_keyword":
                    parameter["kind"] = "positional_only"
            continue
        if token == "*":
            keyword_only = True
            continue
        parts = split_top(token, "=")
        left = parts[0]
        default = ({"state": "specified",
                    "expression": unmark("=".join(parts[1:]), literal=True)}
                   if len(parts) > 1 else {"state": "absent"})
        annotation = split_top(left, ":")
        name = annotation[0].strip()
        annotated_type = ":".join(annotation[1:]).strip() if len(annotation) > 1 else None
        if name in ("self", "cls"):
            receiver = name
            continue
        if name.startswith("**"):
            kind, name = "var_keyword", name[2:]
        elif name.startswith("*"):
            kind, name = "var_positional", name[1:]
            keyword_only = True
        else:
            kind = "keyword_only" if keyword_only else "positional_or_keyword"
        if not re.fullmatch(r"[A-Za-z_]\w*", name):
            raise ValueError("Unrecognized documented parameter: " + name)
        item = {"name": name, "kind": kind, "default": default}
        if kind in ("positional_only", "positional_or_keyword"):
            item["position"] = position
            position += 1
        if annotated_type:
            item["type"] = type_expression(annotated_type)
        parameters.append(item)
    result = {"parameters": parameters}
    if receiver:
        result["receiver"] = receiver
    if return_text:
        result["returns"] = {"type": type_expression(
            unmark(return_text, literal=literal, remove_links=False))}
    return result


def type_text(value):
    if not value:
        return "unknown"
    kind = value["kind"]
    if kind == "name":
        return value["name"]
    if kind == "none":
        return "None"
    if kind == "ellipsis":
        return "..."
    if kind == "unparsed":
        return value["text"]
    if kind == "union":
        return " | ".join(type_text(v) for v in value["options"])
    if kind == "generic":
        return value["base"] + "[" + ", ".join(type_text(v) for v in value["arguments"]) + "]"
    if kind == "argument_list":
        return "[" + ", ".join(type_text(v) for v in value["items"]) + "]"
    raise ValueError("Unknown structured type kind: " + kind)
