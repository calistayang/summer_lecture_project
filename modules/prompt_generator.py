"""產生給 NotebookLM 或其他簡報 AI 使用的逐頁 Prompt。"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict


SECTION_ORDER = ("background", "methods", "results", "conclusion")
LABELS_ZH = {
    "background": "研究背景",
    "methods": "研究方法",
    "results": "研究結果",
    "conclusion": "結論與未來工作",
}
LABELS_EN = {
    "background": "Background",
    "methods": "Methods",
    "results": "Results",
    "conclusion": "Conclusion & Future Work",
}

CITATION_RE = re.compile(
    r"https?://|\bdoi\s*:|\[[0-9]{1,3}\]|\bet\s+al\.|"
    r"(?:參考文獻|引用|來源|reference|citation)\s*[:：]",
    re.IGNORECASE,
)
DATA_RE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:%|nm|μm|um|mm|cm|V|mV|A|mA|μA|uA|Ω|ohm|Hz|kHz|MHz|GHz|K|°C|eV|W|mW)|"
    r"[A-Za-zα-ωΑ-Ω][A-Za-z0-9_]*\s*[=≈<>≤≥±]\s*[^，。；;\n]+",
    re.IGNORECASE,
)


def generate_final_prompt(user_inputs: dict, style_rules: dict, analysis: dict) -> str:
    """保留原函式介面，產生直接套用既有模板的簡報製作規格。"""

    requirements = user_inputs["requirements"]
    pages = requirements["pages"]
    if not isinstance(pages, int) or pages < 5:
        raise ValueError("內容投影片至少需要 5 頁，才能包含 Outline、背景、方法、結果與結論。")

    topic = _inline(requirements.get("topic")) or "待補"
    language = _inline(requirements.get("language")) or "繁體中文"
    duration = requirements.get("duration_minutes")
    duration = duration if isinstance(duration, int) and duration > 0 else 0

    sequence = _allocate_sections_for_analysis(pages, analysis)
    records = {item["section"]: item for item in analysis.get("sections", []) if item.get("section") in SECTION_ORDER}
    slides = _build_slides(sequence, records, topic, language)
    unused_images = _assign_images(slides, analysis.get("images", []))

    lines = [
        "# NanoSTLab 學術簡報製作 Prompt",
        "",
        "## 一、工作流程與最高優先規則",
        "1. 本網站只產生 final_prompt.txt；接收此 Prompt 的簡報 AI 必須直接交付可編輯的最終 .pptx，不可只回傳大綱、文字或程式碼。",
        "2. 開始製作前，確認已同時取得 final_prompt.txt、原始研究文件、Prompt 指定的研究圖片，以及 NanoSTLab PowerPoint 模板；缺少的素材標示「待補」，不得自行搜尋或捏造。",
        "3. 直接在使用者提供的 NanoSTLab PowerPoint 模板內建立簡報，不可先製作另一套獨立簡報再複製，也不可建立新的母片、主題或視覺系統。",
        "4. 必須保留模板母片、Logo、頂部標題區、底部實驗室識別與右下頁碼，不得重新設計、重畫、遮蓋、位移或替換。",
        "5. 封面完全不在本次製作範圍內：不得生成、重製、修改或填寫封面，也不得變更封面中的任何文字、圖片、位置或格式；模板原有封面必須保持原樣。第一張由 AI 製作的投影片必須是封面之後的 Outline，並作為內容第 1 頁。",
        "",
        "## 二、簡報需求與內容限制",
        f"- 主題：{topic}",
        "- 固定報告對象：實驗室教授與成員。",
        f"- 內容頁數：恰好 {pages} 頁，不包含模板封面。",
        f"- 報告時間：{duration if duration else '待補'} 分鐘。",
        f"- 語言：{language}；專有名詞、符號與公式可保留原文。",
        "- 固定採用 NanoSTLab 實驗室優良簡報風格，不提供其他風格選項。",
        "- 只能使用使用者提供的文字、文件、圖片、數據、公式與引用；不得用網路或模型記憶補寫研究事實。",
        "- 資料不足時標示「待補」；不得捏造數值、結果、公式、圖片檔名、引用或結論。",
        "",
        "## 三、NanoSTLab 視覺規則",
        *_style_lines(style_rules),
        "",
        "## 四、使用者圖片",
    ]

    images = analysis.get("images", [])
    if images:
        for image in images:
            lines.append(
                f"- {image.get('filename', '待補')}｜類型：{image.get('type', '其他')}｜"
                f"說明：{image.get('description') or '待補'}｜用途：{image.get('purpose') or '待補'}｜"
                f"建議章節：{LABELS_ZH.get(image.get('suggested_section'), '待補')}"
            )
    else:
        lines.append("- 無；不得自行生成、搜尋或加入圖片。")

    warnings = analysis.get("warnings", [])
    if warnings:
        lines.extend(["", "## 五、內容分析提醒", *(f"- {warning}" for warning in warnings)])

    lines.extend(["", "## 六、逐頁規格", "每頁只傳達一個 Main Message。Text 可精簡、翻譯或條列化，但不得改變原意。", ""])
    seconds = max(1, round(duration * 60 / pages)) if duration else 0

    for slide in slides:
        slide_images = slide["images"]
        names = ", ".join(image.get("filename", "待補") for image in slide_images) or "無"
        lines.extend([
            f"### Slide Number: {slide['number']}",
            f"Title: {slide['title']}",
            f"Main Message: {slide['main_message']}",
            f"Layout: {_layout(slide_images, style_rules)}",
            "Text:",
            _bullet_text(slide["text"]),
            f"Image Filename: {names}",
            f"Image Guidance: {_image_guidance(slide_images)}",
            f"Data or Formula: {_data_or_formula(slide)}",
            f"Citation: {_citation(slide)}",
            f"Speaker Notes: {_speaker_notes(slide, seconds)}",
            f"Design Instructions: 依「NanoSTLab 視覺規則」執行；{'以指定圖片為主要視覺焦點' if slide_images else '使用文字層級或使用者數據，不加入裝飾圖'}。",
            "",
        ])

    lines.append("Unused Images: " + (", ".join(unused_images) if unused_images else "無"))
    return "\n".join(lines)


def _allocate_sections(pages: int) -> list[str]:
    """保留原 helper 介面。"""

    return _allocate_sections_for_analysis(pages, {})


def _allocate_sections_for_analysis(pages: int, analysis: dict) -> list[str]:
    if not isinstance(pages, int) or pages < 5:
        raise ValueError("內容投影片至少需要 5 頁。")

    counts = {section: 1 for section in SECTION_ORDER}
    weights = {"background": 1.0, "methods": 1.4, "results": 2.5, "conclusion": 0.9}
    records = {item.get("section"): item for item in analysis.get("sections", [])}

    for section in SECTION_ORDER:
        record = records.get(section, {})
        suggested = record.get("suggested_slides", 1)
        characters = record.get("character_count", 0)
        images = record.get("image_count", 0)
        weights[section] += max(0, min(suggested if isinstance(suggested, int) else 1, 7) - 1) * 0.9
        weights[section] += min(characters / 800, 1.25) if isinstance(characters, int) else 0
        weights[section] += min(images, 6) * 0.3 if isinstance(images, int) else 0

    tie_order = {"results": 4, "methods": 3, "background": 2, "conclusion": 1}
    for _ in range(pages - 5):
        chosen = max(SECTION_ORDER, key=lambda key: (weights[key] / (counts[key] + 0.35), tie_order[key]))
        counts[chosen] += 1

    sequence = ["outline"]
    for section in SECTION_ORDER:
        sequence.extend([section] * counts[section])
    return sequence


def _build_slides(sequence: list[str], records: dict[str, dict], topic: str, language: str) -> list[dict]:
    counts = Counter(sequence)
    chunks = {
        section: _split_content(str(records.get(section, {}).get("content", "")), counts[section])
        for section in SECTION_ORDER
    }
    indexes = defaultdict(int)
    slides = []

    for number, section in enumerate(sequence, start=1):
        if section == "outline":
            text = "\n".join(_label(item, language) for item in SECTION_ORDER)
            title = "Outline"
            message = "依序預告研究背景、研究方法、研究結果、結論與未來工作"
            part, total = 1, 1
        else:
            part = indexes[section] + 1
            total = counts[section]
            text = chunks[section][indexes[section]]
            indexes[section] += 1
            title = _title(section, text, part, total, language)
            message = _message(section, text, language)

        slides.append({
            "number": number,
            "section": section,
            "title": title,
            "main_message": message,
            "text": text,
            "part": part,
            "total": total,
            "images": [],
        })
    return slides


def _assign_images(slides: list[dict], images: list[dict]) -> list[str]:
    used = set()
    ordered = sorted(enumerate(images), key=lambda item: (item[1].get("original_order", item[0] + 1), item[0]))

    for index, image in ordered:
        section = image.get("suggested_section", "background")
        candidates = [slide for slide in slides if slide["section"] == section and len(slide["images"]) < 4]
        if not candidates:
            candidates = [slide for slide in slides if slide["section"] != "outline" and len(slide["images"]) < 4]
        if not candidates:
            continue

        image_tokens = _tokens(" ".join(str(image.get(key, "")) for key in ("type", "description", "purpose")))
        selected = max(
            candidates,
            key=lambda slide: (len(image_tokens & _tokens(slide["text"])), -len(slide["images"]), -slide["number"]),
        )
        selected["images"].append(image)
        used.add(index)

    return [str(image.get("filename", "待補")) for index, image in enumerate(images) if index not in used]


def _slide_content(number: int, pages: int, section: str, topic: str, slide_text: str) -> tuple[str, str, str]:
    """保留原 helper 介面。"""

    if section == "outline":
        return "Outline", "說明本次報告的研究敘事與主要章節", slide_text
    text = slide_text or "待補"
    return LABELS_ZH.get(section, section), _message(section, text, "繁體中文"), text


def _split_content(content: str, count: int) -> list[str]:
    """依原始順序將內容平均切成連續區塊。"""

    if count <= 0:
        return []
    units = _units(content)
    if not units:
        return ["待補"] * count
    if count == 1:
        return ["\n".join(units)]

    while len(units) < count:
        index = max(range(len(units)), key=lambda item: len(units[item]))
        text = units[index]
        if len(text) < 40:
            break
        middle = len(text) // 2
        positions = [match.end() for match in re.finditer(r"[，,：:；;\s]", text)]
        split_at = min(positions, key=lambda value: abs(value - middle)) if positions else middle
        if not 0 < split_at < len(text):
            break
        units[index:index + 1] = [text[:split_at].strip(), text[split_at:].strip()]

    if len(units) < count:
        units.extend(["待補"] * (count - len(units)))

    chunks, cursor = [], 0
    for group in range(count):
        groups_left = count - group
        units_left = len(units) - cursor
        if groups_left == 1:
            selected = units[cursor:]
            cursor = len(units)
        elif units_left <= groups_left:
            selected = [units[cursor]]
            cursor += 1
        else:
            target = math.ceil(sum(len(unit) for unit in units[cursor:]) / groups_left)
            selected, length = [], 0
            max_take = units_left - groups_left + 1
            while len(selected) < max_take:
                next_unit = units[cursor]
                if selected and length + len(next_unit) > target:
                    break
                selected.append(next_unit)
                length += len(next_unit)
                cursor += 1
        chunks.append("\n".join(selected).strip() or "待補")
    return chunks


def _style_lines(style_rules: dict) -> list[str]:
    """只輸出一次必要規則，避免再附完整 JSON 造成重複。"""

    typography = _mapping(style_rules.get("typography"))
    colors = _mapping(style_rules.get("color_palette"))
    layout_value = style_rules.get("visual_layout")
    layout = _mapping(layout_value)
    size = _mapping(style_rules.get("slide_size"))
    density = _mapping(style_rules.get("content_density"))
    image_layout = _mapping(style_rules.get("image_layout"))

    patterns = layout.get("preferred_patterns")
    if not isinstance(patterns, list):
        patterns = [layout_value] if isinstance(layout_value, str) else ["大圖搭配精簡標註", "左摘要、右圖表", "左右比較"]
    avoid = layout.get("avoid", ["大段文字", "過長條列", "過度裝飾"])
    if isinstance(avoid, str):
        avoid = [avoid]

    title_size = typography.get("preferred_title_range_pt", typography.get("title_pt", "48–53"))
    return [
        f"- 版面：{size.get('aspect_ratio', '16:9')}、白底；不可沿用舊簡報的 4:3 比例。",
        f"- 字級：標題約 {title_size} pt，主文約 {typography.get('body_pt', '24–27')} pt且不得低於 {typography.get('minimum_body_pt', 21)} pt，引用約 {typography.get('reference_pt', '10–11')} pt。放不下時精簡或拆頁，不可縮字硬塞。",
        f"- 色彩：技術重點使用藍色 {colors.get('technical_emphasis_blue', '#0000FF')}；差異或警告使用紅色 {colors.get('warning_red', '#FF0000')}；正文使用黑色。",
        "- 優先版型：" + "、".join(str(item) for item in patterns) + "。",
        "- 避免：" + "、".join(str(item) for item in avoid) + "。",
        f"- 內容密度：{density.get('rule', '每頁只傳達一個主要訊息，保留 15%–25% 留白。')}",
        f"- 圖片：{image_layout.get('rule', '只使用使用者提供的精確檔名；不得拉伸或裁掉座標軸、圖例與重要標示。')}",
        "- 引用置於頁尾正上方，使用深灰小字，只列出使用者提供且與該頁直接相關的來源。",
        "- 若提供參考簡報，只沿用視覺層級、配色與版面節奏，不複製其研究內容、圖片、數據或引用。",
    ]


def _layout(images: list[dict], style_rules: dict) -> str:
    rules = _mapping(style_rules.get("image_layout"))
    count = len(images)
    if count == 0:
        return "標題＋2–4 個精簡重點，保留 15%–25% 留白"
    keys = {1: "one_image", 2: "two_images", 3: "three_images", 4: "four_images"}
    defaults = {
        1: "左側摘要、右側單一主要圖片",
        2: "兩張圖片左右並排並保持一致尺寸",
        3: "三欄或一主兩輔",
        4: "2×2 圖片網格",
    }
    return str(rules.get(keys[min(count, 4)], defaults[min(count, 4)]))


def _image_guidance(images: list[dict]) -> str:
    if not images:
        return "無"
    return "｜".join(
        f"{image.get('filename', '待補')}：{image.get('description') or '待補'}；用途：{image.get('purpose') or '待補'}"
        for image in images
    )


def _title(section: str, text: str, part: int, total: int, language: str) -> str:
    label = _label(section, language)
    first = _first(text)
    if first == "待補":
        title = label
    else:
        phrase = re.split(r"[，,：:；;。.!?！？]", first, maxsplit=1)[0].strip()
        phrase = " ".join(phrase.split()[:8]) if _english(language) else phrase[:16]
        title = phrase if phrase.lower().startswith(label.lower()) else f"{label}{': ' if _english(language) else '：'}{phrase}"
    return f"{title}（{part}/{total}）" if total > 1 else title


def _message(section: str, text: str, language: str) -> str:
    first = _first(text)
    if first == "待補":
        return f"{_label(section, language)}所需資料尚未提供，保留「待補」"
    return first if len(first) <= 100 else first[:100].rstrip("，,；; ") + "…"


def _bullet_text(text: str) -> str:
    units = _units(text) or ["待補"]
    return "\n".join(f"• {unit}" for unit in units)


def _data_or_formula(slide: dict) -> str:
    if slide["section"] == "outline":
        return "無"
    matches = [unit for unit in _units(slide["text"]) if DATA_RE.search(unit)]
    return "｜".join(matches) if matches else "待補（若本頁需要數據或公式，不得自行補寫）"


def _citation(slide: dict) -> str:
    if slide["section"] == "outline":
        return "無"
    matches = [unit for unit in _units(slide["text"]) if CITATION_RE.search(unit)]
    return "｜".join(matches) if matches else "待補（不得搜尋或虛構）"


def _speaker_notes(slide: dict, seconds: int) -> str:
    time_text = f"約 {seconds} 秒" if seconds else "依總時間平均分配"
    if slide["section"] == "outline":
        return f"用 {time_text} 說明章節順序"
    relation = "並解釋指定圖片與結論的關係" if slide["images"] else "並說明本頁重點的邏輯"
    return f"用 {time_text}、約 2–5 句說明 Main Message，{relation}，最後加一句自然轉場；不得加入來源外主張"


def _label(section: str, language: str) -> str:
    if _english(language):
        return LABELS_EN[section]
    if "雙語" in language:
        return f"{LABELS_ZH[section]} / {LABELS_EN[section]}"
    return LABELS_ZH[section]


def _english(language: str) -> bool:
    return language.strip().lower() in {"英文", "english", "en"}


def _units(content: object) -> list[str]:
    text = str(content or "").replace("\r", "")
    units = []
    for paragraph in text.splitlines():
        paragraph = re.sub(r"^\s*(?:[-*•]|\d+[.)、])\s*", "", paragraph.strip())
        units.extend(
            part.strip()
            for part in re.split(r"(?<=[。！？!?])\s*|(?<=[.;])\s+(?=[A-Z0-9])|(?<=[；;])\s*", paragraph)
            if part.strip()
        )
    return units


def _first(text: str) -> str:
    units = _units(text)
    return units[0] if units else "待補"


def _tokens(content: object) -> set[str]:
    stop_words = {"the", "and", "for", "with", "from", "this", "that", "image", "figure"}
    return {token for token in re.findall(r"[a-z][a-z0-9_-]{2,}|\d+(?:\.\d+)?", str(content).lower()) if token not in stop_words}


def _inline(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _mapping(value: object) -> dict:
    return value if isinstance(value, dict) else {}
