# Lineart 專案分析與改善優化建議

> 分析日期：2026-06-21  
> 分析範圍：完整原始碼（engine.py、cli.py、app.py、adapters/、templates/、characters/、i18n/）

---

## 目錄

1. [概觀與評價](#1-概觀與評價)
2. [P0 — 必須改善](#2-p0--必須改善)
3. [P1 — 高度建議](#3-p1--高度建議)
4. [P2 — 值得優化](#4-p2--值得優化)
5. [P3 — 未來展望](#5-p3--未來展望)
6. [改善路線圖](#6-改善路線圖)

---

## 1. 概觀與評價

### 專案定位 ★★★★☆

Lineart 是一個**動漫角色設定稿提示詞生成工具**，為 Stable Diffusion、MidJourney、NovelAI 等 AI 繪圖模型輸出格式化的線稿提示詞。專案架構清晰、程式碼簡潔、Adapter 策略模式運用恰當，以極少的程式碼（約 700 行）實現了完整的功能。

### 當前得分

| 面向 | 分數 | 說明 |
|------|------|------|
 | 架構設計 | 8/10 | Adapter 模式正確，engine 角色分明 |
| 程式碼可讀性 | 7/10 | 簡潔但缺型別與 docstring |
| 測試覆蓋 | 0/10 | 完全無測試 |
| i18n 完整性 | 4/10 | 架構有但實際上幾乎未使用 |
| 型別安全 | 4/10 | 部分 engine 有型別，其他欠缺 |
| 錯誤處理 | 5/10 | CLI 和 Web 不一致 |
| 可維護性 | 6/10 | 模板中有大量硬編碼 |
| 可復現性 | 3/10 | 無鎖定版本、無 lint、無格式化設定 |

---

## 2. P0 — 必須改善

### 2.1 加入單元測試

**嚴重性：** 🔴 高  
**現狀：** 完全無測試，整個專案 0% 測試覆蓋。  
**風險：** 任何重構或新增功能都可能無意間破壞 pipeline，且無從察覺。  
**建議：**

```python
# tests/test_engine.py — 最小可行測試集
# 1. engine.list_characters() 回傳不為空
# 2. engine.load_character("sword_maiden") 回傳合法 dict
# 3. engine.generate_prompt("three_view", model="sd") 回傳非空字串
# 4. engine.generate_prompt("three_view", model="mj") — MidJourney 格式正確
# 5. engine.generate_prompt("three_view", model="nai") — NovelAI 格式正確
# 6. engine.build_custom_character() 回傳結構正確
# 7. adapter._parse_blocks() 正確解析 ###KEY### 格式
# 8. adapter._normalize_punct() 正確轉換標點
```

**應對措施：**
- 使用 `pytest` + `pytest-cov`
- 優先覆蓋 `engine.py`（核心 pipeline）和 `adapters/*.py`（格式轉換）
- 目標：核心 pipeline > 90% coverage

### 2.2 模板 i18n 一致化

**嚴重性：** 🔴 高  
**現狀：** 
- `engine.py` 有 `load_i18n()` 函式，但**完全未在 pipeline 中使用**
- `i18n/zh.yaml` 和 `i18n/en.yaml` 存在但幾乎無用
- 多個模板硬編碼中文文字：

  | 模板 | 硬編碼問題 |
  |------|-----------|
  | `chibi_version.j2` | `Q版化，二頭身比例`、`放大`、`圓潤臉頰`、`簡化` |
  | `color_scheme.j2` | `髮色：黑色`、`瞳色：留白處理`、`主色調：黑色線稿` |
  | `weapon_prop.j2` | `手持道具設計拆解圖`、`主體結構`、`部件1`~`部件3` |
  | `action_pose.j2` | 待確認，但很可能也有類似問題 |

**建議：**
- 將所有模板中的顯示名稱文字移至角色 YAML 的 `outputs` 定義或 i18n 詞典
- 在 `engine.generate_prompt()` 中實際調用 `load_i18n()` 並傳遞給模板
- 範例修正：

```diff
# chibi_version.j2 (修正前)
- Q版化，二頭身比例，頭大身小，可愛風格
+ {{ char.outputs.chibi_version.style[lang] }}
```

### 2.3 角色 YAML Schema 驗證

**嚴重性：** 🔴 高  
**現狀：** 
- YAML 角色檔無結構驗證
- 若某個角色缺少 `outputs.three_view.style`，模板渲染時會報 `NoneType` 錯誤
- `engine.list_outputs()` 回傳**所有模板檔案**（即使角色未定義該輸出類型），但模板存取 `char.outputs.xxx.style` 時若無定義則崩潰

**建議：**
- 導入 `pydantic` 或 `dataclass` 定義角色 Schema
- 在 `load_character()` 時執行驗證
- `list_outputs()` 應區分「角色已定義」與「通用模板可用」

```python
from pydantic import BaseModel
from typing import Optional

class BilingualField(BaseModel):
    zh: str
    en: str

class CharacterOutput(BaseModel):
    label: BilingualField
    style: BilingualField
    variants: Optional[list[dict]] = None

class Character(BaseModel):
    id: str
    label: BilingualField
    base_style: BilingualField
    components: dict
    outputs: dict[str, CharacterOutput]
```

---

## 3. P1 — 高度建議

### 3.1 補齊型別註釋

**嚴重性：** 🟠 中高  
**現狀：**
- `engine.py` 有部分型別（`Optional`, `list[str]`）— ✅
- `cli.py` — 所有函式無型別註釋 ❌
- `adapters/*.py` — 方法無回傳值型別 ❌
- `app.py` — 部分函式無型別 ❌

**建議：** 全面導入 `pyright` 或 `mypy` 並補齊型別：

```python
# cli.py 範例
def main() -> None: ...
def parse_args() -> argparse.Namespace: ...
def handle_generate(args: argparse.Namespace) -> None: ...
def handle_list(args: argparse.Namespace) -> None: ...
```

### 3.2 導入 Ruff（Lint + Format 一體）

**嚴重性：** 🟠 中  
**現狀：** 無任何 lint 或 formatting 工具。  
**建議：** 使用 `ruff` 單一工具同時處理 lint 與 format：

```bash
pip install ruff
```

在 `pyproject.toml` 中設定：

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.ruff.format]
quote-style = "double"
```

加入 GitHub Actions 或 pre-commit hook。

### 3.3 相依性版本鎖定

**嚴重性：** 🟠 中  
**現狀：**
```
pyyaml>=6.0
jinja2>=3.0
flask>=3.0
```

使用 `>=` 而非 `==`，無法保證可復現的安裝。  
**建議：** 改用 `requirements.in`（手動維護）搭配 `pip-compile` 產出 `requirements.txt`（鎖定版），或改用 `pyproject.toml` + `uv`。

### 3.4 建立 pyproject.toml

**嚴重性：** 🟠 中  
**現狀：** 專案根目錄無 `pyproject.toml`，依賴管理依賴 `requirements.txt`。  
**建議：** 建立 `pyproject.toml` 集中管理 metadata、依賴、工具設定：

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "lineart"
version = "0.2.0"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0",
    "jinja2>=3.0",
    "flask>=3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov>=5",
    "ruff>=0.5",
    "pyright>=1.1",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

## 4. P2 — 值得優化

### 4.1 錯誤處理一致化

**現狀問題：**
- `cli.py` 使用全域 `try/except Exception` 捕獲所有錯誤（喪失除錯資訊）
- `engine.py` 拋出具名例外（`FileNotFoundError`, `ValueError`）— ✅
- `app.py` Flask 路由個別處理錯誤

**建議：**
- CLI 改用具名例外處理而非統一 `except Exception`
- 考慮加入自訂例外類別：

```python
class LineartError(Exception): ...
class CharacterNotFoundError(LineartError): ...
class TemplateNotFoundError(LineartError): ...
class ModelNotSupportedError(LineartError): ...
```

### 4.2 Jinja2 全域快取

**現狀：** `_jinja_env` 是模組層級全域變數，在測試環境中可能造成狀態污染。  
**建議：** 改用 `lru_cache` 或 factory function：

```python
from functools import cache

@cache
def _get_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
```

### 4.3 角色輸出類型與模板對齊

**現狀：**
- `engine.list_outputs()` 回傳角色已定義 + 所有模板檔案的路集
- 但若角色缺少某模板的定義，模板執行時要求存取 `char.outputs.xxx.style` 會崩潰

**建議方案 A（推薦）：** 分離為更明確的方法：
- `get_defined_outputs(char_id)` → 只回傳角色有定義的
- `get_available_templates()` → 回傳所有模板
- `get_compatible_outputs(char_id)` → 回傳角色能安全使用的（已定義 + 通用）

**建議方案 B：** 在 `generate_prompt()` 中補上 fallback 語意，確保就算 output 無定義也不會崩潰。

### 4.4 改進 `build_custom_character` 設計

**現狀：**
- 內部使用巢狀 closure（`val()`, `t()`），每次呼叫都重新定義
- 12 個雙語欄位用 `_en` 後綴手動配對
- 預設值定義在函式內部，難以覆寫或擴展

**建議：** 抽取為 `CharacterForm` dataclass：

```python
@dataclass
class BilingualField:
    zh: str
    en: str

@dataclass
class CharacterForm:
    name: BilingualField
    face_shape: BilingualField = field(default_factory=lambda: BilingualField("瓜子臉", "oval face"))
    eyes: BilingualField = field(default_factory=lambda: BilingualField("大眼睛", "big eyes"))
    # ...

    def build(self) -> dict:
        return { ... }
```

### 4.5 日誌系統

**現狀：** 使用 `print()` 輸出錯誤資訊，無日誌級別、無檔案輸出、無法除錯。  
**建議：** 引入 `logging`：

```python
import logging
logger = logging.getLogger(__name__)

# 在 engine.py 中使用
logger.info("Generating prompt: type=%s, model=%s", output_type, model)
logger.warning("Output type '%s' not defined for character, using fallback", output_type)
```

### 4.6 範例角色多樣化

**現狀：** 7 個角色全為女性。  
**建議：** 加入 2–3 個男性角色（如武將、忍者、機械師），增加角色應用的廣度與展示效果。

---

## 5. P3 — 未來展望

### 5.1 支援更多 AI 模型

當前支援 SD / MJ / NAI。可考慮加入：
- **DALL·E 3** — 自然語言描述格式
- **ComfyUI Workflow** — JSON 工作流匯出
- **FLUX / SD3** — 新興模型格式

### 5.2 角色 prompt 歷史與管理

- 新增「已生成 prompt 歷史」功能（CLI 寫入檔案、Web 用 session 或 SQLite）
- 角色自訂內容可匯出/匯入 JSON

### 5.3 批次與腳本模式

- 從 CSV/JSON 檔案批次載入多角色、多輸出類型、多模型
- 支援 `--batch` CLI 參數指定輸入檔案

### 5.4 Web GUI 改善

- 加入角色設定圖片即時預覽（用 SVG 示意或 CSS 渲染）
- 前端使用適當框架（如 HTMX 或 Alpine.js）提升互動性
- 角色欄位支援雙語同時輸入

---

## 6. 改善路線圖

### Phase 1 — Foundation（1–2 天）
| # | 任務 | 預計工時 |
|---|------|----------|
| 1 | 建立 `pyproject.toml` + `ruff` 設定 | 30 min |
| 2 | 補齊型別註釋（engine + adapters） | 1 hr |
| 3 | 撰寫核心測試（`tests/test_engine.py`） | 2 hr |
| 4 | 撰寫 adapter 測試（`tests/test_adapters.py`） | 1.5 hr |
| 5 | 設定 CI（GitHub Actions），執行 pytest + ruff | 1 hr |

### Phase 2 — i18n 與 Schema（1–2 天）
| # | 任務 | 預計工時 |
|---|------|----------|
| 6 | 建立角色 Pydantic Schema | 1.5 hr |
| 7 | 所有模板移除硬編碼文字，改從角色 YAML 或 i18n 讀取 | 2.5 hr |
| 8 | `load_i18n()` 接入 pipeline | 0.5 hr |
| 9 | 模板 fallback 機制（output 未定義時使用預設值） | 1 hr |

### Phase 3 — 穩定性與品質（1 天）
| # | 任務 | 預計工時 |
|---|------|----------|
| 10 | CLI 錯誤處理改用具名例外 | 1 hr |
| 11 | 引入 logging 取代 print | 1 hr |
| 12 | 相依性版本鎖定（pip-compile 或 uv） | 0.5 hr |
| 13 | 送出全面 code review | 1 hr |

### Phase 4 — 功能擴展（可選）
| # | 任務 | 預計工時 |
|---|------|----------|
| 14 | 新增 2–3 個男性角色 | 1 hr |
| 15 | 批次模式（CSV/JSON 輸入） | 2 hr |
| 16 | 支援 DALL·E 3 格式 | 1 hr |

---

## 總結

| 優先級 | 數量 | 主要影響 |
|--------|------|----------|
| P0 (必須) | 3 | 無測試、i18n 不可用、Schema 無驗證 |
| P1 (高度) | 4 | 型別、lint、相依性、專案設定 |
| P2 (值得) | 6 | 錯誤處理、日誌、模板對齊、API 設計 |
| P3 (未來) | 4 | 多模型、批次、Web 改善 |

**建議立即啟動 Phase 1 以建立品質基礎，再進到 Phase 2 解決核心的 i18n 與 Schema 問題。**
