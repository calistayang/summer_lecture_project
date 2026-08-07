import json


def generate_final_prompt(user_inputs: dict, style_rules: dict, analysis: dict) -> str:
    req = user_inputs["requirements"]
    pages = req["pages"]
    sections = _allocate_sections(pages)
    images = analysis.get("images", [])
    lines = [
        "# 學術簡報製作指令",
        f"主題：{req['topic']}",
        f"對象：{req['audience']}｜時間：{req['duration_minutes']} 分鐘｜頁數：{pages}｜語言：{req['language']}",
        "不得捏造數據或引用；資料不足時標示「待使用者補充」。",
        "",
        "## 視覺規則",
        json.dumps(style_rules, ensure_ascii=False, indent=2),
        "",
        "## 逐頁規格",
    ]
    content_map = {item["section"]: item["content"] for item in analysis["sections"]}
    used_images: set[str] = set()
    for number, section in enumerate(sections, start=1):
        matched = [img for img in images if img["suggested_section"] == section]
        image = next((img for img in matched if img["filename"] not in used_images), None)
        if image:
            used_images.add(image["filename"])
        title, message, text = _slide_content(number, pages, section, req["topic"], content_map)
        lines.extend([
            f"### Slide Number: {number}",
            f"Title: {title}",
            f"Main Message: {message}",
            f"Layout: {'大圖搭配重點文字' if image else '標題加重點文字'}",
            f"Text: {text}",
            f"Image Filename: {image['filename'] if image else '無'}",
            "Data or Formula: 僅使用使用者提供的資料；沒有則標示無",
            "Citation: 使用者未提供來源時標示待補，不得自行虛構",
            f"Speaker Notes: 用約 {max(20, req['duration_minutes'] * 60 // pages)} 秒說明本頁核心訊息",
            "Design Instructions: 保持單一視覺焦點、足夠留白與可讀字級",
            "",
        ])
    unused = [img["filename"] for img in images if img["filename"] not in used_images]
    lines.append("Unused Images: " + (", ".join(unused) if unused else "無"))
    return "\n".join(lines)


def _allocate_sections(pages: int) -> list[str]:
    if pages == 3:
        return ["cover", "results", "conclusion"]
    middle = ["background", "methods", "results", "results"]
    while len(middle) < pages - 2:
        middle.insert(-1, "results")
    return ["cover", *middle[: pages - 2], "conclusion"]


def _slide_content(number: int, pages: int, section: str, topic: str, content: dict) -> tuple[str, str, str]:
    if section == "cover":
        return topic, "建立報告主題與研究範圍", f"{topic}"
    labels = {"background": "研究背景", "methods": "研究方法", "results": "研究結果", "conclusion": "結論"}
    label = labels[section]
    raw = content.get(section, "待使用者補充")
    suffix = f"（{number}/{pages}）" if section == "results" else ""
    return label + suffix, f"說明{label}的核心重點", raw

