import hashlib
import math
import re
from collections import Counter

from .utils import sha256_text


PUNCS = "。！？!?，,、；;：:“”\"‘’'（）()【】[]《》<>……—-~"


def split_sentences(text):
    parts = re.split(r"[。！？!?\\n]+", text)
    return [p.strip() for p in parts if p.strip()]


def tokenize_for_simhash(text):
    # 中文按 2 字符滑窗，英文按单词；适合 MVP，不依赖 jieba
    clean = re.sub(r"\\s+", "", text)
    cjk = re.findall(r"[\\u4e00-\\u9fff]", clean)
    tokens = []
    if len(cjk) >= 2:
        tokens.extend(["".join(cjk[i:i + 2]) for i in range(len(cjk) - 1)])
    tokens.extend(re.findall(r"[A-Za-z0-9_]+", text.lower()))
    return tokens


def simhash_text(text, bits=64):
    tokens = tokenize_for_simhash(text)
    if not tokens:
        return "0" * (bits // 4)

    weights = Counter(tokens)
    v = [0] * bits

    for token, weight in weights.items():
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        n = int(digest, 16)
        for i in range(bits):
            bit = (n >> i) & 1
            v[i] += weight if bit else -weight

    value = 0
    for i, score in enumerate(v):
        if score > 0:
            value |= 1 << i

    return f"{value:0{bits // 4}x}"


def hamming_hex(a, b):
    if not a or not b:
        return None
    try:
        return (int(a, 16) ^ int(b, 16)).bit_count()
    except ValueError:
        return None


def repeated_ngram_ratio(tokens, n=4):
    if len(tokens) < n:
        return 0.0
    grams = [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
    counts = Counter(grams)
    repeated = sum(c - 1 for c in counts.values() if c > 1)
    return repeated / max(1, len(grams))


def analyze_text(text):
    text = text or ""
    sentences = split_sentences(text)
    sent_lens = [len(s) for s in sentences] or [0]

    chars = [c for c in text if not c.isspace()]
    cjk_chars = re.findall(r"[\\u4e00-\\u9fff]", text)
    punc_count = sum(1 for c in text if c in PUNCS)

    unique_chars = len(set(chars))
    type_token_ratio = unique_chars / max(1, len(chars))

    avg_sentence_len = sum(sent_lens) / max(1, len(sent_lens))
    if len(sent_lens) > 1:
        mean = avg_sentence_len
        variance = sum((x - mean) ** 2 for x in sent_lens) / len(sent_lens)
        sentence_len_cv = math.sqrt(variance) / max(1, mean)
    else:
        sentence_len_cv = 0

    tokens = tokenize_for_simhash(text)
    repeat4 = repeated_ngram_ratio(tokens, n=4)
    punc_ratio = punc_count / max(1, len(chars))

    # 轻量文本启发式：只能提示“可能机器化/模板化”，不能定责
    risk = 0
    reasons = []

    if len(chars) >= 300 and sentence_len_cv < 0.28:
        risk += 22
        reasons.append("句长波动偏低，文本可能较模板化或经过机器润色")

    if len(chars) >= 300 and type_token_ratio < 0.42:
        risk += 16
        reasons.append("字词多样性偏低，可能存在重复表达或模板痕迹")

    if repeat4 > 0.06:
        risk += 20
        reasons.append("重复 n-gram 偏多，可能存在洗稿、套话或模型复述")

    if punc_ratio > 0.13:
        risk += 10
        reasons.append("标点比例偏高，建议复核语气词、断句和排版习惯")

    if 0 < len(chars) < 180:
        risk += 8
        reasons.append("文本太短，AI 鉴定稳定性较差，只适合作弱提示")

    risk = max(0, min(100, risk))

    if risk < 30:
        level = "低"
    elif risk < 60:
        level = "中"
    else:
        level = "高"

    return {
        "kind": "text",
        "text_sha256": sha256_text(text),
        "simhash_hex": simhash_text(text),
        "char_count": len(chars),
        "cjk_char_count": len(cjk_chars),
        "sentence_count": len(sentences),
        "avg_sentence_len": round(avg_sentence_len, 2),
        "sentence_len_cv": round(sentence_len_cv, 4),
        "type_token_ratio": round(type_token_ratio, 4),
        "punctuation_ratio": round(punc_ratio, 4),
        "repeat_4gram_ratio": round(repeat4, 4),
        "ai_risk_score": risk,
        "ai_risk_level": level,
        "risk_reasons": reasons,
    }


def text_match_label(distance, seq_ratio=None):
    if distance is None:
        return "无法比较"
    if distance <= 6:
        return "高度相似，可能是同文、轻微改写或局部洗稿"
    if distance <= 14:
        return "较相似，建议人工复核设定、句式和关键情节"
    if distance <= 24:
        return "有一定相似，可能是题材、设定或表达习惯接近"
    if seq_ratio is not None and seq_ratio >= 0.55:
        return "表面文本重合较高，建议人工复核"
    return "相似度低"
