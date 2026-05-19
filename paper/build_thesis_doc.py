from __future__ import annotations

from pathlib import Path

from win32com.client import Dispatch, constants


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = PROJECT_ROOT / "paper"
SOURCE_PATH = PAPER_DIR / "thesis_source.md"
OUTPUT_PATH = PAPER_DIR / (
    "\u57fa\u4e8ePython\u7684\u667a\u80fd\u9519\u9898\u672c\u7cfb\u7edf\u8bbe\u8ba1\u4e0e\u5b9e\u73b0_"
    "\u6bd5\u4e1a\u8bba\u6587.docx"
)

TITLE = "\u57fa\u4e8e Python \u7684\u667a\u80fd\u9519\u9898\u672c\u7cfb\u7edf\u8bbe\u8ba1\u4e0e\u5b9e\u73b0"
META_LINES = [
    "\u5b66\u9662\uff1a\u5f85\u586b\u5199",
    "\u4e13\u4e1a\uff1a\u5f85\u586b\u5199",
    "\u5b66\u751f\u59d3\u540d\uff1a\u5f85\u586b\u5199",
    "\u5b66\u53f7\uff1a\u5f85\u586b\u5199",
    "\u6307\u5bfc\u6559\u5e08\uff1a\u5f85\u586b\u5199",
    "\u5b8c\u6210\u65e5\u671f\uff1a2026\u5e744\u6708",
]

FONT_SONG = "\u5b8b\u4f53"
FONT_HEI = "\u9ed1\u4f53"
DOC_TITLE = "\u5e7f\u4e1c\u5de5\u4e1a\u5927\u5b66\u672c\u79d1\u751f\u6bd5\u4e1a\u8bbe\u8ba1\uff08\u8bba\u6587\uff09"
TOC_TITLE = "\u76ee\u5f55"
CH_ABSTRACT = "\u4e2d\u6587\u6458\u8981"
EN_ABSTRACT = "\u82f1\u6587\u6458\u8981"
FIRST_CHAPTER = "\u7b2c\u4e00\u7ae0"
PAPER_SIZE_A4 = 7
CM_TO_POINT = 28.35
ALIGN_LEFT = 0
ALIGN_CENTER = 1
ALIGN_JUSTIFY = 3
LINE_SINGLE = 0
LINE_EXACTLY = 4
PAGE_BREAK = 7
FOOTER_PRIMARY = 1
PAGE_NUMBER_CENTER = 1
STYLE_HEADING_1 = -2
STYLE_HEADING_2 = -3
STYLE_HEADING_3 = -4


def _set_font(range_obj, font_name: str, size: float, bold: bool = False) -> None:
    range_obj.Font.NameFarEast = font_name
    range_obj.Font.Name = font_name
    range_obj.Font.Size = size
    range_obj.Font.Bold = int(bold)


def _add_paragraph(doc, text: str = ""):
    paragraph = doc.Paragraphs.Add()
    if text:
        paragraph.Range.Text = text
    return paragraph


def _apply_body_style(paragraph) -> None:
    _set_font(paragraph.Range, FONT_SONG, 10.5, False)
    paragraph.Alignment = ALIGN_JUSTIFY
    paragraph.FirstLineIndent = 21
    paragraph.LineSpacingRule = LINE_EXACTLY
    paragraph.LineSpacing = 20
    paragraph.SpaceAfter = 0


def _apply_heading(doc, paragraph, level: int) -> None:
    if level == 2:
        paragraph.Range.Style = STYLE_HEADING_1
        _set_font(paragraph.Range, FONT_HEI, 16, True)
    elif level == 3:
        paragraph.Range.Style = STYLE_HEADING_2
        _set_font(paragraph.Range, FONT_HEI, 14, True)
    else:
        paragraph.Range.Style = STYLE_HEADING_3
        _set_font(paragraph.Range, FONT_HEI, 12, True)
    paragraph.Alignment = ALIGN_LEFT
    paragraph.FirstLineIndent = 0
    paragraph.LineSpacingRule = LINE_SINGLE


def _parse_markdown_sections(text: str):
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            yield ("blank", "")
        elif line.startswith("### "):
            yield ("h3", line[4:].strip())
        elif line.startswith("## "):
            yield ("h2", line[3:].strip())
        elif line.startswith("# "):
            yield ("h1", line[2:].strip())
        else:
            yield ("p", line)


if __name__ == "__main__":
    markdown = SOURCE_PATH.read_text(encoding="utf-8")

    word = Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0

    doc = word.Documents.Add()
    doc.PageSetup.PaperSize = PAPER_SIZE_A4
    doc.PageSetup.TopMargin = 2.5 * CM_TO_POINT
    doc.PageSetup.BottomMargin = 2.2 * CM_TO_POINT
    doc.PageSetup.LeftMargin = 2.8 * CM_TO_POINT
    doc.PageSetup.RightMargin = 2.2 * CM_TO_POINT

    title_para = _add_paragraph(doc, DOC_TITLE)
    title_para.Alignment = ALIGN_CENTER
    _set_font(title_para.Range, FONT_HEI, 18, True)
    title_para.SpaceAfter = 18

    sub_para = _add_paragraph(doc, TITLE)
    sub_para.Alignment = ALIGN_CENTER
    _set_font(sub_para.Range, FONT_SONG, 22, True)
    sub_para.SpaceAfter = 30

    for line in META_LINES:
        meta_para = _add_paragraph(doc, line)
        meta_para.Alignment = ALIGN_CENTER
        _set_font(meta_para.Range, FONT_SONG, 14, False)
        meta_para.SpaceAfter = 8

    doc.Paragraphs.Add().Range.InsertBreak(PAGE_BREAK)

    toc_inserted = False
    for kind, value in _parse_markdown_sections(markdown):
        if kind == "h1":
            continue

        if not toc_inserted and kind == "h2" and value.startswith(FIRST_CHAPTER):
            toc_title = _add_paragraph(doc, TOC_TITLE)
            toc_title.Alignment = ALIGN_CENTER
            _set_font(toc_title.Range, FONT_HEI, 16, True)
            toc_title.SpaceAfter = 12
            toc_range = _add_paragraph(doc).Range
            doc.TablesOfContents.Add(
                Range=toc_range,
                UseHeadingStyles=True,
                UpperHeadingLevel=1,
                LowerHeadingLevel=2,
                RightAlignPageNumbers=True,
                IncludePageNumbers=True,
            )
            doc.Paragraphs.Add().Range.InsertBreak(PAGE_BREAK)
            toc_inserted = True

        if kind == "blank":
            continue

        if kind == "h2":
            para = _add_paragraph(doc, value)
            _apply_heading(doc, para, 2)
            if value in {CH_ABSTRACT, EN_ABSTRACT}:
                para.Alignment = ALIGN_CENTER
        elif kind == "h3":
            para = _add_paragraph(doc, value)
            _apply_heading(doc, para, 3)
        else:
            para = _add_paragraph(doc, value)
            _apply_body_style(para)

    for toc in doc.TablesOfContents:
        toc.Update()

    for section in doc.Sections:
        footer = section.Footers(FOOTER_PRIMARY)
        footer.PageNumbers.Add(PageNumberAlignment=PAGE_NUMBER_CENTER)

    doc.SaveAs(str(OUTPUT_PATH))
    doc.Close(False)
    word.Quit()

    print(str(OUTPUT_PATH))
