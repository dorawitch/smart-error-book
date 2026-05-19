# -*- coding: utf-8 -*-
import sys
import shutil
import os

print("\n" + "="*40)
print("       OCR 环境深度诊断工具")
print("="*40)

# 1. 检查 Python 库
print("\n[1/4] 检查 Python 依赖库...")
try:
    import cv2
    print(f"  - OpenCV: 已安装 (版本: {cv2.__version__})")
except ImportError:
    print("  - [!!] 缺失 OpenCV (解决: pip install opencv-python)")

try:
    import numpy as np
    print(f"  - Numpy:  已安装 (版本: {np.__version__})")
except ImportError:
    print("  - [!!] 缺失 Numpy (解决: pip install numpy)")

try:
    import pytesseract
    from PIL import Image
    print("  - Pillow & Pytesseract: 已安装")
except ImportError:
    print("  - [!!] 缺失 pytesseract 或 Pillow (解决: pip install pytesseract Pillow)")

# 2. 检查配置文件
print("\n[2/4] 检查 config.py 配置...")
try:
    from config import TESSERACT_CMD, OCR_LANG
    print(f"  - OCR_LANG: {OCR_LANG}")
    print(f"  - TESSERACT_CMD (配置值): '{TESSERACT_CMD}'")
except Exception as e:
    print(f"  - [!!] 无法读取 config.py: {e}")
    TESSERACT_CMD = ""
    OCR_LANG = "chi_sim+eng"

# 3. 检查 Tesseract 引擎
print("\n[3/4] 检查 Tesseract 引擎...")
t_path = TESSERACT_CMD if TESSERACT_CMD else shutil.which('tesseract')

if t_path and os.path.exists(t_path):
    print(f"  - 引擎路径: {t_path}")
    try:
        pytesseract.pytesseract.tesseract_cmd = t_path
        ver = pytesseract.get_tesseract_version()
        print(f"  - 引擎版本: {ver}")
        
        langs = pytesseract.get_languages()
        print(f"  - 已安装语言包: {langs}")
        
        needed = [l.strip() for l in OCR_LANG.split('+')]
        for n in needed:
            if n in langs:
                print(f"    [OK] 语言包 '{n}' 已就绪")
            else:
                print(f"    [!!] 缺失语言包 '{n}' (需下载放入 tessdata 目录)")
    except Exception as e:
        print(f"  - [!!] 引擎调用报错: {e}")
else:
    print("  - [!!] 找不到 Tesseract 引擎！")
    print("    请确保已安装 Tesseract 软件，并在 config.py 中正确配置 TESSERACT_CMD 路径。")

# 4. 权限测试
print("\n[4/4] 权限与路径测试...")
test_dir = os.path.dirname(t_path) if t_path else "未知"
print(f"  - 引擎所在目录: {test_dir}")
if t_path and os.access(t_path, os.X_OK):
    print("  - [OK] Python 有权执行该引擎")
else:
    print("  - [!!] 警告: Python 可能没有执行 Tesseract 的权限")

print("\n" + "="*40)
print("诊断完成。请根据 [!!] 标记的内容进行修复。")
print("="*40 + "\n")