from modules.validators import validate_user_inputs


def valid_input() -> dict:
    return {
        "requirements": {"topic": "RRAM", "audience": "研究生", "duration_minutes": 10, "pages": 8, "language": "繁體中文", "style": "學術正式"},
        "text_content": {"background": "背景", "methods": "方法", "results": "結果", "conclusion": "結論"},
        "images": [],
    }


def test_valid_input_without_images_is_allowed():
    assert validate_user_inputs(valid_input()) == []


def test_missing_topic_is_rejected():
    data = valid_input()
    data["requirements"]["topic"] = ""
    assert "請填寫主題。" in validate_user_inputs(data)


def test_invalid_page_count_is_rejected():
    data = valid_input()
    data["requirements"]["pages"] = 2
    assert any("頁數" in error for error in validate_user_inputs(data))

