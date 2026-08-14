# NanoSTLab 學術簡報 Prompt 產生器

本專案是 NanoSTLab 實驗室專用的 Streamlit 工具。使用者輸入研究內容、報告時間、內容頁數與圖片後，系統會依照實驗室學姊的優良簡報風格，產生可交給 NotebookLM 或其他簡報 AI 使用的 `final_prompt.txt`。

系統本身不直接產生 `.pptx`。正確流程是：將 Prompt、原始報告、原始圖片與實驗室 PowerPoint 模板一起交給支援編輯 PPTX 的 AI，讓 AI 直接使用模板母片與版面配置產生最終可編輯簡報。

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

`data/style_rules.json` 依照兩份實驗室優良簡報整理：

- 主要參考：`ITRI-Meeting_Ming-Chun-Hong_20201119_Quantum-Computing_new.pptx`，使用 16:9 比例與新版實驗室視覺系統。
- 輔助參考：`Group-Meeting_Ming-Chun-Hong_20181220.pptx`，只參考學術內容節奏，不沿用其 4:3 比例。

主要版面規則包括約 48–53 pt 標題、24–27 pt 主文、10–11 pt 引用，以及藍色技術重點、紅色差異或警告、固定頁首頁尾和右下頁碼。

## 成員分工

- 成員一：`app.py`、`validators.py`、`quality_checker.py`、`integration.py`、介面整合與整體測試。
- 成員二：檢查及維護 `data/style_rules.json`，確認規則符合實驗室優良簡報與固定模板。
- 成員三：改進 `content_analyzer.py` 與 `prompt_generator.py`，提高摘要、分頁、圖片配對及逐頁 Prompt 品質；不得改變既有函式介面。
- `teammate_original/academic_presentation_generator.py` 保留成員三原始附件，只作比較參考，不直接接入執行流程。

## 安裝與執行

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

可以另外告訴 AI：

```text
請嚴格依照 final_prompt.txt 製作內容頁，只能使用我提供的研究資料與圖片。
請直接使用我上傳的實驗室 PowerPoint 模板建立簡報，不要另外仿製一套模板。
保留模板既有封面、母片、Logo、頁首、頁尾、固定圖案與頁碼位置。
內容頁從 Outline 開始，所有內容保持可編輯，不可把整頁轉成圖片。
```

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

## Git/GitHub 協作

開始新工作前，先從最新 `main` 建立自己的分支：

```powershell
git switch main
git pull origin main
git switch -c member-name-task
```

修改完成後：

```powershell
git status
git add <修改的檔案>
git commit -m "說明本次修改"
git push -u origin member-name-task
```

再到 GitHub 建立 Pull Request。不要直接在已經合併的舊分支繼續修改，也不要 commit `.venv`、上傳圖片或 `outputs` 執行結果。

## 常見問題

- 沒有圖片仍可執行，系統會產生純文字版 Prompt 並加入警告。
- 找不到 `data/style_rules.json` 時，系統會顯示可讀的錯誤訊息。
- 系統產生的是簡報製作 Prompt，不是最終 `.pptx`。
- AI 看到圖片檔名不代表已取得圖片，必須把原始圖片一起上傳。
- 不提供來源時，Prompt 會標示「待補」，禁止捏造引用與數據。
- 模板封面不計入 Streamlit 設定的內容頁數。

## Docker

目前不加入 Docker。本機展示及 Streamlit Community Cloud 使用 `requirements.txt` 即可；只有老師明確要求容器，或三位成員的系統環境持續無法統一時，再評估加入 Dockerfile。
