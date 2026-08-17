from modules.content_analyzer import analyze_content
from modules.prompt_generator import generate_final_prompt


def test_result_content_is_split_across_slides():
    data = {
        "requirements": {
            "topic": "RRAM",
            "audience": "研究生",
            "duration_minutes": 10,
            "pages": 10,
            "language": "繁體中文",
            "style": "學術正式",
        },
        "text_content": {
            "background": "這是研究背景。",
            "methods": "這是研究方法。",
            "results": "第一項結果。第二項結果。第三項結果。",
            "conclusion": "這是研究結論。",
        },
        "images": [],
    }

    analysis = analyze_content(data)
    prompt = generate_final_prompt(data, {}, analysis)

    assert prompt.count("第一項結果。第二項結果。第三項結果。") == 0
    assert "第一項結果。" in prompt
    assert "第二項結果。" in prompt


def test_prompt_requires_ai_to_use_supplied_template():
    data = {
        "requirements": {
            "topic": "RRAM",
            "audience": "實驗室教授與成員",
            "duration_minutes": 10,
            "pages": 10,
            "language": "繁體中文",
            "style": "NanoSTLab 實驗室優良簡報風格",
        },
        "text_content": {
            "background": "這是研究背景。",
            "methods": "這是研究方法。",
            "results": "這是研究結果。",
            "conclusion": "這是研究結論。",
        },
        "images": [],
    }

    analysis = analyze_content(data)
    prompt = generate_final_prompt(data, {}, analysis)

    assert "完整閱讀" in prompt and "原始研究報告" in prompt
    assert "Figure、Table 與圖片" in prompt
    assert "不得自行上網搜尋、生成或替換研究圖片" in prompt
    assert "使用者不需要另外提供圖片說明" in prompt
    assert "若與圖片實際內容不符，必須移至正確頁面" in prompt
    assert "直接使用" in prompt and "實驗室 PowerPoint 模板" in prompt
    assert "保留模板既有封面、母片、Logo、頁首、頁尾" in prompt
    assert "套用模板既有的內容版面" in prompt
    assert "已套用實驗室模板的可編輯 .pptx" in prompt
    assert "不得把整頁轉成單一圖片" in prompt


def test_prompt_adds_repeated_section_transition_slides():
    data = {
        "requirements": {
            "topic": "RRAM",
            "audience": "實驗室教授與成員",
            "duration_minutes": 10,
            "pages": 10,
            "language": "繁體中文",
            "style": "NanoSTLab 實驗室優良簡報風格",
        },
        "text_content": {
            "background": "研究背景內容。",
            "methods": "研究方法內容。",
            "results": "研究結果內容。",
            "conclusion": "研究結論內容。",
        },
        "images": [],
    }

    prompt = generate_final_prompt(data, {}, analyze_content(data))

    assert prompt.count("Layout: 章節導覽轉場") == 4
    assert "僅「研究背景」使用黑色 #000000" in prompt
    assert "僅「研究方法」使用黑色 #000000" in prompt
    assert "僅「研究結果」使用黑色 #000000" in prompt
    assert "僅「結論與未來工作」使用黑色 #000000" in prompt
    assert "淺灰 #BFBFBF" in prompt
    assert "研究背景\n研究方法\n研究結果\n結論與未來工作" in prompt
    assert "由上往下單欄排列、靠左對齊" in prompt
    assert "不得改成橫向並排" in prompt
    assert "Speaker Notes:" not in prompt
