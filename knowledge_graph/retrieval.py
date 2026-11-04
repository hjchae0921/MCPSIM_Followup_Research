"""Rank API declarations by cosine similarity and expand one structural hop.

Class members compete independently with classes and functions. No API-specific
filters or score bonuses are used. The coder receives a compact declaration view.
"""

import hashlib
import json
from pathlib import Path

import numpy as np

from .contracts import MODEL, RetrievedGraph, fingerprint
from .ranking import rank
from .wire import dumps as dump
from .search import expand_one_hop, search_documents
from .wire import FORMAT, decode, id_map


HERE = Path(__file__).resolve().parent
GRAPH = HERE / "assets/api_graph.json"
INDEX = HERE / "assets/api_embeddings.npz"
QUERIES = HERE / "assets/procedure_embeddings.npz"
TOP_K = 3
HOPS = 1
SEARCH_VARIANT = "split_members"
EXPANSION_POLICY = "class_fields"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def configuration():
    """Snapshot the actual retrieval assets along with each immutable web job."""
    return {
        "payload_format": FORMAT,
        "top_k": TOP_K, "hops": HOPS, "queries": "numbered Procedure items only",
        "search_variant": SEARCH_VARIANT, "expansion_policy": EXPANSION_POLICY,
        "embedding_model": MODEL, "graph_sha256": sha(GRAPH),
        "index_sha256": sha(INDEX), "query_cache_sha256": sha(QUERIES),
    }


class GraphRetriever:
    def __init__(self, graph, ids, vectors, query_vectors=None):
        expected = [row["id"] for row in search_documents(graph)]
        if list(ids) != expected:
            raise ValueError("The API index must match the separate API search records")
        self.graph, self.ids = graph, list(ids)
        self.vectors = np.asarray(vectors, dtype=np.float64)
        if (self.vectors.ndim != 2 or len(self.vectors) != len(self.ids)
                or not np.all(np.isfinite(self.vectors))
                or np.any(np.linalg.norm(self.vectors, axis=1) == 0)):
            raise ValueError("Invalid API API embedding matrix")
        self.query_vectors = dict(query_vectors or {})

    @classmethod
    def load(cls, expected=None):
        current = configuration()
        if expected is not None and expected != current:
            raise ValueError("Retrieval settings or assets changed after this job was created")
        graph = json.loads(GRAPH.read_text())
        rows = search_documents(graph)
        ids, texts = [r["id"] for r in rows], [r["text"] for r in rows]
        metadata = json.loads(INDEX.with_suffix(".meta.json").read_text())
        if (metadata.get("model") != MODEL or metadata.get("variant") != SEARCH_VARIANT
                or metadata.get("fingerprint") != fingerprint(ids, texts)):
            raise ValueError("The API API embeddings do not match the current documents")
        qmeta = json.loads(QUERIES.with_suffix(".meta.json").read_text())
        if qmeta.get("model") != MODEL or qmeta.get("sha256") != sha(QUERIES):
            raise ValueError("The API Procedure embedding cache is inconsistent")
        with np.load(QUERIES, allow_pickle=False) as data:
            queries = dict(zip(data["ids"].tolist(), data["vectors"]))
        with np.load(INDEX, allow_pickle=False) as data:
            return cls(graph, data["ids"].tolist(), data["vectors"], queries)

    def retrieve(self, queries, *, query_vectors=None, client=None):
        queries = list(queries)
        if not queries:
            raise ValueError("At least one numbered Procedure item is required")
        vectors = {**self.query_vectors, **(query_vectors or {})}
        missing = list(dict.fromkeys(q for q in queries if q not in vectors))
        if missing:
            if client is None:
                raise ValueError("New Procedure items require an embedding client")
            response = client.embeddings.create(model=MODEL, input=missing)
            data = sorted(response.data, key=lambda item: item.index)
            if [item.index for item in data] != list(range(len(missing))):
                raise ValueError("Query embedding response count or indices mismatch")
            vectors.update((q, item.embedding) for q, item in zip(missing, data))
            self.query_vectors.update({q: vectors[q] for q in missing})
        for query in queries:
            if np.asarray(vectors[query]).shape != (self.vectors.shape[1],):
                raise ValueError("Query embedding dimensions do not match the API index")
        rankings, _ = rank(queries, vectors, self.ids, self.vectors, top_k=TOP_K)
        seeds = {item["id"] for row in rankings for item in row["top_3"]}
        fragment = expand_one_hop(self.graph, seeds)
        text = dump(fragment)
        payload, original = json.loads(text), id_map(fragment)
        if decode(payload, original_ids=original) != fragment:
            raise ValueError("Compact serialization changed a declaration or relationship")
        return RetrievedGraph(fragment, payload, text, rankings, original)
