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
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

    /* 淡米白背景嗨嗨 */
    .stApp {
        background-color: #FAF7F0;
        color: #2F3542;
        font-family:
            "Microsoft JhengHei",
            "Noto Sans TC",
            sans-serif;
    }

    /* 深藍色標題 */
    h1, h2, h3 {
        color: #376092 !important;
        font-family:
            "Source Han Sans TC",
            "思源黑體 TC",
            "Noto Sans TC",
            "Microsoft JhengHei",
            sans-serif !important;
        font-weight: 900 !important;
    }

    /* 欄位名稱與一般小字 */
    label,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"],
    .stFileUploader small {
        color: #2F3542 !important;
    }

    /* 輸入框內的文字與下拉選單文字 */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input,
    [data-baseweb="select"] input,
    [data-baseweb="select"] span,
    [data-baseweb="select"] div {
        color: #202733 !important;
        -webkit-text-fill-color: #202733 !important;
    }

    /* 尚未輸入時的提示文字 */
    input::placeholder,
    textarea::placeholder {
        color: #7A7F87 !important;
        opacity: 1 !important;
    }

    /* 主標題置中 */
    h1 {
        text-align: center;
    }

    /* 黃色標題裝飾線 */
    h1::after {
        content: "";
        display: block;
        width: 100px;
        height: 5px;
        margin: 12px auto 20px auto;
        background-color: #F9CB07;
        border-radius: 10px;
    }

    /* 深藍色按鈕 */
    .stButton > button,
    .stFormSubmitButton > button {
        display: block;
        margin: 12px auto;
        color: #FFFFFF !important;
        background-color: #6F98C4 !important;
        border: 2px solid #6F98C4 !important;
        border-radius: 999px;
        font-weight: bold;
        padding: 0.6rem 2rem;
    }

    .stButton > button p,
    .stButton > button span,
    .stFormSubmitButton > button p,
    .stFormSubmitButton > button span {
        color: #FFFFFF !important;
    }

    /* 滑鼠移到按鈕時使用黃色 */
    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        color: #2F3542;
        background-color: #F5D96B !important;
        border-color: #F5D96B !important;
    }

    .stButton > button:hover p,
    .stButton > button:hover span,
    .stFormSubmitButton > button:hover p,
    .stFormSubmitButton > button:hover span {
        color: #2F3542 !important;
    }

    /* 白色輸入框 */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input,
    [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border-radius: 12px;
    }

    /* 圖片上傳區的說明與按鈕文字 */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #9AA8B8;
        border-radius: 12px;
    }

    [data-testid="stFileUploaderDropzone"] div,
    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] small {
        color: #2F3542 !important;
    }

    /* Upload 按鈕使用淡色，避免文字與背景混在一起 */
    [data-testid="stFileUploaderDropzone"] button {
        color: #315B8A !important;
        background-color: #E7EFF8 !important;
        border: 1px solid #9CB6D2 !important;
        border-radius: 10px !important;
    }

    [data-testid="stFileUploaderDropzone"] button p,
    [data-testid="stFileUploaderDropzone"] button span,
    [data-testid="stFileUploaderDropzone"] button svg {
        color: #315B8A !important;
        fill: #315B8A !important;
    }

    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #D5E4F3 !important;
        border-color: #6F98C4 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("學術簡報 Prompt 產生器")
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
