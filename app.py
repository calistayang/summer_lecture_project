import json
import re
from pathlib import Path
from uuid import uuid4

import streamlit as st

from modules.integration import run_pipeline
from modules.validators import MAX_IMAGE_BYTES

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR = OUTPUT_DIR / "uploads"

st.set_page_config(page_title="學術簡報 Prompt 產生器", page_icon="📊", layout="wide")
st.title("學術簡報 Prompt 產生器")
st.caption("輸入研究內容與圖片，產生符合 NanoSTLab 實驗室優良簡報風格的製作 Prompt。")
st.info("系統固定以實驗室教授與成員為報告對象，並自動套用 NanoSTLab 實驗室模板規則。")

with st.form("presentation_form"):
    st.subheader("一、簡報需求")
    col1, col2 = st.columns(2)
    topic = col1.text_input("主題 *")
    duration = col2.number_input("報告時間（分鐘）*", 1, 180, 10)
    pages = col1.number_input("內容投影片頁數（不含模板封面）*", 5, 50, 8)
    language = col2.selectbox("語言 *", ["繁體中文", "英文", "中英雙語"])

    st.subheader("二、研究內容")
    background = st.text_area("研究背景 *", height=120)
    methods = st.text_area("方法 *", height=120)
    results = st.text_area("結果 *", height=120)
    conclusion = st.text_area("結論 *", height=120)

    st.subheader("三、圖片")
    uploaded_files = st.file_uploader("上傳 PNG、JPG 或 JPEG（每張最多 10 MB）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    image_details = []
    for index, uploaded in enumerate(uploaded_files):
        st.markdown(f"**圖片 {index + 1}：{uploaded.name}**")
        c1, c2 = st.columns(2)
        image_type = c1.selectbox("圖片類型", ["實驗結果圖", "流程圖", "設備照片", "數據圖表", "其他"], key=f"type_{index}_{uploaded.name}")
        purpose = c2.text_input("用途", value="補充本頁重點", key=f"purpose_{index}_{uploaded.name}")
        description = st.text_input("圖片說明 *", key=f"description_{index}_{uploaded.name}")
        image_details.append((uploaded, image_type, purpose, description))

    submitted = st.form_submit_button("開始分析", type="primary")

if submitted:
    image_records = []
    upload_errors = []
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for uploaded, image_type, purpose, description in image_details:
        data = uploaded.getvalue()
        if len(data) > MAX_IMAGE_BYTES:
            upload_errors.append(f"{uploaded.name} 超過 10 MB。")
            continue
        safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(uploaded.name).stem).strip("_") or "image"
        safe_name = f"{safe_stem}_{uuid4().hex[:8]}{Path(uploaded.name).suffix.lower()}"
        saved_path = UPLOAD_DIR / safe_name
        saved_path.write_bytes(data)
        image_records.append({"filename": safe_name, "type": image_type, "description": description.strip(), "purpose": purpose.strip()})

    user_inputs = {
        "schema_version": "1.0",
        "requirements": {
            "topic": topic.strip(), "audience": "實驗室教授與成員",
            "duration_minutes": int(duration), "pages": int(pages),
            "language": language, "style": "NanoSTLab 實驗室優良簡報風格",
        },
        "text_content": {
            "background": background.strip(), "methods": methods.strip(),
            "results": results.strip(), "conclusion": conclusion.strip(),
        },
        "images": image_records,
    }
    if upload_errors:
        for error in upload_errors:
            st.error(error)
    else:
        style_path = BASE_DIR / "data" / "style_rules.json"
        with st.spinner("正在驗證、分析並產生 Prompt…"):
            result = run_pipeline(user_inputs, OUTPUT_DIR, style_path)
        if not result["success"]:
            for error in result["errors"]:
                st.error(error)
        else:
            st.success(f"完成。品質檢查：{'通過' if result['quality']['passed'] else '需要修正'}")
            if result["quality"]["errors"]:
                st.warning("\n".join(result["quality"]["errors"]))
            tabs = st.tabs(["style_rules.json", "content_analysis.json", "final_prompt.txt"])
            style_json = json.dumps(result["style_rules"], ensure_ascii=False, indent=2)
            analysis_json = json.dumps(result["content_analysis"], ensure_ascii=False, indent=2)
            with tabs[0]:
                st.json(result["style_rules"])
                st.download_button("下載 style_rules.json", style_json, "style_rules.json", "application/json")
            with tabs[1]:
                st.json(result["content_analysis"])
                st.download_button("下載 content_analysis.json", analysis_json, "content_analysis.json", "application/json")
            with tabs[2]:
                st.code(result["final_prompt"], language="markdown")
                st.download_button("下載 final_prompt.txt", result["final_prompt"], "final_prompt.txt", "text/plain")
            st.caption(f"本次檔案儲存在：{result['output_dir']}")
