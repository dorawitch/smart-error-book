# -*- coding: utf-8 -*-
import os
import re
import unicodedata
from statistics import mean
import easyocr

# 初始化 EasyOCR (支持中英双语，全学科通用)
_READER = easyocr.Reader(['ch_sim', 'en'], gpu=False)

def _advanced_layout_engine(ocr_results):
    """
    【全学科通用布局引擎】
    通过动态行高算法，适配数学公式、英语长句、语文古诗的排版
    """
    if not ocr_results: return ""
    
    # 1. 初始按 Y 轴顶端排序
    ocr_results.sort(key=lambda x: x[0][0][1])
    
    rows = []
    for res in ocr_results:
        box, text, conf = res
        y_top, y_bot = box[0][1], box[2][1]
        center_y = (y_top + y_bot) / 2
        
        assigned = False
        for row in rows:
            # 计算行基准高度
            row_top = min(b[0][0][1] for b in row)
            row_bot = max(b[0][2][1] for b in row)
            row_height = row_bot - row_top
            
            # 如果文字中心落在行的 70% 范围内，或者垂直重叠度高，则视为同一行
            # 这样可以兼容数学公式中的分子分母偏移
            if row_top - 5 < center_y < row_bot + 5:
                row.append(res)
                assigned = True
                break
        
        if not assigned:
            rows.append([res])

    output_lines = []
    for row in rows:
        row.sort(key=lambda x: x[0][0][0]) # 行内按 X 排序
        
        line_str = ""
        for i, item in enumerate(row):
            txt = item[1].strip()
            if not txt: continue
            
            if i > 0:
                prev_x_end = row[i-1][0][1][0]
                curr_x_start = row[i][0][0][0]
                dist = curr_x_start - prev_x_end
                
                # 智能空格判定：根据间距比例决定是否加空格
                if dist > 15: # 明显的单词间距
                    line_str += " " + txt
                else: # 紧凑字符（可能是被切开的单词）
                    line_str += txt
            else:
                line_str = txt
        output_lines.append(line_str)
        
    return "\n".join(output_lines)

def _universal_cleaner(text):
    """
    【学科无关的通用清洗】
    """
    # 1. 基础清理：Unicode 归一化
    text = unicodedata.normalize("NFKC", text)
    
    # 2. 结构标准化 (适配所有学科的题目)
    # 规范化题号 (例如: 02. (1) 等)
    text = re.sub(r"^(\d+)[\s。．,，、]+", r"\1. ", text, flags=re.M)
    # 规范化选项 (A. B. C. D.)
    text = re.sub(r"\b([A-D])[\s。．,，、]+", r"\1. ", text)
    # 规范化填空括号 ( )
    text = re.sub(r"[\(\uff08]\s*[\)\uff09]", "( )", text)
    
    # 3. 常见 OCR 漂移符号修复 (仅限于不影响语义的符号)
    sym_map = {
        "$": "S", 
        "|": "I",
        "~": "-",
        "○": "0",
    }
    for s, r in sym_map.items():
        text = text.replace(s, r)

    # 4. 移除明显的图片边缘噪声 (单字乱码出现在最后一行且置信度低)
    lines = text.splitlines()
    if lines and len(lines[-1]) < 2 and not lines[-1].isalnum():
        lines.pop()
        
    return "\n".join(lines)

def _typography_polish(text):
    """
    【排版润色】使数学/英语/语文内容符合标准排版格式
    """
    # 合并中文内部的碎空格（OCR 常见问题）
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    
    # 在中文字符与英文字母/数字之间自动插入一个空格（提升阅读体验）
    text = re.sub(r"([\u4e00-\u9fff])([A-Za-z0-9])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z0-9])([\u4e00-\u9fff])", r"\1 \2", text)
    
    # 修正数学表达式中多余的空格，例如 "x + y" 保持，但 "x+y" 不要变成 "x +y"
    text = re.sub(r"(\d)\s+([\.\d])", r"\1\2", text)
    
    return text.strip()

def extract_text_with_meta(image_path):
    if not os.path.exists(image_path):
        return {"text": "", "status": "failed"}

    try:
        # EasyOCR 执行
        results = _READER.readtext(image_path, detail=1)
        
        # 1. 布局分析：将离散块拼成有意义的行
        raw_text = _advanced_layout_engine(results)
        
        # 2. 通用清洗
        cleaned_text = _universal_cleaner(raw_text)
        
        # 3. 排版优化
        final_text = _typography_polish(cleaned_text)
        
        # 统计平均置信度
        avg_conf = mean([res[2] for res in results]) if results else 0.0
        
        # 判断题目类型（仅用于 meta 标记）
        if re.search(r"[A-D]\.", final_text):
            fmt = "multiple_choice"
        elif re.search(r"[+\-*/=√∑∫]", final_text):
            fmt = "math"
        else:
            fmt = "general"

        return {
            "text": final_text,
            "status": "ok" if len(final_text) > 5 else "empty",
            "confidence": round(avg_conf, 4),
            "format_type": fmt,
            "raw_word_count": len(final_text)
        }
    except Exception as e:
        return {"text": "", "status": "failed", "error": str(e)}

def extract_text(image_path):
    return extract_text_with_meta(image_path).get("text", "")