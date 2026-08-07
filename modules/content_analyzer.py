SECTION_LABELS = {
    "background": "研究背景",
    "methods": "研究方法",
    "results": "研究結果",
    "conclusion": "結論",
}


def analyze_content(user_inputs: dict) -> dict:
    text = user_inputs["text_content"]
    sections = []
    for key, label in SECTION_LABELS.items():
        content = text[key].strip()
        sections.append({
            "section": key,
            "label": label,
            "content": content,
            "character_count": len(content),
            "priority": "high" if key in {"results", "conclusion"} else "medium",
        })

    images = []
    for image in user_inputs.get("images", []):
        images.append({
            "filename": image["filename"],
            "type": image.get("type", "其他"),
            "description": image.get("description", ""),
            "purpose": image.get("purpose", "補充說明"),
            "suggested_section": _suggest_section(image.get("type", "")),
        })
    return {"sections": sections, "images": images, "warnings": [] if images else ["未上傳圖片，可先產生純文字版 Prompt。"]}


def _suggest_section(image_type: str) -> str:
    return {
        "實驗結果圖": "results",
        "數據圖表": "results",
        "流程圖": "methods",
        "設備照片": "methods",
    }.get(image_type, "background")

