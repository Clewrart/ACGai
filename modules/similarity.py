import difflib
import json

from .db import list_works
from .image_analyzer import hamming_hex as image_hamming_hex, image_match_label
from .text_analyzer import hamming_hex as text_hamming_hex, text_match_label


def compare_image_to_registry(phash_hex, top_k=10):
    results = []
    for work in list_works(limit=1000):
        old = work.get("phash_hex")
        if not old:
            continue
        dist = image_hamming_hex(phash_hex, old)
        if dist is None:
            continue
        results.append({
            "id": work["id"],
            "title": work["title"],
            "creator_alias": work["creator_alias"],
            "work_type": work["work_type"],
            "distance": dist,
            "label": image_match_label(dist),
            "created_at": work["created_at"],
            "platform_url": work.get("platform_url") or "",
        })
    results.sort(key=lambda x: x["distance"])
    return results[:top_k]


def compare_text_to_registry(simhash_hex, text, top_k=10):
    results = []
    text = text or ""
    for work in list_works(limit=1000):
        old_hash = work.get("simhash_hex")
        old_text = work.get("text_sample") or ""
        if not old_hash:
            continue
        dist = text_hamming_hex(simhash_hex, old_hash)
        seq_ratio = 0
        if old_text and text:
            seq_ratio = difflib.SequenceMatcher(None, text[:5000], old_text[:5000]).ratio()
        results.append({
            "id": work["id"],
            "title": work["title"],
            "creator_alias": work["creator_alias"],
            "work_type": work["work_type"],
            "distance": dist,
            "seq_ratio": round(seq_ratio, 4),
            "label": text_match_label(dist, seq_ratio),
            "created_at": work["created_at"],
            "platform_url": work.get("platform_url") or "",
        })

    def sort_key(x):
        d = x["distance"] if x["distance"] is not None else 999
        return (d, -x["seq_ratio"])

    results.sort(key=sort_key)
    return results[:top_k]
