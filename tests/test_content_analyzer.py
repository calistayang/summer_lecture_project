from modules.content_analyzer import analyze_content


def test_short_sections_create_warnings():
    data = {
        "requirements": {"pages": 8},
        "text_content": {
            "background": "短",
            "methods": "短",
            "results": "短",
            "conclusion": "短",
        },
        "images": [],
    }

    result = analyze_content(data)

    assert result["warnings"]
    assert any(
        "研究背景內容較短" in warning
        for warning in result["warnings"]
    )