"""Search API declarations and expand only their immediate structural neighbors."""
from copy import deepcopy

SEARCH_KINDS={"function","class","method","property","field"}
MEMBER_KINDS={"method","property","field"}
PORT_EDGES={"HAS_ARGUMENT","HAS_RETURN"}

def _index(graph):
    nodes={}
    for node in graph["nodes"]:
        if node["id"] in nodes:raise ValueError("Duplicate API node ID: "+node["id"])
        nodes[node["id"]]=node
    for edge in graph["edges"]:
        if edge["src"] not in nodes or edge["dst"] not in nodes:raise ValueError("Dangling graph edge")
    return nodes

def search_documents(graph):
    nodes=_index(graph);records=[]
    for key,node in sorted(nodes.items()):
        kind=node["kind"]
        if kind not in SEARCH_KINDS:continue
        lines=["API: "+key,"Kind: "+kind]
        description=node.get("description")
        if description:
            purpose=description if kind=="class" else description.split("\n\n",1)[0]
            lines.append("Purpose: "+purpose)
        records.append({"id":key,"text":"\n".join(lines)})
    return records

def expand_one_hop(graph,seeds):
    nodes=_index(graph);seeds=set(seeds);selected=set(seeds)
    for seed in seeds:
        if seed not in nodes or nodes[seed]["kind"] not in SEARCH_KINDS:
            raise ValueError("Only API declarations may be search seeds: "+seed)
    for edge in graph["edges"]:
        src,dst,kind=edge["src"],edge["dst"],edge["kind"]
        if src in seeds:
            if kind in PORT_EDGES:selected.add(dst)
            elif kind=="HAS_MEMBER" and nodes[src]["kind"]=="class" and nodes[dst]["kind"]=="field":selected.add(dst)
        if dst in seeds and kind=="HAS_MEMBER" and nodes[dst]["kind"] in MEMBER_KINDS:selected.add(src)
    return {
        "nodes":[{k:deepcopy(v) for k,v in nodes[key].items() if k!="sources"} for key in sorted(selected)],
        "edges":[{k:deepcopy(v) for k,v in e.items() if k!="evidence"} for e in graph["edges"] if e["src"] in selected and e["dst"] in selected],
    }
