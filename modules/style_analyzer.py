import json
from pathlib import Path

from .validators import validate_style_rules


def default_style_rules(style_name: str) -> dict:
    return {
        "source": "mock",
        "style_name": style_name,
        "presentation_structure": "封面、背景、方法、結果、結論",
        "visual_layout": "16:9；每頁一個主要訊息；圖文保持留白",
        "color_palette": ["#16324F", "#2E86AB", "#F6F7F8"],
        "typography": {"title_pt": 36, "body_pt": 22, "font": "Noto Sans TC"},
        "image_layout": "結果圖優先使用大圖，流程圖搭配精簡步驟",
        "citation_style": "頁尾列出來源；未知來源標記待補，不得捏造",
    }


def load_style_rules(path: Path | None, style_name: str) -> dict:
    if path is None:
        return default_style_rules(style_name)
    if not path.exists():
        raise ValueError(f"找不到成員二的風格規則檔：{path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_style_rules(data)
    if errors:
        raise ValueError("；".join(errors))
    data.setdefault("source", str(path))
    return data
