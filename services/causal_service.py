def explain_recommendation(current, candidate, breakdown=None):
    reasons = []

    if (current.knowledge_point or "").strip() and (current.knowledge_point or "").strip() == (candidate.knowledge_point or "").strip():
        reasons.append("知识点一致")

    if (current.error_type or "").strip() and (current.error_type or "").strip() == (candidate.error_type or "").strip():
        reasons.append("错误类型一致")

    if breakdown and breakdown.get("text_cosine", 0) >= 0.3:
        reasons.append("题目文本相似度较高")

    if breakdown and not breakdown.get("pattern_same", False):
        reasons.append("题型相关但题干结构不同")

    if not reasons:
        reasons.append("题目文本存在一定相似性")

    return "，".join(reasons)
