import re
from collections import Counter
from math import sqrt


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9+#./-]+", text.lower())


def cosine_similarity_text(a: str, b: str) -> float:
    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0

    counter_a = Counter(tokens_a)
    counter_b = Counter(tokens_b)
    vocabulary = set(counter_a) | set(counter_b)

    dot = sum(counter_a[token] * counter_b[token] for token in vocabulary)
    norm_a = sqrt(sum(value * value for value in counter_a.values()))
    norm_b = sqrt(sum(value * value for value in counter_b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return max(0.0, min(1.0, dot / (norm_a * norm_b)))
