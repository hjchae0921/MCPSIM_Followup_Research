"""Cosine ranking over all indexed API declarations."""
import numpy as np

def rank(queries, query_vectors, ids, vectors, top_k=3):
    matrix = np.asarray(vectors, dtype=np.float64)
    norms = np.linalg.norm(matrix, axis=1)
    if len(matrix) != len(ids) or not np.all(np.isfinite(matrix)) or np.any(norms == 0):
        raise ValueError("Invalid embedding matrix")
    results, positions = [], []
    for query in queries:
        vector = np.asarray(query_vectors[query], dtype=np.float64)
        if not np.all(np.isfinite(vector)) or np.linalg.norm(vector) == 0:
            raise ValueError("Invalid query embedding")
        scores = matrix @ vector / (norms * np.linalg.norm(vector))
        ordered = sorted(zip(scores.tolist(), ids), reverse=True)
        results.append({"query": query, "top_3": [
            {"rank": i, "id": key, "cosine_similarity": value}
            for i, (value, key) in enumerate(ordered[:top_k], 1)]})
        positions.append({key: {"rank": i, "cosine_similarity": value}
                          for i, (value, key) in enumerate(ordered, 1)})
    return results, positions
