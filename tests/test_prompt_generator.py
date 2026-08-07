from modules.content_analyzer import analyze_content
from modules.prompt_generator import generate_final_prompt


def test_result_content_is_split_across_slides():
    data = {
        "requirements": {
            "topic": "RRAM",
            "audience": "研究生",
            "duration_minutes": 10,
            "pages": 8,
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