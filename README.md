# 學術簡報 Prompt 產生器

本專案將簡報需求、研究文字與圖片資料整理成 `style_rules.json`、`content_analysis.json` 與 `final_prompt.txt`。目前是可展示的 mock 整合版；成員二、三交付模組後，可透過 `modules/style_analyzer.py` 與 `modules/integration.py` 接入。

## 分工界線

- 成員一：`app.py`、`validators.py`、`quality_checker.py`、`integration.py` 與整體測試。
- 成員二：提供正式的 `data/style_rules.json` 或替換 `style_analyzer.py` 的分析來源。
- 成員三：改進 `content_analyzer.py` 與 `prompt_generator.py`；輸出介面保持不變。
- `C:\Users\user\Downloads\academic_presentation_generator.py` 是隊友原始附件，本專案沒有修改它。

## Windows + VS Code 初次設定

### 1. 安裝正確的 Python

目前這台電腦的 `python` 指向 GTKWave 附帶的損壞版本。請從 [python.org](https://www.python.org/downloads/windows/) 安裝正式 Python，安裝時勾選 **Add python.exe to PATH**，完成後完全關閉並重開 VS Code。

在 VS Code 選「終端機 → 新增終端機」，執行：

```powershell
where.exe python
python --version
git --version
```

`where.exe python` 的第一個結果不應是 `C:\iverilog\gtkwave\bin\python.exe`。若仍是它，請在 Windows「編輯系統環境變數 → 環境變數 → Path」把正式 Python 路徑移到 GTKWave 前面，再重開 VS Code。

### 2. 開啟專案與建立虛擬環境

```powershell
cd "C:\Users\user\OneDrive\文件\summer lecture\academic-presentation-generator"
code .
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

如果 PowerShell 不允許啟用，僅對目前視窗執行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

在 VS Code 按 `Ctrl+Shift+P`，選 `Python: Select Interpreter`，再選 `.venv`。

### 3. 執行

```powershell
python -m streamlit run app.py
```

瀏覽器通常會開啟 `http://localhost:8501`。終端機按 `Ctrl+C` 停止。

### 4. 測試

```powershell
python -m pytest -q
```

正常會看到所有測試通過。若出現 `No module named ...`，先確認終端機開頭有 `(.venv)`，再重新安裝 requirements。

## 資料契約

完整範例位於 `data/samples/`。

### user_inputs.json

- 必填 `requirements`：`topic` 字串、`audience` 字串、`duration_minutes` 整數、`pages` 整數、`language` 字串、`style` 字串。
- 必填 `text_content`：`background`、`methods`、`results`、`conclusion`，皆為字串。
- 選填 `images`：陣列；每項包含 `filename`、`type`、`description`、`purpose`。JSON 不保存二進位圖片。

### style_rules.json

必填 `presentation_structure`、`visual_layout`、`color_palette`、`typography`；其他欄位可選。正式檔案可放在 `data/style_rules.json`。

### content_analysis.json

包含 `sections`、`images` 與 `warnings`。圖片實體檔存在 `outputs/uploads/`，JSON 只保存安全檔名與描述。

## Git/GitHub 協作

第一次開始自己的工作：

```powershell
git switch -c member1-streamlit
git status
git add academic-presentation-generator
git commit -m "建立 Streamlit 整合介面"
git push -u origin member1-streamlit
```

之後到 GitHub 從 `member1-streamlit` 對 `main` 建立 Pull Request。開始新工作前：

```powershell
git switch main
git pull origin main
git switch -c member1-next-task
```

不要把 `.venv`、上傳圖片或 `outputs` 執行結果 commit。合併隊友檔案前先 `git status`，有未提交修改時先完成 commit，不要用會清除修改的 reset 指令。

## Docker 決策

目前不加入 Docker：本機展示與 Streamlit Community Cloud 通常使用 `requirements.txt` 即可。先確保三位成員使用相同 Python 主版本、測試通過且 README 可重現。只有老師要求容器、系統依賴複雜，或各電腦環境持續不一致時，再加入 Dockerfile；Docker 會增加映像建置、port、volume 與檔案權限的除錯成本。

## 常見問題

- 沒有圖片仍可執行，系統會產生純文字版並加入警告。
- 勾選外部風格規則但 `data/style_rules.json` 不存在時，系統會顯示可讀的錯誤訊息；未勾選時使用 mock 規則。
- 系統目前產生的是 AI/NotebookLM 可使用的文字 Prompt，不會直接產生 `.pptx`。
- 不提供來源時，Prompt 會要求標記「待補」，禁止捏造引用與數據。
