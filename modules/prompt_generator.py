from collections import Counter, defaultdict
import re


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
        "",
        *_execution_contract(req, images),
        "",
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
    outline_text = _derive_outline_text(content_map)
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
            slide_text = outline_text
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
    lines.extend([
        "",
        "## 交付前硬性 QA（任一項失敗就必須修正，不得交付）",
        "1. 逐頁檢查標題物件：每張內容頁只能改寫模板原有 Title 2；標題必須位於頂部藍黃分隔線之上，沿用模板座標與尺寸。任何標題 top 超過 65.9 pt、掉入內容區、另建標題文字框或壓在線條下方，都判定失敗。",
        "2. 檢查原生 PPTX 物件：只要頁面包含流程、因果、時間順序、before/after 或多圖閱讀順序，就必須至少有一個可編輯的原生箭頭／connector；不可只用文字箭頭符號代替。整份簡報若有多圖頁但箭頭端點數為 0，判定失敗。",
        "3. 至少一張關鍵結果頁必須使用可編輯的細虛線矩形框，透明填滿，只框住決定性圖區並搭配短標籤；結果頁達 3 張以上但整份簡報沒有真正 dashed outline，判定失敗。",
        "4. 每張結果頁至少將一個結論關鍵詞或關鍵數值加粗，必要時再使用技術藍或警示紅；不可整段全粗、整頁同色，也不可只改標題顏色。",
        "5. 箭頭、虛線框、粗體與重點色必須服務科學敘事：先指定閱讀起點，再指出順序／差異，最後落到結論；不得當成裝飾。",
        "6. 檢查所有可見正文與一般項目文字：不得小於 24 pt。若 24 pt 放不下，必須刪減文字、放大主圖或拆頁，禁止縮字；只有圖片內原始標籤、caption 16–20 pt 與 citation 12–14 pt 可以小於 24 pt。",
        "7. 檢查項目符號：單句結論與圖旁短標籤不得加 bullet；同一層級若使用清單，所有同層項目必須使用 PowerPoint 原生且相同的 bullet、縮排與間距。禁止直接輸入 □、■、▪、• 字元冒充項目符號。",
        "8. Outline 與四張章節導覽頁必須使用同一份兩層階層：四個主章節下各有 1–3 個從研究內容推導的子標題；若只剩四大章節而沒有子標題，判定失敗。",
        "9. 虛線框只可出現在確實存在局部關鍵差異的 1–3 張結果頁，每頁最多一個。矩形四邊必須貼合實際圖區或 panel，與目標約留 4–8 pt；不得框大片空白、跨越無關 panels、漂浮在圖片外或為了達成數量而硬加。若無局部 ROI，該頁不要使用虛線框。",
    ])
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
    title = _derive_slide_title(text, f"{label}：待補子題")

    return title, f"以「{title}」作為本頁唯一結論，內容必須支持此判斷", text


def _derive_slide_title(text: str, fallback: str) -> str:
    """Create a concise content-specific title instead of repeating a section name."""
    cleaned = re.sub(r"(?i)^\s*(?:figure|fig\.?|圖)\s*\d+[A-Za-z]?\s*[：:]?\s*", "", str(text or ""))
    cleaned = re.sub(r"^[\s\-–—•□■▪]+", "", cleaned)
    quoted = re.search(r"『([^』]{4,50})』", cleaned)
    candidate = quoted.group(1).strip() if quoted else re.split(r"[。；;\n]", cleaned, maxsplit=1)[0].strip()
    candidate = re.split(r"[，,：:]", candidate, maxsplit=1)[0].strip()
    if not candidate or candidate == "待使用者補充":
        return fallback
    words = candidate.split()
    if len(words) > 10:
        candidate = " ".join(words[:10])
    if len(candidate) > 34:
        candidate = candidate[:34].rstrip()
    return candidate


def _derive_outline_text(content_map: dict[str, str]) -> str:
    """Build the same two-level outline for all section-navigation slides."""
    lines: list[str] = []
    for section, label in SECTION_LABELS.items():
        content = str(content_map.get(section, "") or "")
        pieces = [
            _derive_slide_title(piece, "")
            for piece in re.split(r"[。；;\n]+", content)
            if piece.strip()
        ]
        pieces = [piece for piece in pieces if piece.lower() not in {"doi", "citation", "reference"}]
        unique: list[str] = []
        for piece in pieces:
            if piece and piece not in unique:
                unique.append(piece)
            if len(unique) == 3:
                break
        if not unique:
            unique = ["待使用者補充"]
        lines.append(label)
        lines.extend(f"  子標題：{piece}" for piece in unique)
    return "\n".join(lines)


