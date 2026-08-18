# NanoSTLab 學術簡報 Prompt 產生器

本專案是 NanoSTLab 實驗室專用的 Streamlit 工具。使用者輸入研究內容、報告時間、內容頁數與圖片後，系統會依照實驗室學姊的優良簡報風格，產生可交給 NotebookLM 或其他簡報 AI 使用的 `final_prompt.txt`。

系統本身不直接產生 `.pptx`。正確流程是：將 Prompt、原始報告及圖片、與實驗室 PPT 模板一起交給支援編輯 PPT 的 AI，讓 AI 直接使用模板母片與版面配置產生最終可編輯簡報。

## 線上使用（推薦）

本專案可部署至 Streamlit Community Cloud，並透過固定網址展示與使用。部署完成後，使用者只需要瀏覽器，不需要下載專案、安裝 Python 或設定 VS Code。

> **固定網址：[開啟 NanoSTLab 學術簡報 Prompt 產生器](https://nanostlab-prompt-generator.streamlit.app/)**

線上使用流程：

1. 開啟固定網址。
2. 填寫簡報需求與四個部分的研究內容。
3. 視需要上傳研究圖片。
4. 按下「開始分析」，並下載系統產生的 `final_prompt.txt`。
5. 將 `final_prompt.txt`、原始研究文件、研究圖片及實驗室 PowerPoint 模板一起交給支援製作簡報的 AI。

### 資料安全提醒

- 本系統目前是課程專題與實驗室使用原型。
- 公開展示版本請勿輸入機密、尚未發表或禁止上傳至外部雲端服務的研究資料。
- 部署於 Streamlit Community Cloud 時，使用者輸入與上傳檔案會由雲端環境處理。
- 若要處理未公開研究資料，應改用本機版本或由實驗室管理的內部伺服器。

## 核心規則

- 固定以「實驗室教授與成員」為報告對象。
- 固定使用 NanoSTLab 實驗室優良簡報風格，不提供其他風格選項。
- 自動載入 `data/style_rules.json`，使用者不需要手動選擇。
- 實驗室模板封面由使用者填寫，不由 AI 重新生成。
- AI 產生的第一張內容頁必須是 `Outline`。
- 每個新段落前重複使用相同的 `Outline` 導覽頁；目前段落使用黑色，其餘段落使用淺灰色。
- 使用者設定的頁數只計算內容頁，不包含模板封面。
- 保留模板母片、Logo、頂部標題區、底部實驗室識別與右下頁碼。
- 只使用使用者提供的文字、圖片、數據、公式與引用；資料不足時標示「待補」。
- 為縮短 AI 生成時間，Prompt 不要求講者備註、不要求重建模板固定元素，也不要求裝飾性圖片。
- 圖像頁以一張主圖、一個結論為原則，可見正文最多約 60 個中文字，並限制箭頭、標籤與虛線重點框的使用。

## 風格參考

`data/style_rules.json` 依照兩份實驗室優良簡報整理，主要版面規則包括約 48–53 pt 標題、24–27 pt 主文、10–11 pt 引用，以及藍色技術重點、紅色差異或警告、固定頁首頁尾和右下頁碼。

## 成員分工

- 成員一 楊馨惠：`app.py`、`validators.py`、`quality_checker.py`、`integration.py`、介面整合與整體測試，及最後所有排版確認及優化。
- 成員二 吳芷暄：檢查及維護 `data/style_rules.json`，確認規則符合實驗室優良簡報與固定模板。
- 成員三 李秉奇：改進 `content_analyzer.py` 與 `prompt_generator.py`，提高摘要、分頁、圖片配對及逐頁 Prompt 品質；不得改變既有函式介面。

## 本機安裝與執行（開發或內部資料使用）

只有需要修改程式、執行測試，或不希望研究資料經過公開雲端環境時，才需要在本機安裝。

### 1. 建立環境

在 VS Code 開啟專案後執行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

如果 PowerShell 不允許啟用虛擬環境：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. 啟動 Streamlit

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

瀏覽器通常會開啟 `http://localhost:8501`。終端機按 `Ctrl+C` 可停止服務。

### 3. 執行測試

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

如果 Windows 暫存資料夾出現權限錯誤，可指定專案內的測試暫存位置：

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q --basetemp=outputs\pytest-temp -p no:cacheprovider
```

## 使用方式

Streamlit 介面讓使用者輸入：

- 主題
- 報告時間
- 內容投影片頁數（不含模板封面，至少 8 頁以容納四張段落導覽頁）
- 語言
- 研究背景
- 研究方法
- 研究結果
- 結論
- 選填圖片、圖片類型、用途與說明

完成後會產生：

- `user_inputs.json`：本次使用者輸入。
- `style_rules.json`：本次使用的實驗室風格規則。
- `content_analysis.json`：章節、圖片配置建議與警告。
- `quality_report.json`：頁數與逐頁必要欄位檢查結果。
- `final_prompt.txt`：交給簡報 AI 使用的最終 Prompt。

每次執行結果會存放在 `outputs/<時間戳記>/`。

## 將 Prompt 交給 AI

把以下資料一起上傳給 NotebookLM 或其他支援簡報製作的 AI：

1. 系統產生的 `final_prompt.txt`。
2. 原始研究文件，例如 Word、PDF 或文字資料。
3. Prompt 中列出的所有研究圖片。
4. 實驗室 PowerPoint 模板。

## 資料契約

範例位於 `data/samples/`。

### `user_inputs.json`

- `requirements`：包含 `topic`、`audience`、`duration_minutes`、`pages`、`language`、`style`。
- `audience` 由系統固定為「實驗室教授與成員」。
- `style` 由系統固定為「NanoSTLab 實驗室優良簡報風格」。
- `text_content`：包含 `background`、`methods`、`results`、`conclusion`。
- `images`：選填陣列，每項包含 `filename`、`type`、`description`、`purpose`。

### `style_rules.json`

必須包含 `presentation_structure`、`visual_layout`、`color_palette` 與 `typography`。正式規則固定放在 `data/style_rules.json`。

### `content_analysis.json`

包含 `sections`、`images` 與 `warnings`。圖片實體檔存在 `outputs/uploads/`，JSON 只保存安全檔名與描述。

## 常見問題

- 一般使用者可直接開啟固定網址，不需要安裝 Python、VS Code 或下載 GitHub 專案。
- 沒有圖片仍可執行，系統會產生純文字版 Prompt 並加入警告。
- 找不到 `data/style_rules.json` 時，系統會顯示可讀的錯誤訊息。
- 系統產生的是簡報製作 Prompt，不是最終 `.pptx`。
- AI 看到圖片檔名不代表已取得圖片，必須把原始圖片一起上傳。
- 不提供來源時，Prompt 會標示「待補」，禁止捏造引用與數據。
- 模板封面不計入 Streamlit 設定的內容頁數。