from pathlib import Path

from modules.integration import run_pipeline


def test_pipeline_writes_all_outputs(tmp_path):
    data = {
        "schema_version": "1.0",
        "requirements": {"topic": "RRAM", "audience": "研究生", "duration_minutes": 10, "pages": 8, "language": "繁體中文", "style": "學術正式"},
        "text_content": {"background": "研究背景資料", "methods": "實驗方法資料", "results": "研究結果資料", "conclusion": "研究結論資料"},
        "images": [{"filename": "result.png", "type": "實驗結果圖", "description": "I-V 曲線", "purpose": "呈現量測結果"}],
    }
    result = run_pipeline(data, tmp_path)
    assert result["success"] is True
    assert result["quality"]["passed"] is True
    output = Path(result["output_dir"])
    assert (output / "style_rules.json").exists()
    assert (output / "content_analysis.json").exists()
    assert (output / "final_prompt.txt").exists()


def test_missing_external_style_file_returns_readable_error(tmp_path):
    data = {
        "requirements": {"topic": "RRAM", "audience": "研究生", "duration_minutes": 10, "pages": 8, "language": "繁體中文", "style": "學術正式"},
        "text_content": {"background": "背景", "methods": "方法", "results": "結果", "conclusion": "結論"},
        "images": [],
    }
    result = run_pipeline(data, tmp_path, tmp_path / "missing.json")
    assert result["success"] is False
    assert "找不到" in result["errors"][0]
