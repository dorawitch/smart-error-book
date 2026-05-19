from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = PROJECT_ROOT / "paper"
REPORT_PATH = PAPER_DIR / "recommendation_evaluation.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.models import ErrorQuestion, get_session
from services.recommend_service import (
    _cosine_similarity,
    _normalize,
    _pattern_signature,
    get_recommendations,
)


def _same_label(query: ErrorQuestion, candidate: ErrorQuestion) -> bool:
    return (
        _normalize(query.knowledge_point) == _normalize(candidate.knowledge_point)
        and _normalize(query.error_type) == _normalize(candidate.error_type)
    )


def _same_knowledge(query: ErrorQuestion, candidate: ErrorQuestion) -> bool:
    return _normalize(query.knowledge_point) == _normalize(candidate.knowledge_point)


def _baseline_text_only(query: ErrorQuestion, all_items: list[ErrorQuestion], limit: int) -> list[ErrorQuestion]:
    scored = []
    for item in all_items:
        if item.id == query.id:
            continue
        score = _cosine_similarity(query.question or "", item.question or "")
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda row: row[0], reverse=True)
    return [item for _, item in scored[:limit]]


def _baseline_fused(query: ErrorQuestion, all_items: list[ErrorQuestion], limit: int) -> list[ErrorQuestion]:
    scored = []
    for item in all_items:
        if item.id == query.id:
            continue

        knowledge_exact = 1.0 if _normalize(item.knowledge_point) == _normalize(query.knowledge_point) and _normalize(query.knowledge_point) else 0.0
        error_exact = 1.0 if _normalize(item.error_type) == _normalize(query.error_type) and _normalize(query.error_type) else 0.0
        text_cosine = _cosine_similarity(query.question or "", item.question or "")
        score = 0.4 * knowledge_exact + 0.3 * error_exact + 0.3 * text_cosine
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda row: row[0], reverse=True)
    return [item for _, item in scored[:limit]]


def _proposed(query: ErrorQuestion, db_session, limit: int) -> list[ErrorQuestion]:
    rows = get_recommendations(db_session, query, limit=limit, min_score=0.08)
    return [row["item"] for row in rows]


def _precision_at_k(query: ErrorQuestion, recs: list[ErrorQuestion]) -> float:
    if not recs:
        return 0.0
    hits = sum(1 for item in recs if _same_label(query, item))
    return hits / len(recs)


def _knowledge_precision_at_k(query: ErrorQuestion, recs: list[ErrorQuestion]) -> float:
    if not recs:
        return 0.0
    hits = sum(1 for item in recs if _same_knowledge(query, item))
    return hits / len(recs)


def _mrr_at_k(query: ErrorQuestion, recs: list[ErrorQuestion]) -> float:
    for idx, item in enumerate(recs, start=1):
        if _same_label(query, item):
            return 1.0 / idx
    return 0.0


def _novelty_rate(query: ErrorQuestion, recs: list[ErrorQuestion]) -> float:
    if not recs:
        return 0.0
    query_pattern = _pattern_signature(query.question or "")
    novel = sum(1 for item in recs if _pattern_signature(item.question or "") != query_pattern)
    return novel / len(recs)


def _intra_list_diversity(recs: list[ErrorQuestion]) -> float:
    if len(recs) <= 1:
        return 0.0

    values = []
    for idx, left in enumerate(recs):
        for right in recs[idx + 1 :]:
            values.append(1.0 - _cosine_similarity(left.question or "", right.question or ""))
    return mean(values) if values else 0.0


def _sample_cases(all_items: list[ErrorQuestion], db_session) -> list[dict]:
    groups = defaultdict(list)
    for item in all_items:
        groups[(item.knowledge_point, item.error_type)].append(item)

    selected_queries = []
    for _, group in sorted(groups.items(), key=lambda row: len(row[1]), reverse=True):
        if len(group) >= 8:
            selected_queries.append(group[0])
        if len(selected_queries) == 3:
            break

    cases = []
    for query in selected_queries:
        proposed = _proposed(query, db_session, limit=5)
        cases.append(
            {
                "query": query.question,
                "knowledge_point": query.knowledge_point,
                "error_type": query.error_type,
                "recommendations": [item.question for item in proposed],
            }
        )
    return cases


def main() -> None:
    PAPER_DIR.mkdir(parents=True, exist_ok=True)

    session = get_session()
    try:
        all_items = session.query(ErrorQuestion).all()
        eligible = []
        label_counts = Counter((_normalize(item.knowledge_point), _normalize(item.error_type)) for item in all_items)
        for item in all_items:
            if label_counts[(_normalize(item.knowledge_point), _normalize(item.error_type))] >= 3:
                eligible.append(item)

        sampled = []
        sampled_per_label = Counter()
        for item in eligible:
            key = (_normalize(item.knowledge_point), _normalize(item.error_type))
            if sampled_per_label[key] < 18:
                sampled.append(item)
                sampled_per_label[key] += 1

        evaluators = {
            "text_only_baseline": lambda q: _baseline_text_only(q, all_items, limit=5),
            "fused_score_baseline": lambda q: _baseline_fused(q, all_items, limit=5),
            "proposed_model": lambda q: _proposed(q, session, limit=5),
        }

        results = {}
        for name, runner in evaluators.items():
            precision_values = []
            knowledge_precision_values = []
            mrr_values = []
            novelty_values = []
            diversity_values = []

            for query in sampled:
                recs = runner(query)
                precision_values.append(_precision_at_k(query, recs))
                knowledge_precision_values.append(_knowledge_precision_at_k(query, recs))
                mrr_values.append(_mrr_at_k(query, recs))
                novelty_values.append(_novelty_rate(query, recs))
                diversity_values.append(_intra_list_diversity(recs))

            results[name] = {
                "sample_size": len(sampled),
                "precision_at_5_same_label": round(mean(precision_values), 4) if precision_values else 0.0,
                "precision_at_5_same_knowledge": round(mean(knowledge_precision_values), 4) if knowledge_precision_values else 0.0,
                "mrr_at_5": round(mean(mrr_values), 4) if mrr_values else 0.0,
                "novelty_rate_at_5": round(mean(novelty_values), 4) if novelty_values else 0.0,
                "intra_list_diversity": round(mean(diversity_values), 4) if diversity_values else 0.0,
            }

        report = {
            "dataset_total": len(all_items),
            "eligible_queries": len(eligible),
            "evaluated_queries": len(sampled),
            "metrics": results,
            "sample_cases": _sample_cases(all_items, session),
        }

        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        session.close()


if __name__ == "__main__":
    main()
