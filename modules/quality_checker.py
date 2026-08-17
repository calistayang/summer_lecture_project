import re

REQUIRED_FIELDS = [
    "Title:", "Main Message:", "Layout:", "Text:", "Image Filename:",
    "Data or Formula:", "Citation:", "Design Instructions:",
]


def check_final_prompt(prompt: str, user_inputs: dict) -> dict:
    expected_pages = user_inputs["requirements"]["pages"]
    slides = re.findall(r"(?m)^### Slide Number: (\d+)$", prompt)
    errors = []
    if len(slides) != expected_pages:
        errors.append(f"頁數不符：預期 {expected_pages}，實際 {len(slides)}。")
    blocks = re.split(r"(?m)^### Slide Number: \d+$", prompt)[1:]
    for index, block in enumerate(blocks, start=1):
        for field in REQUIRED_FIELDS:
            if field not in block:
                errors.append(f"第 {index} 頁缺少 {field}")
    for label in ["研究背景", "研究方法", "研究結果", "結論"]:
        if label not in prompt:
            errors.append(f"最終 Prompt 未涵蓋：{label}")
    for rule in [
        "每張內容頁只能改寫模板原有 Title 2",
        "標題 top 超過 65.9 pt",
        "原生箭頭／connector",
        "真正 dashed outline",
        "每張結果頁至少將一個結論關鍵詞或關鍵數值加粗",
    ]:
        if rule not in prompt:
            errors.append(f"最終 Prompt 缺少硬性視覺規則：{rule}")
    return {"passed": not errors, "errors": errors, "slide_count": len(slides)}

