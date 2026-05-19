import os
import re
import shutil
import unicodedata
from statistics import mean

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from config import OCR_LANG, TESSERACT_CMD

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None


def _detect_tesseract_cmd():
    if TESSERACT_CMD and os.path.exists(TESSERACT_CMD):
        return TESSERACT_CMD

    from_path = shutil.which("tesseract")
    if from_path:
        return from_path

    common_windows_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(common_windows_path):
        return common_windows_path

    return ""


if pytesseract:
    detected_cmd = _detect_tesseract_cmd()
    if detected_cmd:
        pytesseract.pytesseract.tesseract_cmd = detected_cmd


def _preprocess_image(img):
    # Convert to grayscale
    gray = ImageOps.grayscale(img)
    
    # Enhance contrast
    contrast = ImageEnhance.Contrast(gray).enhance(2.0)
    
    # Sharpen the image
    sharpened = ImageEnhance.Sharpness(contrast).enhance(2.0)
    
    # Apply median filter to reduce noise
    denoised = sharpened.filter(ImageFilter.MedianFilter(size=3))
    
    # Binarize the image using Otsu's method for better text extraction
    threshold = ImageOps.autocontrast(denoised, cutoff=0)
    
    return threshold


def _clean_text(text):
    normalized = unicodedata.normalize("NFKC", text or "")
    normalized = normalized.replace("\uFFFD", "")
    normalized = "".join(ch for ch in normalized if ch.isprintable() or ch in "\n\t")
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    return _normalize_ocr_text("\n".join(lines))


def _validate_question_format(text):
    """Validate if the extracted text resembles a question format."""
    if not text:
        return False, "empty"
    
    # Check for common question patterns
    lines = text.split('\n')
    
    # Look for multiple choice options (A, B, C, D)
    option_pattern = re.compile(r'\b[ABCD]\.?\s', re.IGNORECASE)
    options_found = len(option_pattern.findall(text))
    
    # Look for mathematical expressions
    math_pattern = re.compile(r'[+\-*/=×÷≠≈≤≥]')
    math_found = bool(math_pattern.search(text))
    
    # Look for question marks or typical question starters
    question_indicators = ['?', '？', '选择', '计算', '证明', '解答', '解题']
    has_question = any(indicator in text for indicator in question_indicators)
    
    # Basic heuristics
    if options_found >= 2:
        return True, "multiple_choice"
    elif math_found and len(text) > 10:
        return True, "math_problem"
    elif has_question and len(text) > 20:
        return True, "general_question"
    elif len(lines) > 1 and len(text) > 30:
        return True, "structured_text"
    else:
        return False, "unstructured"


def _format_question_text(text, question_type):
    """Format the text based on detected question type."""
    if question_type == "multiple_choice":
        # Ensure options are properly formatted
        lines = text.split('\n')
        formatted_lines = []
        for line in lines:
            # Format options like "A." or "A "
            line = re.sub(r'\b([ABCD])\.?\s*', r'\1. ', line, flags=re.IGNORECASE)
            formatted_lines.append(line.strip())
        return '\n'.join(formatted_lines)
    elif question_type == "math_problem":
        # Clean up mathematical expressions
        text = re.sub(r'×', '×', text)  # Ensure multiplication symbol
        text = re.sub(r'÷', '÷', text)  # Ensure division symbol
        return text
    else:
        return text


def _normalize_ocr_text(text):
    """Normalize OCR artifacts while preserving useful structure."""
    if not text:
        return ""

    normalized_lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # 1) Merge spaces between Chinese characters: "广 东 工 业" -> "广东工业"
        line = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", line)

        # 2) Remove spaces around Chinese punctuation and brackets.
        line = re.sub(r"\s*([，。！？；：、）】》])\s*", r"\1", line)
        line = re.sub(r"\s*([（【《])\s*", r"\1", line)

        # 3) Remove spaces between Chinese and punctuation/number boundaries.
        line = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[()（）\[\]【】《》,:：;；])", "", line)
        line = re.sub(r"(?<=[()（）\[\]【】《》,:：;；])\s+(?=[\u4e00-\u9fff])", "", line)

        # 4) Collapse repeated spaces in remaining regions (mainly English segments).
        line = re.sub(r"[ \t]{2,}", " ", line)

        normalized_lines.append(line)

    return "\n".join(normalized_lines)


