"""Mesh length conventions and numeric conversion of explicit length factors."""
import ast
from decimal import Decimal
import math
import re

_LENGTH_IN_METERS={'m':1.0,'mm':1e-3,'cm':1e-2,'um':1e-6,'µm':1e-6,'μm':1e-6}
_LENGTH_TOKEN=re.compile(r'(?<![A-Za-zµμΩ°_])(?:mm|cm|um|µm|μm|m)(?![A-Za-zµμΩ°_])')
_SUPER=re.compile(r'[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+')
_SUPER_TABLE=str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺','0123456789-+')
_TOKEN=re.compile(r'\*\*|[*/()+-]|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[A-Za-zµμΩ°_]+')
_NAME=re.compile(r'[A-Za-zµμΩ°_]+\Z')


def unit_context(summary):
    unit=summary.get('coordinate_unit') or None
    return {'length_unit':unit,'meters_per_length_unit':_LENGTH_IN_METERS.get(unit)}


def _factor(unit,target):
    expression=_SUPER.sub(lambda m:'**('+m[0].translate(_SUPER_TABLE)+')',unit)
    expression=expression.replace('^','**').replace('·','*').replace('⋅','*').replace('×','*')
    expression=re.sub(r'(?<![A-Za-z0-9_.])([A-Za-zµμΩ°_]+)(-?\d+)\b',r'\1**(\2)',expression)
    tokens=_TOKEN.findall(expression)
    if ''.join(tokens)!=re.sub(r'\s+','',expression):raise ValueError('Unsupported unit notation')
    joined=[]
    for i,token in enumerate(tokens):
        if i:
            prev=tokens[i-1]
            if (prev==')' or _NAME.fullmatch(prev) or prev[0].isdigit()) and (token=='(' or _NAME.fullmatch(token) or token[0].isdigit()):joined.append('*')
        joined.append(token)
    tree=ast.parse(''.join(joined),mode='eval')
    if len(list(ast.walk(tree)))>100:raise ValueError('Unit expression too long')
    def evaluate(node,exponent=False):
        if isinstance(node,ast.Expression):return evaluate(node.body,exponent)
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):return float(node.value)
        if isinstance(node,ast.Name) and not exponent:
            return _LENGTH_IN_METERS[node.id]/_LENGTH_IN_METERS[target] if node.id in _LENGTH_IN_METERS else 1.0
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            return evaluate(node.operand,exponent)*(-1 if isinstance(node.op,ast.USub) else 1)
        if isinstance(node,ast.BinOp):
            a=evaluate(node.left,exponent)
            if isinstance(node.op,ast.Pow):
                power=evaluate(node.right,True)
                if abs(power)>12:raise ValueError('Unit exponent out of range')
                return a**power
            b=evaluate(node.right,exponent)
            if isinstance(node.op,ast.Mult):return a*b
            if isinstance(node.op,ast.Div):return a/b
        raise ValueError('Unsupported unit expression')
    result=evaluate(tree)
    if not math.isfinite(result) or result<=0:raise ValueError('Invalid unit scale')
    return result


def convert_length(value,unit,summary):
    """Return an equivalent value/unit; leave units without explicit length unchanged.

    Other named units (N, W, Pa, K, etc.) retain their meaning and spelling.
    The parser only evaluates numeric scaling of explicit m/mm/cm/um factors.
    """
    target=summary.get('coordinate_unit')
    if value is None or not isinstance(unit,str) or target not in _LENGTH_IN_METERS:return value,unit,None
    sources=_LENGTH_TOKEN.findall(unit)
    if not sources or all(s==target for s in sources):return value,unit,None
    if len(unit)>200:return value,unit,None
    try:factor=_factor(unit,target)
    except (ValueError,TypeError,SyntaxError,ZeroDivisionError,OverflowError):return value,unit,None
    def scale(item):
        if isinstance(item,list):return [scale(v) for v in item]
        result=float(Decimal(str(item))*Decimal(str(factor)))
        if not math.isfinite(result):raise ValueError("The unit conversion result is outside the valid numerical range.")
        return result
    converted=scale(value);new_unit=_LENGTH_TOKEN.sub(target,unit)
    note={'source_value':value,'source_unit':unit,'value':converted,'unit':new_unit}
    return converted,new_unit,note


def normalize_items(items,summary,key='name'):
    notes=[]
    for item in items:
        value,unit,note=convert_length(item.get('value'),item.get('unit'),summary)
        item.update(value=value,unit=unit)
        if note:notes.append({key:item[key],**note})
    return notes


def normalize_material_reply(reply,summary):
    notes=[]
    if reply.get('question_type')=='recommendation':
        for index,option in enumerate(reply['options']):
            notes.extend({'option_index':index,**n} for n in normalize_items(option['values'],summary))
    if 'proposed_card' in reply:notes.extend(normalize_items(reply['proposed_card']['constitutive_parameters'],summary))
    return notes


def normalize_boundary_reply(reply,summary):
    notes=normalize_items(reply['draft'],summary,'id')
    question=reply.get('question')
    if question and question.get('question_type')=='recommendation':
        for index,option in enumerate(question['options']):
            notes.extend({'option_index':index,**n} for n in normalize_items(option['values'],summary))
    return notes
