from pathlib import Path

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
TEXT_MAX_CHARS = {
    "background": 3000,
    "methods": 4000,
    "results": 5000,
    "conclusion": 3000,
}


def validate_user_inputs(data: dict) -> list[str]:
    errors: list[str] = []
    requirements = data.get("requirements", {})
    text = data.get("text_content", {})

    required_requirements = {
        "topic": "主題",
        "audience": "報告對象",
        "language": "語言",
        "style": "簡報風格",
    }
    for key, label in required_requirements.items():
        if not str(requirements.get(key, "")).strip():
            errors.append(f"請填寫{label}。")

    pages = requirements.get("pages")
    if not isinstance(pages, int) or not 5 <= pages <= 50:
        errors.append("內容投影片頁數必須介於 5 到 50 頁，才能涵蓋 Outline、背景、方法、結果與結論；模板封面不計入。")

    minutes = requirements.get("duration_minutes")
    if not isinstance(minutes, int) or not 1 <= minutes <= 180:
        errors.append("報告時間必須介於 1 到 180 分鐘。")

    text_labels = {
        "background": "研究背景",
        "methods": "方法",
        "results": "結果",
        "conclusion": "結論",
    }
    for key, label in text_labels.items():
        content = str(text.get(key, "")).strip()
        if not content:
            errors.append(f"請填寫{label}。")
        elif len(content) > TEXT_MAX_CHARS[key]:
            errors.append(
                f"{label}不可超過 {TEXT_MAX_CHARS[key]:,} 字，"
                f"目前為 {len(content):,} 字。請保留與簡報直接相關的內容。"
            )

    for image in data.get("images", []):
        filename = str(image.get("filename", ""))
        if Path(filename).suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            errors.append(f"圖片格式不支援：{filename}")
        if not str(image.get("description", "")).strip():
            errors.append(f"請填寫圖片說明：{filename}")
    return errors


def validate_style_rules(style_rules: dict) -> list[str]:
    required = ["presentation_structure", "visual_layout", "color_palette", "typography"]
    return [f"style_rules.json 缺少必要欄位：{key}" for key in required if not style_rules.get(key)]

