import json
from datetime import datetime
from pathlib import Path

from .content_analyzer import analyze_content
from .prompt_generator import generate_final_prompt
from .quality_checker import check_final_prompt
from .style_analyzer import load_style_rules
from .validators import validate_user_inputs


def run_pipeline(user_inputs: dict, output_root: Path, style_rules_path: Path | None = None) -> dict:
    errors = validate_user_inputs(user_inputs)
    if errors:
        return {"success": False, "errors": errors}
    try:
        style_rules = load_style_rules(style_rules_path, user_inputs["requirements"]["style"])
        content_analysis = analyze_content(user_inputs)
        final_prompt = generate_final_prompt(user_inputs, style_rules, content_analysis)
        quality = check_final_prompt(final_prompt, user_inputs)
        run_dir = output_root / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        run_dir.mkdir(parents=True, exist_ok=False)
        _write_json(run_dir / "user_inputs.json", user_inputs)
        _write_json(run_dir / "style_rules.json", style_rules)
        _write_json(run_dir / "content_analysis.json", content_analysis)
        _write_json(run_dir / "quality_report.json", quality)
        (run_dir / "final_prompt.txt").write_text(final_prompt, encoding="utf-8")
        return {
            "success": True,
            "style_rules": style_rules,
            "content_analysis": content_analysis,
            "final_prompt": final_prompt,
            "quality": quality,
            "output_dir": str(run_dir),
        }
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return {"success": False, "errors": [f"系統處理失敗：{exc}"]}


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

