# Lineart 複刻規格書 (Specification)

> 文件版本：1.0
> 基於原始專案：Lineart v0.3.0
> 複刻目標：建立一份可獨立部署、功能完全對等的 Lineart 複刻版本

---

## 1. 專案概述

### 1.1 什麼是 Lineart

Lineart 是一個**動漫角色設定稿提示詞生成器**，為 AI 繪圖模型（Stable Diffusion、MidJourney、NovelAI）產出結構化的線稿提示詞。使用者可以從內建角色庫選擇或自行定義角色特徵，選擇輸出類型（三視圖、表情集、服裝拆解等），獲得針對不同 AI 模型格式化的提示詞。

### 1.2 核心價值

- 減少手動撰寫複雜提示詞的時間
- 確保角色設定在所有輸出類型間保持一致
- 一次設定多種輸出格式（SD/MJ/NAI）的工具
- 雙語支援（中文 / English）

### 1.3 目標使用者

- 動漫角色設計師
- AI 繪圖使用者（SD / MJ / NovelAI）
- 概念美術設計師
- 角色設定愛好者

---

## 2. 功能規格

### 2.1 角色系統

#### 2.1.1 內建角色
- 提供 12 個預先設計的動漫角色，以 YAML 格式儲存
- 每個角色包含：
  - id — 唯一識別碼
  - label — 雙語名稱（zh/en）
  - gender — 雙語性別標籤
  - ase_style — 基底風格描述（雙語）
  - components — 角色元件（臉部、表情、姿勢、髮型、服裝）
  - outputs — 輸出類型定義（含標籤、風格描述、表情變體）
- 現有角色清單：sword_maiden, meiji_schoolgirl, bushi, court_lady, cyber_knight, fantasy_elf, kikai, magical_girl, republican_lady, rock_musician, ronin, sci_fi_mercenary

#### 2.1.2 自訂角色建構器
- 透過表單（CLI 參數或 Web 表單）定義客製角色
- 可編輯欄位：名稱（雙語）、性別、臉型、眼睛、表情、嘴巴、頭部角度、動作姿勢、髮型、飾品、外袍/上衣、領口、腰飾
- 所有欄位皆有雙語預設值，留空時自動套用

### 2.2 輸出模板系統

#### 2.2.1 可用模板（8 種）
| 模板 ID | 中文名稱 | 英文名稱 |
|---------|---------|---------|
| three_view | 人物三視圖 | Character Three-view Sheet |
| expressions | 表情演變五連圖 | Expression Evolution Sheet |
| clothing_breakdown | 服裝拆解圖 | Clothing Breakdown |
| hair_breakdown | 髮飾拆解圖 | Hair Accessory Breakdown |
| action_pose | 動態姿勢集 | Action Poses |
| chibi_version | Q版化 | Chibi Version |
| color_scheme | 配色方案 | Color Scheme |
| weapon_prop | 武器道具拆解 | Weapon/Prop Breakdown |

#### 2.2.2 中間格式
- 模板使用 ###KEY### 區塊標記作為中間格式
- 通用區塊：BASE, GENDER, FACE, EXPRESSION, HAIR, CLOTHING, OUTPUT
- 模板特定區塊：EXPRESSIONS, POSES, CHIBI_BASE, BREAKDOWN_LAYERS 等

### 2.3 AI 模型轉接器 (Adapter)

| 模型 | Adapter | 格式特點 |
|------|---------|---------|
| Stable Diffusion | StableDiffusionAdapter | 逗號分隔標籤，支援加權 (tag:1.3)，--ar 參數 |
| MidJourney | MidjourneyAdapter | 自然語言句子，--style raw --s 250 --v 6 參數 |
| NovelAI | NovelAIAdapter | 花括號加權 {tag}，附加品質標籤 |

### 2.4 使用者介面

#### 2.4.1 CLI
`
lineart generate <character> --type <output(s)> [--model sd|mj|nai] [--lang zh|en] [--ar <ratio>]
lineart generate --custom --name "角色名" ...
lineart list [characters|templates|outputs --character <id>]
`

#### 2.4.2 Web GUI
- Flask 單頁應用，雙標籤內建/自訂角色
- 結果顯示卡片 + 複製按鈕
- Ctrl+Enter 快捷鍵
- 響應式設計

### 2.5 國際化 (i18n)
- i18n/zh.yaml 與 i18n/en.yaml 雙語詞典

### 2.6 Prompt 歷史管理 (SQLite)

#### 2.6.1 自動記錄
- 每次成功產生提示詞後自動儲存至 SQLite 資料庫（lineart_history.db）
- 儲存粒度：**每種輸出類型一筆獨立記錄**
- 記錄欄位：id, created_at, mode, character, char_label, gender, model, lang, ar, output_type, prompt

#### 2.6.2 歷史頁面 (/history)
- 獨立頁面，完整表格 + 分頁 + 篩選 + 匯出（JSON/CSV）

#### 2.6.3 CLI 歷史子命令
`
lineart history list [--page N] [--model mj] [--type three_view]
lineart history show <id>
lineart history delete <id> | clear
lineart history export [--format json|csv] [--output FILE]
`

### 2.7 Web GUI 改善（HTMX + Alpine.js）

#### 2.7.1 HTMX 表單提交
- hx-post, hx-target, hx-indicator, hx-target-error 取代 Vanilla JS fetch
- 伺服器辨識 HX-Request header，回傳 HTML 片段

#### 2.7.2 Alpine.js UI 互動
- x-data, @click, x-show, :class 管理 Tab 切換與 UI 狀態
- 複製按鈕使用 Alpine.js 反應式狀態

---

## 3. 技術架構

### 3.1 目錄結構
`
lineart/
├── __main__.py, app.py, cli.py, engine.py
├── exceptions.py, schemas.py, history.py
├── pyproject.toml, requirements.txt, run.bat
├── adapters/ (5 files)
├── characters/ (12 YAML files)
├── templates/ (8 .j2 + index.html + _partials.html)
├── i18n/ (zh.yaml, en.yaml)
├── static/ (style.css)
└── tests/ (3 test files)
`

### 3.2 資料流 Pipeline
`
使用者輸入 → engine.py (YAML載入 + Jinja2渲染 → ###KEY###中間格式)
          → adapters/*.py (轉換為 SD/MJ/NAI 格式)
          → 輸出 + 自動儲存至 SQLite 歷史
`

### 3.3 依賴
- Python ≥3.11, PyYAML, Jinja2, Flask, Pydantic, sqlite3(內建)
- Dev: pytest, pytest-cov, ruff
- Frontend: HTMX 2.0+ (CDN), Alpine.js 3.14+ (CDN)
