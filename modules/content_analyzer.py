"""將使用者提供的研究素材整理成可供簡報分頁使用的結構。"""

from __future__ import annotations

import math
import re
from collections import Counter


SECTION_LABELS = {
    "background": "研究背景",
    "methods": "研究方法",
    "results": "研究結果",
    "conclusion": "結論",
}

IMAGE_TYPE_SECTIONS = {
    "實驗結果圖": "results",
    "數據圖表": "results",
    "流程圖": "methods",
    "設備照片": "methods",
    "元件照片": "methods",
    "結構圖": "methods",
    "概念圖": "background",
    "文獻圖": "background",
    "總結圖": "conclusion",
    "result": "results",
    "chart": "results",
    "plot": "results",
    "flowchart": "methods",
    "equipment": "methods",
    "schematic": "methods",
}

SECTION_KEYWORDS = {
    "background": ("背景", "動機", "問題", "挑戰", "文獻", "原理", "概念", "background", "motivation", "theory"),
    "methods": ("方法", "流程", "步驟", "結構", "設備", "製程", "量測", "模擬", "method", "process", "setup", "device", "measurement"),
    "results": ("結果", "數據", "曲線", "比較", "趨勢", "效能", "誤差", "result", "data", "curve", "plot", "performance"),
    "conclusion": ("結論", "總結", "貢獻", "限制", "未來", "展望", "conclusion", "summary", "future", "limitation"),
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


def analyze_content(user_inputs: dict) -> dict:
    """保留原函式介面，回傳 sections、images 與 warnings。"""

    text_content = user_inputs["text_content"]
    sections = []
    warnings = []

    for key, label in SECTION_LABELS.items():
        content = _normalize(text_content.get(key, ""))
        units = _split_units(content)
        section = {
            "section": key,
            "label": label,
            "content": content,
            "character_count": len(content),
            "word_count": len(re.findall(r"[A-Za-z0-9]+|[\u3400-\u9fff]", content)),
            "content_units": units,
            "key_points": units[:8],
            "summary": " ".join(units[:2]) if units else "待補",
            "priority": "high" if key in {"results", "conclusion"} else "medium",
            "suggested_slides": _estimate_slides(content, units, key),
            "has_explicit_data_or_formula": bool(DATA_RE.search(content)),
            "has_explicit_citation": bool(CITATION_RE.search(content)),
            "image_count": 0,
        }
        sections.append(section)

        if len(content) < 20:
            warnings.append(f"{label}內容較短，建議補充資料。不足處將標示「待補」。")
        if len(content) > 1000:
            warnings.append(f"{label}內容較長，產生簡報時將拆分重點並維持原始順序。")

    images = []
    for order, raw_image in enumerate(user_inputs.get("images", []), start=1):
        image_type = _inline(raw_image.get("type", "其他")) or "其他"
        description = _inline(raw_image.get("description", ""))
        purpose = _inline(raw_image.get("purpose", "補充說明")) or "補充說明"
        section, reason = _match_image(image_type, description, purpose, sections)
        images.append({
            "filename": str(raw_image.get("filename", "")).strip(),
            "type": image_type,
            "description": description,
            "purpose": purpose,
            "suggested_section": section,
            "match_reason": reason,
            "original_order": order,
        })

    image_counts = Counter(image["suggested_section"] for image in images)
    for section in sections:
        count = image_counts.get(section["section"], 0)
        section["image_count"] = count
        section["suggested_slides"] = max(section["suggested_slides"], math.ceil(count / 2) or 1)

    pages = user_inputs["requirements"].get("pages", 0)
    available_pages = max(pages - 2, 0) if isinstance(pages, int) else 0
    if len(images) > available_pages:
        warnings.append("圖片數量較多，部分頁面需使用多圖配置；放不下的圖片應列為未使用。")
    if not images:
        warnings.append("未上傳圖片，可先產生純文字版 Prompt。不得由 AI 自行補圖。")
    if not any(section["has_explicit_citation"] for section in sections):
        warnings.append("未偵測到明確引用來源，各頁 Citation 應標示「待補」，不得虛構。")

    return {"sections": sections, "images": images, "warnings": warnings}


def _suggest_section(image_type: str) -> str:
    """保留原 helper 介面。"""

    return IMAGE_TYPE_SECTIONS.get(str(image_type).strip().lower(), "background")


def _match_image(image_type: str, description: str, purpose: str, sections: list[dict]) -> tuple[str, str]:
    scores = Counter()
    reasons = {key: [] for key in SECTION_LABELS}
    normalized_type = image_type.lower()

    if normalized_type in IMAGE_TYPE_SECTIONS:
        section = IMAGE_TYPE_SECTIONS[normalized_type]
        scores[section] += 5
        reasons[section].append(f"類型：{image_type}")

    metadata = f"{image_type} {description} {purpose}".lower()
    for section, keywords in SECTION_KEYWORDS.items():
        matched = [word for word in keywords if word.lower() in metadata]
        if matched:
            scores[section] += min(len(matched), 3) * 2
            reasons[section].append("關鍵詞：" + "、".join(matched[:3]))

    metadata_tokens = _tokens(metadata)
    for item in sections:
        overlap = metadata_tokens & _tokens(item["content"])
        if overlap:
            scores[item["section"]] += min(len(overlap), 3)

    if not scores:
        return "background", "未找到明確線索，暫配研究背景"

    tie_order = {"results": 4, "methods": 3, "background": 2, "conclusion": 1}
    best = max(scores, key=lambda key: (scores[key], tie_order[key]))
    return best, "；".join(reasons[best]) or "與章節文字相符"


def _normalize(value: object) -> str:
    lines = [re.sub(r"[ \t\u3000]+", " ", line).strip() for line in str(value or "").replace("\r", "").split("\n")]
    return "\n".join(line for line in lines if line)


def _inline(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _split_units(content: str) -> list[str]:
    units = []
    for paragraph in content.splitlines():
        paragraph = re.sub(r"^\s*(?:[-*•]|\d+[.)、])\s*", "", paragraph)
        parts = re.split(r"(?<=[。！？!?])\s*|(?<=[.;])\s+(?=[A-Z0-9])|(?<=[；;])\s*", paragraph)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            units.extend(part[index:index + 220] for index in range(0, len(part), 220))
    return units


def _estimate_slides(content: str, units: list[str], section: str) -> int:
    estimate = max(1, math.ceil(len(content) / 260), math.ceil(max(len(units), 1) / 4))
    if section == "results" and (len(content) > 180 or len(units) > 3):
        estimate = max(2, estimate)
    return min(estimate, 12)


def _tokens(content: str) -> set[str]:
    stop_words = {"the", "and", "for", "with", "from", "this", "that", "image", "figure"}
    return {token for token in re.findall(r"[a-z][a-z0-9_-]{2,}|\d+(?:\.\d+)?", content.lower()) if token not in stop_words}
