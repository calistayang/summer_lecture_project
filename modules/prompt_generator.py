from collections import Counter, defaultdict


SECTION_LABELS = {
    "background": "研究背景",
    "methods": "研究方法",
    "results": "研究結果",
    "conclusion": "結論與未來工作",
}


def generate_final_prompt(user_inputs: dict, style_rules: dict, analysis: dict) -> str:
    req = user_inputs["requirements"]
    pages = req["pages"]
    sections = _allocate_sections(pages)
    images = analysis.get("images", [])
    lines = [
        "# 學術簡報製作指令",
        f"主題：{req['topic']}",
        f"對象：{req['audience']}｜時間：{req['duration_minutes']} 分鐘｜內容頁數：{pages}（不含模板封面）｜語言：{req['language']}",
        "請先完整閱讀與本 Prompt 一起提供的原始研究報告；報告是內容、數據、公式與引用的主要依據，下方逐頁文字是規劃提示。",
        "請嚴格依照本 Prompt 的逐頁規格，使用原始研究報告內與各頁內容直接相關的 Figure、Table 與圖片；不得自行上網搜尋、生成或替換研究圖片。",
        "對每張上傳圖片先自行辨識其圖說、座標軸、圖例、標籤、比較關係與科學意義，再決定最適合的投影片、圖片順序及必要短句；使用者不需要另外提供圖片說明。逐頁 Image Filename 是初步配置，若與圖片實際內容不符，必須移至正確頁面，不可硬套。",
        "請直接使用與本 Prompt 一起提供的實驗室 PowerPoint 模板作為唯一版型來源，在模板檔中新增或複製內容頁，不得另外設計一套相似模板。",
        "保留模板既有封面、母片、Logo、頁首、頁尾、固定圖案與頁碼位置；內容頁數不包含封面，第一張內容頁必須是 Outline。",
        "每張內容頁都必須套用模板既有的內容版面，所有正文、圖片、表格與引用都不可遮住模板的固定元素。",
        "最終請輸出已套用實驗室模板的可編輯 .pptx；文字、圖片、表格與圖表必須保持可編輯，不得把整頁轉成單一圖片。",
        "為縮短生成時間：不要製作講者備註、不要重建模板元素、不要產生裝飾性圖片，只完成必要內容頁，不需要做封面頁。",
        "不得捏造數據或引用；資料不足時標示「待使用者補充」。",
        "",
        "## 精簡視覺規則",
        *_visual_rules_summary(style_rules),
        "",
        "## 逐頁規格",
    ]
    content_map = {item["section"]: item["content"] for item in analysis["sections"]}
    section_counts = Counter(sections)

    section_chunks = {
        section: _split_content(content_map.get(section, ""), count)
        for section, count in section_counts.items()
        if not section.startswith("transition:")
    }

    section_indexes = defaultdict(int)

    used_images: set[str] = set()
    for number, section in enumerate(sections, start=1):
        matched = [img for img in images if img["suggested_section"] == section]
        image = next((img for img in matched if img["filename"] not in used_images), None)
        if image:
            used_images.add(image["filename"])
        if section.startswith("transition:"):
            slide_text = "研究背景\n研究方法\n研究結果\n結論與未來工作"
        else:
            index = section_indexes[section]
            slide_text = section_chunks[section][index]
            section_indexes[section] += 1

        title, message, text = _slide_content(
            number, pages, section, req["topic"], slide_text
        )
        is_transition = section.startswith("transition:")
        layout = "章節導覽轉場" if is_transition else ("大圖搭配重點文字" if image else "標題加重點文字")
        image_name = image["filename"] if image else "無（可使用原始研究報告內與本頁直接相關的圖）"
        design = _design_instructions(section, bool(image))
        lines.extend([
            f"### Slide Number: {number}",
            f"Title: {title}",
            f"Main Message: {message}",
            f"Layout: {layout}",
            f"Text: {text}",
            f"Image Filename: {image_name if not is_transition else '無'}",
            "Data or Formula: 僅使用使用者提供的資料；沒有則標示無",
            "Citation: 使用者未提供來源時標示待補，不得自行虛構",
            f"Design Instructions: {design}",
            "",
        ])
    unused = [img["filename"] for img in images if img["filename"] not in used_images]
    lines.append("Unused Images: " + (", ".join(unused) if unused else "無"))
    return "\n".join(lines)


