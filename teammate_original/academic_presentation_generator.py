import json

def analyze_and_prompt_for_notebooklm_ppt(user_inputs, style_rules):
    """
    產生專門給 NotebookLM 讀取的全中文 Prompt。
    強制執行「純淨白底」與「Layout 5 佔位符」兩大鐵律，並匯入精簡版美學規範。
    """
    images_text = json.dumps(user_inputs['images'], ensure_ascii=False, indent=2)
    
    style_rules_text = "\n".join([f"[{k}]：{v}" for k, v in style_rules.items()])

    final_prompt = f"""
你現在是一套學術簡報自動化系統的後端大腦。
使用者會提供你原始的學術素材、上傳的文獻檔案，以及排版要求。你的唯一任務是：**直接生成並輸出一個完整、排版精美的 `.pptx` 簡報檔案**。

【一、 簡報基本資訊與需求】
- 簡報主題：{user_inputs['requirements']['topic']}
- 預計總頁數：至少 {user_inputs['requirements']['pages']} 頁（採用漸進式資訊揭露，維持清爽留白）。

【二、 內容來源：優先解析上傳檔案】
- **請深入分析使用者在此次對話中上傳的所有檔案（如 Word、PDF、txt 報告或文獻）**。
- 將檔案中的內容提煉成學術簡報所需的關鍵字與精簡短語，並與下方「原始素材」交叉整合。

【三、 原始素材與對應說明】
- 背景：{user_inputs['text_content']['background']}
- 實驗方法：{user_inputs['text_content']['methods']}
- 數據結果：{user_inputs['text_content']['results']}
- 結論：{user_inputs['text_content']['conclusion']}
- 圖片素材對應說明：\n{images_text}

【四、 🚨 絕對不可違背的核心排版指令 (最高優先級)】
1. 完全拔除手動背景：刪除了所有手動繪製的藍黃分隔線、NYCU/NanoSTLab 頁尾與背景底色。整張投影片只保留純淨的白底與您的學術內容。
2. 套用 Native Title 佔位符：每一頁的簡報標題，請務必寫進 PowerPoint 內建的「標題佔位符（Layout 5: Title Only）」中，絕對禁止使用自訂文字方塊。

【五、 實驗室精簡美學規範】
請在嚴格遵守【第四點】核心指令的前提下，套用以下美學規則：

{style_rules_text}

【六、 最終輸出規範】
請將上述內容與排版規則完美整合，直接生成並提供 `.pptx` 檔案。不要輸出程式碼，只要最終具備專業排版與圖文並茂的簡報檔案。
"""

    with open('direct_file_prompt.txt', 'w', encoding='utf-8') as f:
        f.write(final_prompt)
        
    print("✅ 成功生成支援『拔除手動背景』及『Layout 5 佔位符』的 direct_file_prompt.txt！")
    return final_prompt


# ==========================================
# 測試執行區
# ==========================================
if __name__ == "__main__":
    mock_user_inputs = {
        "requirements": {
            "topic": "RRAM Mechanism Model", 
            "pages": 8
        },
        "text_content": {
            "background": "請參考我上傳的期末報告 Word 檔第一章。",
            "methods": "請參考上傳文獻中的 Experimental Setup 區塊。",
            "results": "觀察到典型的 Bipolar 切換現象，詳細數據請見上傳的 Excel 或報告內容。",
            "conclusion": "此現象可由氧空缺模型解釋，未來可應用於神經形態運算。"
        },
        "images": [
            {"filename": "device_sem.png", "description": "元件橫截面的 SEM 結構圖，請放在結構分析那一頁的右側"},
            {"filename": "iv_curve.png", "description": "Bipolar I-V 切換曲線，請放在電性測量結果的右側"}
        ]
    }
    
    mock_style_rules = {
        "presentation_structure": "禁止封面頁，第一頁直接使用 Outline。簡報分為 Outline、Core Content、Summary & Future Work 三大區塊。",
        "content_density": "文字極度精簡。標題約 2–8 個英文單字；圖片標籤與重點短語約 3–6 個單字；禁止長段落。",
        "visual_layout": "採學術圖像導向排版，避免傳統大量條列。優先使用左側摘要、右側圖片、圖表或多圖對比配置。",
        "information_pacing": "每頁只呈現一個核心概念。複雜流程、模型或多組實驗應拆成連續投影片，逐步揭露內容。",
        "image_layout": "兩張圖使用左右並排；三張圖使用三欄或一主兩輔；四張圖使用 2×2 排列。圖片與標籤必須對齊並保持一致間距。",
        "data_and_formula_presentation": "核心參數與數據使用表格、數值區塊或左右比較呈現。公式獨立放置，保留符號、單位及變數說明。",
        "slide_size": "統一使用 16:9，尺寸為 13.333 × 7.500 inch，背景為純白色。",
        "title_style": "遵循 Layout 5 佔位符設定。字體使用 Arial 或 Calibri 粗體黑字，建議 48 pt；長標題可縮小至 40–44 pt。",
        "body_font_style": "區塊標題使用 26–28 pt，主要文字 24 pt，次要文字 18–20 pt，圖說 16–18 pt，參考文獻 10 pt。",
        "color_palette": "主色為深藍 #376092 與黃色 #F9CB07（僅用於重點強調或表格）；正文使用黑色，背景使用純白色。",
        "page_number_style": "第一張 Outline 從第 1 頁開始。頁碼直接透過內建功能加入，使用 14 pt。",
        "reference_style": "引用放在投影片底部邊緣，使用 Arial 10 pt 深灰色，只保留與該頁直接相關的來源。",
        "visual_whitespace": "每頁保留約 15%–25% 留白。若內容無法以規定字體放入，必須拆頁，不可縮小文字硬塞。",
        "content_accuracy": "只能使用使用者提供的文字、圖片、數據、公式與來源，不得虛構參數、結果、文獻或結論。",
        "prompt_output_requirement": "最終 Prompt 必須逐頁提供 Slide Number、Title、Main Message、Layout、Text、Image Filename、Data or Formula、Citation、Speaker Notes 與 Design Instructions。"
    }
    
    analyze_and_prompt_for_notebooklm_ppt(mock_user_inputs, mock_style_rules)