import math
import re
from collections import Counter, defaultdict

from models.models import ErrorQuestion

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]")
NUMBER_PATTERN = re.compile(r"[+-]?\d+(?:\.\d+)?")
SPACE_PATTERN = re.compile(r"\s+")

WEIGHTS = {
    "knowledge_exact": 0.4,
    "error_exact": 0.3,
    "text_cosine": 0.3,
}


def _normalize(value):
    return (value or "").strip().lower()


def _tokens(text):
    return TOKEN_PATTERN.findall(_normalize(text))


def _cosine_similarity(text_a, text_b):
    tokens_a = _tokens(text_a)
    tokens_b = _tokens(text_b)
    if not tokens_a or not tokens_b:
        return 0.0

    counter_a = Counter(tokens_a)
    counter_b = Counter(tokens_b)
    keys = set(counter_a) | set(counter_b)

    dot_product = sum(counter_a[k] * counter_b[k] for k in keys)
    norm_a = math.sqrt(sum(v * v for v in counter_a.values()))
    norm_b = math.sqrt(sum(v * v for v in counter_b.values()))

    if not norm_a or not norm_b:
        return 0.0

    return dot_product / (norm_a * norm_b)


def _pattern_signature(text):
    normalized = _normalize(text)
    normalized = NUMBER_PATTERN.sub("<num>", normalized)
    normalized = SPACE_PATTERN.sub(" ", normalized)
    return normalized


def _score_components(current, candidate):
    knowledge_exact = 1.0 if _normalize(candidate.knowledge_point) == _normalize(current.knowledge_point) and _normalize(current.knowledge_point) else 0.0
    error_exact = 1.0 if _normalize(candidate.error_type) == _normalize(current.error_type) and _normalize(current.error_type) else 0.0
    text_cosine = _cosine_similarity(current.question or "", candidate.question or "")

    score = (
        WEIGHTS["knowledge_exact"] * knowledge_exact
        + WEIGHTS["error_exact"] * error_exact
        + WEIGHTS["text_cosine"] * text_cosine
    )

    return {
        "score": round(score, 6),
        "knowledge_exact": knowledge_exact,
        "error_exact": error_exact,
        "text_cosine": round(text_cosine, 6),
        "novelty": round(1 - text_cosine, 6),
        "weights": WEIGHTS,
    }


def _bucket_priority(row):
    breakdown = row["breakdown"]
    if breakdown["knowledge_exact"] and breakdown["error_exact"]:
        return 0
    if breakdown["knowledge_exact"]:
        return 1
    if breakdown["error_exact"]:
        return 2
    return 3


def _mmr_select(rows, limit):
    selected = []
    pattern_count = defaultdict(int)

    while rows and len(selected) < limit:
        best_idx = -1
        best_val = -10.0

        for idx, row in enumerate(rows):
            pattern = row["pattern_signature"]
            # Hard diversity constraint: one recommendation per pattern template.
            if pattern_count[pattern] >= 1:
                continue

            relevance = row["breakdown"]["score"]
            if selected:
                max_sim = max(
                    _cosine_similarity(row["item"].question or "", s["item"].question or "")
                    for s in selected
                )
            else:
                max_sim = 0.0

            # Maximal marginal relevance: keep relevance while encouraging diversity.
            mmr = 0.78 * relevance - 0.22 * max_sim

            # Small bonus for cross-error-type diversity under same knowledge point.
            if selected and any(
                _normalize(s["item"].knowledge_point) == _normalize(row["item"].knowledge_point)
                and _normalize(s["item"].error_type) != _normalize(row["item"].error_type)
                for s in selected
            ):
                mmr += 0.03

            if mmr > best_val:
                best_val = mmr
                best_idx = idx

        if best_idx < 0:
            break

        chosen = rows.pop(best_idx)
        chosen["breakdown"]["mmr"] = round(best_val, 6)
        selected.append(chosen)
        pattern_count[chosen["pattern_signature"]] += 1

    return selected


def get_recommendations(db_session, current_error, limit=5, min_score=0.22):
    candidates = (
        db_session.query(ErrorQuestion)
        .filter(ErrorQuestion.id != current_error.id)
        .all()
    )

    current_pattern = _pattern_signature(current_error.question or "")

    scored = []
    for item in candidates:
        breakdown = _score_components(current_error, item)
        if breakdown["score"] < min_score:
            continue

        pattern = _pattern_signature(item.question or "")
        pattern_same = pattern == current_pattern

        # Drop near-duplicate templates (same skeleton, only number changes).
        if pattern_same and breakdown["text_cosine"] >= 0.72:
            continue

        breakdown["pattern_same"] = pattern_same
        breakdown["bucket_priority"] = _bucket_priority({"breakdown": breakdown})
        scored.append(
            {
                "item": item,
                "breakdown": breakdown,
                "pattern_signature": pattern,
            }
        )

    strong = [row for row in scored if row["breakdown"]["bucket_priority"] <= 1]
    backup = [row for row in scored if row["breakdown"]["bucket_priority"] > 1]

    strong.sort(
        key=lambda row: (
            row["breakdown"]["bucket_priority"],
            -row["breakdown"]["score"],
        )
    )
    backup.sort(
        key=lambda row: (
            row["breakdown"]["bucket_priority"],
            -row["breakdown"]["score"],
        )
    )

    selected = _mmr_select(strong, limit)
    if not selected and backup:
        remainder = limit - len(selected)
        backup_selected = _mmr_select(backup, remainder)
        selected.extend(backup_selected)

    return selected