def _allocate_sections(pages: int) -> list[str]:
    sections = [
        "transition:background", "background",
        "transition:methods", "methods",
        "transition:results", "results",
        "transition:conclusion", "conclusion",
    ]
    while len(sections) < pages:
        sections.insert(-2, "results")
    return sections[:pages]


def _slide_content(
    number: int,
    pages: int,
    section: str,
    topic: str,
    slide_text: str,
) -> tuple[str, str, str]:
    if section.startswith("transition:"):
        active = section.split(":", 1)[1]
        label = SECTION_LABELS[active]
        return "Outline", f"即將進入：{label}", slide_text

    label = SECTION_LABELS[section]
    text = slide_text or "待使用者補充"
    suffix = f"（{number}/{pages}）" if section == "results" else ""

    return label + suffix, f"說明{label}的核心重點", text


def _visual_rules_summary(style_rules: dict) -> list[str]:
    typography = style_rules.get("typography", {})
    colors = style_rules.get("color_palette", {})
    if not isinstance(typography, dict):
        typography = {}
    if not isinstance(colors, dict):
        colors = {}
    return [
        "- 直接沿用提供的 PowerPoint 模板母片與既有版面，不重畫頁首頁尾。",
        f"- 標題約 {typography.get('title_pt', 48)} pt；主文約 {typography.get('body_pt', 24)} pt；引用約 {typography.get('reference_pt', '10–11')} pt。",
        f"- 技術重點使用 {colors.get('technical_emphasis_blue', '#0000FF')}；差異或警告使用 {colors.get('warning_red', '#FF0000')}；不可過量使用。",
        "- 每段開始前插入同版章節導覽頁：目前段落黑色 #000000，其餘段落淺灰 #BFBFBF；所有文字位置固定不變。",
        "- 圖像優先：一頁一個結論、一張主圖；正文不超過 60 個中文字或 35 個英文單字，最多 3 個短標籤。",
        "- 流程圖依閱讀順序排列，箭頭只表示時間、流程或因果，統一由左至右或由上至下，不可穿過圖片或文字。",
        "- 標籤放在圖片留白或圖片外側，不可遮住座標軸、圖例、數據、元件結構或重要特徵。",
        "- 需要強調時只框一個重點區域，使用細虛線矩形與一個短標籤，不得使用大片裝飾框。",
        "- 多圖比較必須等高、對齊、間距一致；兩圖左右比較，三圖用水平步驟或一主兩輔。",
    ]


def _design_instructions(section: str, has_uploaded_image: bool) -> str:
    if section.startswith("transition:"):
        active = section.split(":", 1)[1]
        active_label = SECTION_LABELS[active]
        return (
            "複製同一張 Outline 版面並保持四段文字位置完全一致；"
            "四個主章節必須放在同一個內容區中，由上往下單欄排列、靠左對齊並維持一致的垂直間距；"
            "不得改成橫向並排、卡片、圓圈、流程箭頭或分散到多欄；"
            f"僅「{active_label}」使用黑色 #000000 與粗體，其餘使用淺灰 #BFBFBF；"
            "不放圖片、段落說明或額外裝飾。"
        )
    image_source = "優先使用指定圖片" if has_uploaded_image else "優先從原始研究報告選取與本頁結論直接相關的圖"
    return (
        f"{image_source}作為主視覺；先決定圖片閱讀順序，再加入必要箭頭。"
        "可見正文不超過 60 個中文字或 35 個英文單字，最多 3 個短標籤；"
        "文字放在圖片留白或外側，不遮住科學資訊；只對一個關鍵區域使用細虛線框。"
    )

def _split_content(content: str, count: int) -> list[str]:
    if count <= 1:
        return [content]

    sentences = [
        sentence.strip()
        for sentence in content.replace("。", "。\n").splitlines()
        if sentence.strip()
    ]

    chunks = [""] * count
    for index, sentence in enumerate(sentences):
        target = index % count
        chunks[target] = f"{chunks[target]}{sentence}".strip()

    return [chunk or "待使用者補充" for chunk in chunks]