def _execution_contract(req: dict, images: list[dict]) -> list[str]:
    image_instruction = (
        f"本次另有 {len(images)} 張上傳圖片；先辨識內容與來源，再依科學意義配置，逐頁建議不是不可更動的綁定。"
        if images
        else "本次沒有另外上傳獨立圖片；請直接從原始研究報告擷取與各頁結論相關的 Figure、Table 或示意圖。"
    )
    return [
        "## 執行契約與規則優先順序",
        "請先完整閱讀本文件、原始研究報告與 PowerPoint 模板，再開始製作；不要邊讀邊生成投影片。",
        f"請直接在提供的模板中製作 {req['pages']} 張內容頁，使用{req['language']}，輸出可編輯的 .pptx。完成初稿後必須逐頁執行本文件末尾的硬性 QA；所有失敗項目修正完畢後才可交付。",
        "除非使用者明確指定，禁止參考、延續或模仿先前 AI 生成的簡報；原始研究報告、模板與本文件才是本次唯一依據。",
        image_instruction,
        "若規則看似衝突，依下列順序處理：① 原始研究報告的事實與數據；② 模板固定 shell、Title 2、安全內容區與頁數；③ 本文件的硬性 QA；④ 逐頁 Main Message 與內容配置；⑤ 裝飾性偏好。低順位規則不得破壞高順位規則。",
        "允許依實際 Figure 與文字長度彈性調整同一章節內的圖片配對、文字位置與內容分配，但不得改變總內容頁數、四大章節順序、模板固定元素、最低字級或資料正確性。",
        "若 24 pt 正文或主圖無法在原配置中清楚呈現，先精簡文字，再於同章節頁面間重新分配內容；不得縮小字體、縮小主圖、遮住模板或新增未經來源支持的內容。",
    ]


def _visual_rules_summary(style_rules: dict) -> list[str]:
    typography = style_rules.get("typography", {})
    colors = style_rules.get("color_palette", {})
    geometry = style_rules.get("template_geometry", {})
    if not isinstance(typography, dict):
        typography = {}
    if not isinstance(colors, dict):
        colors = {}
    if not isinstance(geometry, dict):
        geometry = {}
    return [
        "- 直接沿用提供的 PowerPoint 模板母片與既有版面，不重畫頁首頁尾。",
        f"- 【標題硬規則】每張內容頁只可改寫模板原有 Title 2，不得新增或移動標題框。{geometry.get('title_placeholder', '標題必須位於頂部固定框線與藍黃分隔線之上。')}",
        "- 標題必須完整位於頂部藍黃分隔線之上；標題物件 top 不得超過 65.9 pt，內容圖片、正文與 callout 則必須位於分隔線下方。",
        f"- 標題以 {typography.get('title_pt', 53)} pt 為準，長標題可精簡但不得低於 40 pt；一般正文、清單與圖旁結論以 {typography.get('body_pt', 24)} pt 為絕對下限；caption 16–20 pt，引用 {typography.get('reference_pt', '12–14')} pt。放不下時拆頁或刪字，禁止縮小正文。",
        "- 內容頁標題不得只寫『研究背景／研究方法／研究結果／結論』或加頁碼；必須從本頁證據提煉成具體、可說出口的子標題或結論句。",
        "- Outline 及每張章節導覽頁都要顯示相同的兩層階層：藍色空心方框標示四個主章節，每章下面用黃色實心菱形列出 1–3 個由研究內容推導的短子標題。",
        "- 項目符號採語意一致原則：一個結論句不使用 bullet；真正的同層清單才使用 PowerPoint 原生 bullet，且同頁同層的符號、縮排與間距完全一致。禁止鍵入 □、■、▪、• 當作假 bullet。",
        f"- 技術重點使用 {colors.get('technical_emphasis_blue', '#0000FF')}；差異或警告使用 {colors.get('warning_red', '#FF0000')}；不可過量使用。",
        "- 每張結果頁至少加粗一個結論關鍵詞或關鍵數值；技術機制可用藍色，負向漂移、劣化或風險才用紅色。不得整段全粗或整頁同色。",
        "- 每段開始前插入同版章節導覽頁：目前段落黑色 #000000，其餘段落淺灰 #BFBFBF；所有文字位置固定不變。",
        "- 圖像優先：一頁一個結論、一張主圖；正文不超過 60 個中文字或 35 個英文單字，最多 3 個短標籤。",
        "- 流程、因果、溫度／時間演變、before/after 或多圖閱讀順序必須使用可編輯的原生箭頭／connector；統一由左至右或由上至下，不可穿過圖片或文字，也不可只用『→』字元假裝箭頭。",
        "- 標籤放在圖片留白或圖片外側，不可遮住座標軸、圖例、數據、元件結構或重要特徵。",
        "- 全篇只在 1–3 張真正具有局部關鍵差異的結果頁使用虛線框，每頁最多一個；使用透明填滿、1–2 pt 真正 dashed outline，矩形緊貼目標 panel 或資料區並保留約 4–8 pt。不得框空白、跨無關 panels 或漂浮在圖片外；沒有明確 ROI 就不要加框。",
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
    base = (
        f"{image_source}作為主視覺；先決定圖片閱讀順序，再加入必要箭頭。"
        "可見正文不超過 60 個中文字或 35 個英文單字，最多 3 個短標籤；"
        "文字放在圖片留白或外側，不遮住科學資訊；一般正文與圖旁結論不得低於 24 pt，放不下時刪字或拆頁。"
    )
    if section == "methods":
        return base + "若本頁包含兩個以上製程或量測步驟，必須用可編輯原生箭頭連接，清楚標示由左至右或由上至下的順序。"
    if section == "results":
        return base + "必須將至少一個結論關鍵詞或關鍵數值加粗；有比較或多圖順序時加入原生箭頭。只有能明確指出局部 ROI 時才用一個透明細虛線框緊貼該圖區，否則不要加框。"
    return base + "將最重要的一個詞組加粗；只有技術機制或負向風險需要時才分別使用藍色或紅色。"

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
