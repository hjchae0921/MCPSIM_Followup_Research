"""Validate bundled embeddings or embed declarations and current Procedures."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from .contracts import MODEL, fingerprint
from .retrieval import GRAPH, INDEX, QUERIES, GraphRetriever
from .search import search_documents


def save(path,ids,vectors,metadata):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('wb') as stream:
        np.savez_compressed(stream,ids=np.asarray(ids),vectors=np.asarray(vectors,dtype=np.float64))
    path.with_suffix('.meta.json').write_text(json.dumps(metadata,indent=2)+'\n')


def embed_current():
    from common.models import credentials
    from openai import OpenAI
    from codegen.cards import templates
    from codegen.runner import procedure
    key=credentials()
    if not key:raise ValueError('Set OPENAI_API_KEY before creating embeddings.')
    graph=json.loads(GRAPH.read_text())
    records=search_documents(graph)
    groups=[(INDEX,[r['id'] for r in records],[r['text'] for r in records]),
        (QUERIES,None,list(dict.fromkeys(q for s in templates().values() for q in procedure(s))))]
    with OpenAI(api_key=key,timeout=120) as client:
        for path,ids,texts in groups:
            ids=texts if ids is None else ids
            key=fingerprint(ids,texts)
            metadata=path.with_suffix('.meta.json')
            if path.is_file() and metadata.is_file():
                saved=json.loads(metadata.read_text())
                if saved.get('model')==MODEL and saved.get('fingerprint')==key:
                    continue
            vectors=[]
            for start in range(0,len(texts),128):
                response=client.embeddings.create(model=MODEL,input=texts[start:start+128])
                batch=sorted(response.data,key=lambda item:item.index)
                if len(batch)!=len(texts[start:start+128]):raise ValueError('Embedding response count mismatch')
                vectors.extend(item.embedding for item in batch)
            info={'model':MODEL,'fingerprint':key,'count':len(ids),'variant':'split_members'}
            save(path,ids,vectors,info)
            if path==QUERIES:
                info['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                metadata.write_text(json.dumps(info,indent=2)+'\n')


def validate():
    from codegen.cards import templates
    from codegen.runner import procedure
    retriever=GraphRetriever.load()
    stages={}
    for stage,source in templates().items():
        result=retriever.retrieve(procedure(source))
        stages[stage]={'nodes':result.node_count,'edges':result.edge_count}
    return {'api_declarations':len(retriever.ids),'top_k':3,'hops':1,'stages':stages}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--embed',action='store_true',help='Create embeddings for the current graph and Procedures using OpenAI.')
    args=parser.parse_args()
    if args.embed:embed_current()
    print(json.dumps(validate(),indent=2))
