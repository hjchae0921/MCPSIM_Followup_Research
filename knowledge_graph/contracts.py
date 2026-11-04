"""Retrieval result containers and deterministic embedding fingerprints."""

from dataclasses import dataclass
import hashlib
from .identity import stable


MODEL = "text-embedding-3-large"


def fingerprint(ids, texts):
    return hashlib.sha256(stable({"ids": ids, "texts": texts, "model": MODEL}).encode()).hexdigest()


@dataclass
class RetrievedGraph:
    fragment: dict
    payload: dict
    text: str
    rankings: list
    original_ids: dict

    @property
    def node_count(self):
        return len(self.fragment["nodes"])

    @property
    def edge_count(self):
        return len(self.fragment["edges"])
