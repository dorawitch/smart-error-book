from collections import Counter
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, jsonify, request, send_from_directory
from sqlalchemy import desc, func
from werkzeug.utils import secure_filename

from config import UPLOAD_FOLDER
from models.models import ErrorQuestion, get_session
from services.causal_service import explain_recommendation
from services.ocr_service import extract_text_with_meta
from services.recommend_service import get_recommendations

error_bp = Blueprint("error", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}


def _allowed_file(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def _build_image_url(image_path):
    if not image_path:
        return None

    filename = Path(image_path).name
    return f"{request.host_url.rstrip('/')}/uploads/{filename}"


def _serialize_error(error):
    return error.to_dict(image_url=_build_image_url(error.image_path))


def _confidence_level(score):
    if score >= 0.7:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


@error_bp.route("/uploads/<path:filename>", methods=["GET"])
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@error_bp.route("/upload", methods=["POST"])
def upload():
    db = get_session()
    try:
        file = request.files.get("image")
        if not file:
            return jsonify({"error": "缺少图片文件（字段名应为 image）"}), 400

        if not _allowed_file(file.filename):
            return jsonify({"error": "文件类型不支持，仅支持 png/jpg/jpeg/bmp/webp"}), 400

        upload_dir = Path(UPLOAD_FOLDER)
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_name = secure_filename(file.filename)
        unique_name = f"{uuid4().hex}_{safe_name}"
        save_path = upload_dir / unique_name
        file.save(save_path)

        ocr_meta = extract_text_with_meta(str(save_path))
        text = (ocr_meta.get("text") or "").strip()

        if not text or ocr_meta.get("status") in ["low_confidence", "invalid_format", "failed"]:
            if ocr_meta.get("status") == "invalid_format":
                text = "（OCR 识别的文本格式不符合题目要求，请检查图片质量或手动编辑）"
            else:
                text = "（OCR 未识别出文本，可手动编辑）"

        error = ErrorQuestion(
            question=text,
            knowledge_point=(request.form.get("knowledge_point") or "").strip() or None,
            error_type=(request.form.get("error_type") or "").strip() or None,
            image_path=str(save_path),
            created_at=datetime.utcnow(),
        )

        db.add(error)
        db.commit()
        db.refresh(error)

        return jsonify(
            {
                "msg": "上传并保存成功",
                "item": _serialize_error(error),
                "ai": {
                    "ocr_status": ocr_meta.get("status"),
                    "ocr_confidence": ocr_meta.get("confidence"),
                    "ocr_word_count": ocr_meta.get("raw_word_count"),
                    "ocr_noise_ratio": ocr_meta.get("noise_ratio"),
                },
            }
        )
    except Exception as exc:
        db.rollback()
        return jsonify({"error": f"上传失败: {exc}"}), 500
    finally:
        db.close()


@error_bp.route("/list", methods=["GET"])
def list_errors():
    db = get_session()
    try:
        page = max(int(request.args.get("page", 1)), 1)
        page_size = min(max(int(request.args.get("page_size", 10)), 1), 50)

        keyword = (request.args.get("keyword") or "").strip()
        knowledge_point = (request.args.get("knowledge_point") or "").strip()
        error_type = (request.args.get("error_type") or "").strip()

        query = db.query(ErrorQuestion)

        if keyword:
            like_pattern = f"%{keyword}%"
            query = query.filter(ErrorQuestion.question.ilike(like_pattern))

        if knowledge_point:
            query = query.filter(ErrorQuestion.knowledge_point == knowledge_point)

        if error_type:
            query = query.filter(ErrorQuestion.error_type == error_type)

        total = query.count()

        items = (
            query.order_by(desc(ErrorQuestion.created_at), desc(ErrorQuestion.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return jsonify(
            {
                "items": [_serialize_error(item) for item in items],
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_next": page * page_size < total,
            }
        )
    finally:
        db.close()


@error_bp.route("/recommend/<int:error_id>", methods=["GET"])
def recommend(error_id):
    db = get_session()
    try:
        current = db.query(ErrorQuestion).filter_by(id=error_id).first()
        if not current:
            return jsonify({"error": "错题不存在"}), 404

        limit = min(max(int(request.args.get("limit", 5)), 1), 20)
        min_score = max(0.0, min(float(request.args.get("min_score", 0.22)), 1.0))

        rec_rows = get_recommendations(db, current, limit=limit, min_score=min_score)

        recommendations = []
        for row in rec_rows:
            item = row["item"]
            breakdown = row["breakdown"]

            payload = _serialize_error(item)
            payload["reason"] = explain_recommendation(current, item, breakdown)
            payload["score"] = breakdown["score"]
            payload["confidence_level"] = _confidence_level(breakdown["score"])
            payload["evidence"] = {
                "knowledge_exact": breakdown["knowledge_exact"],
                "error_exact": breakdown["error_exact"],
                "text_cosine": breakdown["text_cosine"],
                "novelty": breakdown.get("novelty"),
                "pattern_same": breakdown.get("pattern_same"),
                "mmr": breakdown.get("mmr"),
                "weights": breakdown["weights"],
            }
            recommendations.append(payload)

        return jsonify(
            {
                "current_id": error_id,
                "reason": "按知识点、错误类型和题目文本相似度综合排序，并设置最小分阈值",
                "min_score": min_score,
                "recommendations": recommendations,
            }
        )
    finally:
        db.close()


@error_bp.route("/delete/<int:error_id>", methods=["DELETE"])
def delete_error(error_id):
    db = get_session()
    try:
        error = db.query(ErrorQuestion).filter_by(id=error_id).first()
        if not error:
            return jsonify({"error": "错题不存在"}), 404

        image_path = error.image_path
        db.delete(error)
        db.commit()

        if image_path:
            img_path = Path(image_path)
            if img_path.exists():
                img_path.unlink(missing_ok=True)

        return jsonify({"msg": "错题已删除"})
    except Exception as exc:
        db.rollback()
        return jsonify({"error": f"删除失败: {exc}"}), 500
    finally:
        db.close()


@error_bp.route("/update/<int:error_id>", methods=["PUT"])
def update_error(error_id):
    db = get_session()
    try:
        payload = request.get_json(silent=True) or {}

        error = db.query(ErrorQuestion).filter_by(id=error_id).first()
        if not error:
            return jsonify({"error": "错题不存在"}), 404

        if "question" in payload:
            error.question = (payload.get("question") or "").strip() or error.question

        if "knowledge_point" in payload:
            error.knowledge_point = (payload.get("knowledge_point") or "").strip() or None

        if "error_type" in payload:
            error.error_type = (payload.get("error_type") or "").strip() or None

        if "answer" in payload:
            error.answer = (payload.get("answer") or "").strip() or None

        db.commit()
        db.refresh(error)

        return jsonify({"msg": "错题已更新", "item": _serialize_error(error)})
    except Exception as exc:
        db.rollback()
        return jsonify({"error": f"更新失败: {exc}"}), 500
    finally:
        db.close()


@error_bp.route("/stats", methods=["GET"])
def stats():
    db = get_session()
    try:
        total = db.query(func.count(ErrorQuestion.id)).scalar() or 0

        all_items = db.query(ErrorQuestion.knowledge_point, ErrorQuestion.error_type).all()
        knowledge_counter = Counter((k or "未标注") for k, _ in all_items)
        type_counter = Counter((t or "未标注") for _, t in all_items)

        return jsonify(
            {
                "total": total,
                "knowledge_top": [
                    {"name": name, "count": count}
                    for name, count in knowledge_counter.most_common(6)
                ],
                "error_type_top": [
                    {"name": name, "count": count}
                    for name, count in type_counter.most_common(6)
                ],
            }
        )
    finally:
        db.close()
