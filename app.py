import re
from pathlib import Path
from uuid import uuid4

import streamlit as st

from modules.integration import run_pipeline
from modules.validators import MAX_IMAGE_BYTES, TEXT_MAX_CHARS

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR = OUTPUT_DIR / "uploads"

st.set_page_config(page_title="學術簡報 Prompt 產生器", page_icon="📊", layout="wide")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

    /* 淡米白背景 */
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

    /* 深色模式：深海藍＋灰米色＋深棕色 */

    /* Streamlit 選單手動指定 Dark theme 時也套用相同配色 */
    [data-theme="dark"] .stApp,
    [data-theme="dark"] [data-testid="stAppViewContainer"] {
        background-color: #001F3D !important;
        color: #F3F0DF !important;
    }

    [data-theme="dark"] h1,
    [data-theme="dark"] h2,
    [data-theme="dark"] h3,
    [data-theme="dark"] label,
    [data-theme="dark"] [data-testid="stWidgetLabel"] p,
    [data-theme="dark"] [data-testid="stMarkdownContainer"] p,
    [data-theme="dark"] [data-testid="stCaptionContainer"] {
        color: #F3F0DF !important;
    }

    [data-theme="dark"] [data-testid="stTextInput"] input,
    [data-theme="dark"] [data-testid="stTextArea"] textarea,
    [data-theme="dark"] [data-testid="stNumberInput"] input {
        color: #082B4C !important;
        -webkit-text-fill-color: #082B4C !important;
        background-color: #C9C7AD !important;
    }

    [data-theme="dark"] [data-baseweb="input"],
    [data-theme="dark"] [data-baseweb="select"] > div {
        background-color: #2B0C00 !important;
        border-color: #2B0C00 !important;
    }

    [data-theme="dark"] [data-baseweb="select"] input,
    [data-theme="dark"] [data-baseweb="select"] span,
    [data-theme="dark"] [data-baseweb="select"] div,
    [data-theme="dark"] [data-testid="stNumberInput"] button,
    [data-theme="dark"] [data-testid="stNumberInput"] button svg {
        color: #FFF8ED !important;
        fill: #FFF8ED !important;
        -webkit-text-fill-color: #FFF8ED !important;
    }

    [data-theme="dark"] [data-testid="stFileUploaderDropzone"] {
        color: #F3F0DF !important;
        background-color: #0B3A67 !important;
        border-color: #C9C7AD !important;
    }

    [data-theme="dark"] [data-testid="stFileUploaderDropzone"] div,
    [data-theme="dark"] [data-testid="stFileUploaderDropzone"] span,
    [data-theme="dark"] [data-testid="stFileUploaderDropzone"] small,
    [data-theme="dark"] [data-testid="stFileUploaderDropzone"] svg {
        color: #F3F0DF !important;
        fill: #F3F0DF !important;
    }

    [data-theme="dark"] [data-testid="stAlert"] {
        background-color: #0B3A67 !important;
        border-color: #71849A !important;
    }

    [data-theme="dark"] [data-testid="stAlert"] div,
    [data-theme="dark"] [data-testid="stAlert"] p,
    [data-theme="dark"] [data-testid="stAlert"] span,
    [data-theme="dark"] [data-testid="stAlert"] svg {
        color: #F3F0DF !important;
        fill: #F3F0DF !important;
    }

    [data-theme="dark"] [data-testid="stFileUploaderDropzone"] button,
    [data-theme="dark"] .stButton > button,
    [data-theme="dark"] .stFormSubmitButton > button,
    [data-theme="dark"] .stDownloadButton > button {
        color: #FFF8ED !important;
        background-color: #2B0C00 !important;
        border-color: #8A4B33 !important;
    }

    /* Streamlit 數字欄位與下拉選單的實際深色控制層 */
    [data-theme="dark"] [data-testid="stTextInput"] [data-baseweb="input"],
    [data-theme="dark"] [data-testid="stNumberInput"] [data-baseweb="input"],
    [data-theme="dark"] [data-testid="stNumberInput"] [data-baseweb="base-input"],
    [data-theme="dark"] [data-testid="stNumberInput"] div:has(> button),
    [data-theme="dark"] [data-testid="stNumberInput"] button,
    [data-theme="dark"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-theme="dark"] [data-testid="stSelectbox"] [role="combobox"] {
        background: #2B0C00 !important;
        background-color: #2B0C00 !important;
        border-color: #2B0C00 !important;
    }

    [data-theme="dark"] [data-testid="stNumberInput"] button,
    [data-theme="dark"] [data-testid="stNumberInput"] button svg,
    [data-theme="dark"] [data-testid="stSelectbox"] [role="combobox"],
    [data-theme="dark"] [data-testid="stSelectbox"] [role="combobox"] span,
    [data-theme="dark"] [data-testid="stSelectbox"] [role="combobox"] svg {
        color: #FFF8ED !important;
        fill: #FFF8ED !important;
        -webkit-text-fill-color: #FFF8ED !important;
    }


    /* 最後統一深色控制列，避免箭頭區或外框殘留藍黑色 */
    [data-theme="dark"] [data-testid="stTextInput"] [data-baseweb="input"],
    [data-theme="dark"] [data-testid="stNumberInput"] [data-baseweb="input"] {
        background: #2B0C00 !important;
        border-color: #2B0C00 !important;
        box-shadow: 0 0 0 3px #2B0C00 !important;
    }

    [data-theme="dark"] [data-testid="stNumberInput"] button,
    [data-theme="dark"] [data-testid="stNumberInput"] div:has(> button),
    [data-theme="dark"] [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-theme="dark"] [data-testid="stSelectbox"] [role="combobox"],
    [data-theme="dark"] [data-testid="stSelectbox"] [role="combobox"] > div,
    [data-theme="dark"] [data-testid="stSelectbox"] [role="combobox"] div {
        background: #2B0C00 !important;
        background-color: #2B0C00 !important;
        border-color: #2B0C00 !important;
        box-shadow: none !important;
    }


    /* 下拉箭頭是 combobox 的獨立兄弟節點，需由 select 根節點一起覆蓋 */
    [data-theme="dark"] [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-theme="dark"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-theme="dark"] [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
    [data-theme="dark"] [data-testid="stSelectbox"] [data-baseweb="select"] button {
        background: #2B0C00 !important;
        background-color: #2B0C00 !important;
        border-color: #2B0C00 !important;
    }


    /* BaseWeb 會把箭頭 enhancer 放在更深的匿名節點中 */
    [data-theme="dark"] [data-testid="stSelectbox"] [data-baseweb="select"] *,
    [data-theme="dark"] [data-testid="stSelectbox"] [role="combobox"] *,
    [data-theme="dark"] [data-testid="stSelectbox"] div:has(> [role="combobox"]),
    [data-theme="dark"] [data-testid="stSelectbox"] [role="combobox"] ~ *,
    [data-theme="dark"] [data-testid="stSelectbox"] [data-baseweb="select"] *::before,
    [data-theme="dark"] [data-testid="stSelectbox"] [data-baseweb="select"] *::after {
        background: #2B0C00 !important;
        background-color: #2B0C00 !important;
        border-color: #2B0C00 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.html(
    """
    <script>
    (() => {
        const root = document.documentElement;

        function resolveColor(value) {
            if (!value) return "";
            const probe = document.createElement("span");
            probe.style.color = value;
            probe.style.display = "none";
            document.body.appendChild(probe);
            const resolved = getComputedStyle(probe).color;
            probe.remove();
            return resolved;
        }

        function isDarkColor(value) {
            const numbers = resolveColor(value).match(/[\\d.]+/g);
            if (!numbers || numbers.length < 3) return false;
            const [r, g, b] = numbers.slice(0, 3).map(Number);
            return (0.2126 * r + 0.7152 * g + 0.0722 * b) < 110;
        }

        function syncTheme() {
            const rootStyle = getComputedStyle(root);
            const themeBackground = rootStyle.getPropertyValue("--background-color").trim();
            const header = document.querySelector('[data-testid="stHeader"]');
            const fallback = header ? getComputedStyle(header).backgroundColor : "";
            const nextTheme = isDarkColor(themeBackground || fallback) ? "dark" : "light";
            if (root.dataset.theme !== nextTheme) root.dataset.theme = nextTheme;
        }

        syncTheme();
        window.setInterval(syncTheme, 400);
    })();
    </script>
    """,
    unsafe_allow_javascript=True,
)
st.title("學術簡報 Prompt 產生器")

with st.form("presentation_form"):
    st.subheader("一、簡報需求")
    col1, col2 = st.columns(2)
    topic = col1.text_input("主題 *")
    duration = col2.number_input("報告時間（分鐘）*", 1, 180, 10)
    pages = col1.number_input("內容投影片頁數（不含模板封面）*", 8, 50, 8)
    language = col2.selectbox("語言 *", ["繁體中文", "英文", "中英雙語"])

    st.subheader("二、研究內容")
    st.caption("請貼上與簡報直接相關的重點；不要在單一欄位貼入整篇論文。字數包含空格與標點。")
    background = st.text_area(
        "研究背景 *",
        height=120,
        max_chars=TEXT_MAX_CHARS["background"],
        help=f"研究動機、問題與技術限制，最多 {TEXT_MAX_CHARS['background']:,} 字。",
    )
    methods = st.text_area(
        "方法 *",
        height=120,
        max_chars=TEXT_MAX_CHARS["methods"],
        help=f"材料、元件、設備、流程與分析方式，最多 {TEXT_MAX_CHARS['methods']:,} 字。",
    )
    results = st.text_area(
        "結果 *",
        height=120,
        max_chars=TEXT_MAX_CHARS["results"],
        help=f"主要觀察、數據、比較與限制，最多 {TEXT_MAX_CHARS['results']:,} 字。",
    )
    conclusion = st.text_area(
        "結論 *",
        height=120,
        max_chars=TEXT_MAX_CHARS["conclusion"],
        help=f"研究發現、限制與未來工作，最多 {TEXT_MAX_CHARS['conclusion']:,} 字。",
    )

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
        image_records.append({
            "filename": Path(uploaded.name).name,
            "stored_filename": safe_name,
            "type": image_type,
            "description": description.strip(),
            "purpose": purpose.strip(),
        })

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
            st.subheader("四、最終 Prompt")
            st.code(result["final_prompt"], language="markdown")
            st.download_button(
                "下載 final_prompt.txt",
                result["final_prompt"],
                "final_prompt.txt",
                "text/plain",
            )
            st.info(
                "下一步：將 final_prompt.txt、原始研究報告、原始圖片與實驗室 PowerPoint 模板一起交給 AI。"
                "請 AI 直接使用模板的母片與版面配置，輸出套好模板的可編輯簡報。"
            )
            st.caption(f"本次檔案儲存在：{result['output_dir']}")