_VALID_CHAR_PATTERN = re.compile(r"[A-Za-z0-9\u4e00-\u9fff，。！？；：、,.!?;:()（）\[\]{}<>+\-*/=_%#@'\" \n\t]")


def _noise_ratio(text):
    if not text:
        return 1.0
    total = len(text)
    valid = sum(1 for ch in text if _VALID_CHAR_PATTERN.fullmatch(ch))
    return max(0.0, min(1.0, 1 - valid / total))


def _get_available_languages():
    if not pytesseract:
        return set()

    try:
        return set(pytesseract.get_languages(config=""))
    except Exception:
        return set()


def _select_ocr_lang():
    preferred = [lang.strip() for lang in (OCR_LANG or "").split("+") if lang.strip()]
    available = _get_available_languages()

    if not available:
        return "eng"

    selected = [lang for lang in preferred if lang in available]
    if selected:
        return "+".join(selected)

    if "eng" in available:
        return "eng"

    return sorted(available)[0]


def _extract_once(image_obj, lang, config):
    data = pytesseract.image_to_data(
        image_obj,
        lang=lang,
        config=config,
        output_type=pytesseract.Output.DICT,
    )
    text = pytesseract.image_to_string(image_obj, lang=lang, config=config)

    confidences = []
    for conf in data.get("conf", []):
        try:
            value = float(conf)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            confidences.append(value)

    avg_conf = mean(confidences) / 100.0 if confidences else 0.0
    word_count = len([w for w in data.get("text", []) if (w or "").strip()])

    return {
        "text": _clean_text(text),
        "confidence": avg_conf,
        "word_count": word_count,
    }


def extract_text_with_meta(image_path):
    if not pytesseract:
        return {
            "text": "",
            "status": "unavailable",
            "confidence": 0.0,
            "raw_word_count": 0,
            "noise_ratio": 1.0,
        }

    ocr_lang = _select_ocr_lang()

    try:
        with Image.open(image_path) as img:
            processed = _preprocess_image(img)

            candidates = [
                _extract_once(processed, ocr_lang, "--oem 3 --psm 6"),
                _extract_once(processed, ocr_lang, "--oem 3 --psm 11"),
                _extract_once(img, ocr_lang, "--oem 3 --psm 6"),
            ]
    except Exception:
        return {
            "text": "",
            "status": "failed",
            "confidence": 0.0,
            "raw_word_count": 0,
            "noise_ratio": 1.0,
        }

    best = max(candidates, key=lambda x: (x["confidence"], len(x["text"])))
    noise = _noise_ratio(best["text"])
    
    # Validate question format
    is_valid_format, format_type = _validate_question_format(best["text"])
    
    status = "ok"
    if not best["text"]:
        status = "failed"
    elif best["confidence"] < 0.45 or noise > 0.35:
        status = "low_confidence"
    elif not is_valid_format:
        status = "invalid_format"

    # Format the text if valid
    formatted_text = best["text"]
    if is_valid_format:
        formatted_text = _format_question_text(best["text"], format_type)

    return {
        "text": _clean_text(formatted_text),
        "status": status,
        "confidence": round(max(0.0, min(1.0, best["confidence"])), 4),
        "raw_word_count": best["word_count"],
        "noise_ratio": round(noise, 4),
        "format_type": format_type if is_valid_format else "unknown",
    }


def extract_text(image_path):
    return extract_text_with_meta(image_path).get("text", "")
