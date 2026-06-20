# Lineart 專案改善實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**目標：** 將 Lineart 專案從 0% 測試覆蓋、無型別、無 lint、硬編碼 i18n 的狀態，提升至具備完整測試套件、型別安全、i18n 一致化、穩固基礎架構的生產級品質。

**架構方向：** 以 `pyproject.toml` 為中心統一管理工具設定與依賴，以 `pydantic` 強型別化角色 Schema，全面接入 i18n 系統，分三階段增量交付。

**技術棧：** Python 3.12+, pytest, ruff, pydantic, pyyaml, jinja2, flask, GitHub Actions

---

### Phase 1 — Foundation（建立基礎品質）

#### Task 1: 建立 pyproject.toml + ruff 設定

**Files:**
- Create: `D:\lineart\pyproject.toml`
- Modify: `D:\lineart\.gitignore`

- [ ] **Step 1: 建立 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "lineart"
version = "0.3.0"
description = "Anime character design prompt generator for AI image models"
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
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.ruff.format]
quote-style = "double"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: 更新 .gitignore 加入 pytest cache**

Add to .gitignore:
```
.pytest_cache/
```

- [ ] **Step 3: 執行 ruff 檢查當前程式碼**

Run: `ruff check . --select=E,F,I,N,W,UP`
Expected: List of lint issues (ok at this stage)

- [ ] **Step 4: 提交變更**

```bash
git add pyproject.toml .gitignore
git commit -m "chore: add pyproject.toml with ruff and pytest config"
```

---

#### Task 2: 補齊型別註釋

**Files:**
- Modify: `D:\lineart\engine.py`
- Modify: `D:\lineart\cli.py`
- Modify: `D:\lineart\app.py`
- Modify: `D:\lineart\adapters\__init__.py`
- Modify: `D:\lineart\adapters\base.py`
- Modify: `D:\lineart\adapters\stable_diffusion.py`
- Modify: `D:\lineart\adapters\midjourney.py`
- Modify: `D:\lineart\adapters\novelai.py`

- [ ] **Step 1: 補齊 engine.py 型別**

engine.py 已有部分型別，只需要：
- `build_custom_character` 回傳型別 `-> dict` 已存在
- 確認所有函式有完整參數與回傳型別

- [ ] **Step 2: 補齊 cli.py 型別**

```python
def main() -> None: ...
```

- [ ] **Step 3: 補齊 adapters 型別**

`base.py` — `_parse_blocks` 回傳 `dict[str, str]`，`_flatten_blocks` 回傳 `str`，`_normalize_punct` 回傳 `str`
`__init__.py` — `get_adapter` 回傳 `BaseAdapter`

- [ ] **Step 4: 補齊 app.py 型別**

```python
def get_characters_meta() -> list[dict]: ...
def get_all_templates_meta() -> list[dict]: ...
```

- [ ] **Step 5: 執行 ruff 確認型別問題**

Run: `ruff check . --select=E,F,I,N,W,UP`

- [ ] **Step 6: 提交變更**

```bash
git add -A
git commit -m "refactor: add type annotations across all modules"
```

---

#### Task 3: 撰寫核心引擎測試

**Files:**
- Create: `D:\lineart\tests\__init__.py`
- Create: `D:\lineart\tests\conftest.py`
- Create: `D:\lineart\tests\test_engine.py`

- [ ] **Step 1: 建立 tests/__init__.py**

Empty file

- [ ] **Step 2: 建立 conftest.py**

```python
"""Shared test fixtures."""
import sys
import pytest
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
```

- [ ] **Step 3: 撰寫 test_engine.py**

```python
"""Tests for engine.py — core pipeline."""

import pytest
from engine import (
    list_characters,
    load_character,
    list_templates,
    list_outputs,
    generate_prompt,
    build_custom_character,
)


class TestListCharacters:
    def test_returns_non_empty_list(self):
        chars = list_characters()
        assert isinstance(chars, list)
        assert len(chars) > 0

    def test_returns_sorted_strings(self):
        chars = list_characters()
        assert all(isinstance(c, str) for c in chars)
        assert chars == sorted(chars)


class TestLoadCharacter:
    def test_load_sword_maiden_returns_dict(self):
        char = load_character("sword_maiden")
        assert isinstance(char, dict)
        assert "id" in char
        assert char["id"] == "sword_maiden"
        assert "components" in char
        assert "outputs" in char

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            load_character("nonexistent_char_xyz")


class TestListTemplates:
    def test_returns_template_names(self):
        tmpls = list_templates()
        assert isinstance(tmpls, list)
        assert len(tmpls) > 0
        assert "three_view" in tmpls


class TestListOutputs:
    def test_returns_union_of_defined_and_all_templates(self):
        char = load_character("sword_maiden")
        outputs = list_outputs(char)
        all_templates = list_templates()
        # All defined outputs should be included
        for defined in char.get("outputs", {}):
            assert defined in outputs
        # All templates should be available
        for t in all_templates:
            assert t in outputs


class TestGeneratePrompt:
    def test_sd_three_view_returns_string(self):
        prompt = generate_prompt("three_view", model="sd", char_id="sword_maiden")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_mj_three_view_returns_string(self):
        prompt = generate_prompt("three_view", model="mj", char_id="sword_maiden")
        assert isinstance(prompt, str)
        assert "--style raw" in prompt
        assert "--v 6" in prompt

    def test_nai_three_view_returns_string(self):
        prompt = generate_prompt("three_view", model="nai", char_id="sword_maiden")
        assert isinstance(prompt, str)
        assert "best quality" in prompt

    def test_unknown_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            generate_prompt("three_view", model="unknown", char_id="sword_maiden")

    def test_unknown_template_raises(self):
        with pytest.raises(ValueError, match="not found"):
            generate_prompt("nonexistent_template", model="sd", char_id="sword_maiden")


class TestBuildCustomCharacter:
    def test_returns_valid_dict(self):
        char = build_custom_character({})
        assert isinstance(char, dict)
        assert char["id"] == "custom"
        assert "components" in char
        assert "outputs" in char

    def test_accepts_custom_fields(self):
        form = {"char_name": "忍者", "char_name_en": "Ninja"}
        char = build_custom_character(form)
        assert char["label"]["zh"] == "忍者"
        assert char["label"]["en"] == "Ninja"

    def test_falls_back_to_defaults(self):
        char = build_custom_character({})
        assert char["components"]["face"]["shape"]["zh"] == "瓜子臉"
        assert char["components"]["face"]["shape"]["en"] == "oval face"
```

- [ ] **Step 4: 執行測試確認通過**

Run: `python -m pytest tests/test_engine.py -v`
Expected: All tests PASS

- [ ] **Step 5: 提交**

```bash
git add tests/
git commit -m "test: add core engine unit tests"
```

---

#### Task 4: 撰寫 Adapter 測試

**Files:**
- Create: `D:\lineart\tests\test_adapters.py`

- [ ] **Step 1: 撰寫 test_adapters.py**

```python
"""Tests for adapters/ — model-specific prompt formatters."""

import pytest
from adapters import get_adapter, BaseAdapter
from adapters.stable_diffusion import StableDiffusionAdapter
from adapters.midjourney import MidjourneyAdapter
from adapters.novelai import NovelAIAdapter


class TestGetAdapter:
    def test_returns_sd_adapter(self):
        adapter = get_adapter("sd")
        assert isinstance(adapter, StableDiffusionAdapter)

    def test_returns_mj_adapter(self):
        adapter = get_adapter("mj")
        assert isinstance(adapter, MidjourneyAdapter)

    def test_returns_nai_adapter(self):
        adapter = get_adapter("nai")
        assert isinstance(adapter, NovelAIAdapter)

    def test_accepts_full_names(self):
        assert isinstance(get_adapter("stable_diffusion"), StableDiffusionAdapter)
        assert isinstance(get_adapter("midjourney"), MidjourneyAdapter)
        assert isinstance(get_adapter("novelai"), NovelAIAdapter)

    def test_unknown_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            get_adapter("unknown_model")


SAMPLE_INTERMEDIATE = """###BASE###
anime character sheet, black and white ink
###FACE###
oval face, big eyes
###OUTPUT###
style guide, character sheet"""


class TestBaseAdapterParseBlocks:
    def test_parse_blocks_correctly(self):
        adapter = StableDiffusionAdapter()
        blocks = adapter._parse_blocks(SAMPLE_INTERMEDIATE)
        assert blocks["BASE"] == "anime character sheet, black and white ink"
        assert blocks["FACE"] == "oval face, big eyes"
        assert blocks["OUTPUT"] == "style guide, character sheet"

    def test_parse_blocks_empty_text(self):
        adapter = StableDiffusionAdapter()
        blocks = adapter._parse_blocks("")
        assert blocks == {"HEADER": ""}


class TestBaseAdapterNormalizePunct:
    def test_zh_keeps_punct(self):
        adapter = StableDiffusionAdapter()
        result = adapter._normalize_punct("大眼睛，可愛", lang="zh")
        assert "，" in result

    def test_en_converts_punct(self):
        adapter = StableDiffusionAdapter()
        result = adapter._normalize_punct("大眼睛，可愛", lang="en")
        assert "，" not in result
        assert ", " in result


class TestStableDiffusionAdapter:
    def test_format_includes_weighting(self):
        adapter = StableDiffusionAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE)
        # BASE and OUTPUT should be weighted
        assert "anime character sheet, black and white ink" in result
        assert "style guide" in result


class TestMidjourneyAdapter:
    def test_format_includes_mj_params(self):
        adapter = MidjourneyAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE)
        assert "--style raw" in result
        assert "--v 6" in result

    def test_format_uses_default_ar(self):
        adapter = MidjourneyAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE)
        assert "--ar" in result


class TestNovelAIAdapter:
    def test_format_includes_quality_tags(self):
        adapter = NovelAIAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE)
        assert "best quality" in result
        assert "absurdres" in result
```

- [ ] **Step 2: 執行測試確認通過**

Run: `python -m pytest tests/test_adapters.py -v`
Expected: All tests PASS

- [ ] **Step 3: 執行完整測試套件**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: 提交**

```bash
git add tests/test_adapters.py
git commit -m "test: add adapter unit tests"
```

---

#### Task 5: 設定 GitHub Actions CI

**Files:**
- Create: `D:\lineart\.github\workflows\ci.yml`

- [ ] **Step 1: 建立 CI 設定**

```yaml
name: CI

on:
  push:
    branches: [main, master, dev]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov ruff
      - name: Lint with ruff
        run: ruff check . --select=E,F,I,N,W,UP
      - name: Test with pytest
        run: python -m pytest tests/ -v --cov=engine --cov=adapters --cov-report=term-missing
```

- [ ] **Step 2: 提交**

```bash
git add .github/
git commit -m "ci: add GitHub Actions CI with ruff and pytest"
```

---

### Phase 2 — i18n & Schema（核心品質改善）

#### Task 6: 建立角色 Pydantic Schema

**Files:**
- Create: `D:\lineart\schemas.py`
- Modify: `D:\lineart\engine.py`

- [ ] **Step 1: 建立 schemas.py**

```python
"""Pydantic schemas for character data validation."""

from typing import Optional
from pydantic import BaseModel


class BilingualField(BaseModel):
    zh: str
    en: str


class CharacterOutput(BaseModel):
    label: BilingualField
    style: BilingualField
    variants: Optional[list[dict]] = None


class CharacterComponents(BaseModel):
    face: dict
    expression: dict
    pose: dict
    hair: dict
    clothing: dict


class Character(BaseModel):
    id: str
    label: BilingualField
    base_style: BilingualField
    components: CharacterComponents | dict
    outputs: dict[str, CharacterOutput]
```

- [ ] **Step 2: 在 engine.py 中加入 validate_character() 函式**

In `engine.py`, add:

```python
from schemas import Character


def validate_character(char_data: dict) -> Character:
    """Validate and return a Character schema from raw dict."""
    return Character(**char_data)
```

Call it after `load_character` and `build_custom_character` if requested.

- [ ] **Step 3: 更新 tests/test_engine.py — 加入 schema 測試**

```python
from schemas import Character, BilingualField, CharacterOutput


class TestCharacterSchema:
    def test_sword_maiden_validates(self):
        char = load_character("sword_maiden")
        validated = Character(**char)
        assert validated.id == "sword_maiden"
        assert isinstance(validated.label, BilingualField)
        assert isinstance(validated.outputs["three_view"], CharacterOutput)

    def test_custom_character_validates(self):
        char = build_custom_character({})
        validated = Character(**char)
        assert validated.id == "custom"
```

- [ ] **Step 4: 執行測試**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS (need pydantic installed)

- [ ] **Step 5: 提交**

```bash
git add schemas.py engine.py tests/test_engine.py
git commit -m "feat: add Pydantic schemas for character validation"
```

---

#### Task 7: 模板移除硬編碼文字 + i18n 接入 Pipeline

**Files:**
- Modify: `D:\lineart\engine.py`
- Modify: `D:\lineart\i18n\zh.yaml`
- Modify: `D:\lineart\i18n\en.yaml`
- Modify: `D:\lineart\templates\chibi_version.j2`
- Modify: `D:\lineart\templates\color_scheme.j2`
- Modify: `D:\lineart\templates\weapon_prop.j2`
- Modify: `D:\lineart\templates\hair_breakdown.j2`
- Modify: `D:\lineart\templates\action_pose.j2`

- [ ] **Step 1: 將模板硬編碼文字移至 i18n 詞典**

在 `i18n/zh.yaml` 新增：
```yaml
templates:
  chibi_version:
    style: "Q版化，二頭身比例，頭大身小，可愛風格"
    face_zoom: "（放大）"
    cheek: "圓潤臉頰"
    hair_simplified: "（簡化）"
    clothing_simplified: "（簡化版）"
    poses:
      front: "Q版站立，大眼睛"
      side: "Q版側身，圓潤曲線"
      back: "Q版背面，細節簡化"
    output_label: "Q版角色設計圖集"
  color_scheme:
    hair_color: "髮色：黑色（墨黑），漸層灰色陰影"
    eye_color: "瞳色：留白處理，黑白對比"
    clothing_main: "主色調：黑色線稿，灰色中間調，白色留白"
    collar_shadow: "：深灰陰影"
    waist_contrast: "：高對比黑色"
    accessory_detail: "：精細線條，留白高光"
    output_label: "黑白配色方案，灰階層次對比圖"
  weapon_prop:
    main_title: "手持道具設計拆解圖"
    main_desc: "主體結構：三視圖展示（正面/側面/俯視）"
    detail_a: "細節A：握柄/裝飾處放大特寫"
    detail_b: "細節B：紋路/花紋細部描寫"
    part_1: "部件1：主體外形"
    part_2: "部件2：裝飾配件"
    part_3: "部件3：連接結構"
  hair_breakdown:
    flower_detail: "花朵髮飾：精細花瓣層次，纏絲工藝"
    tassel_detail: "流蘇垂墜：串珠流蘇，金屬墜飾"
  action_pose:
    pos2_desc: "跳躍動作，動態飄逸"
    pos3_desc: "戰鬥姿勢，全身構圖"
    pos4_desc: "角色比例圖，身高標示"
    output_label: "人物動態姿勢集，角色比例指南"
```

在 `i18n/en.yaml` 新增對應的英文翻譯。

- [ ] **Step 2: engine.py 中將 i18n 字典傳入模板渲染**

修改 `render_template()` 和 `generate_prompt()` 以載入並傳遞 i18n 字典：

```python
def render_template(template_name: str, char_data: dict, lang: str = "zh") -> str:
    env = _get_env()
    template = env.get_template(template_name)
    i18n = load_i18n(lang)
    return template.render(char=char_data, lang=lang, i18n=i18n)
```

- [ ] **Step 3: 更新各模板使用 i18n 變數取代硬編碼文字**

chibi_version.j2:
```jinja2
{%- set lang = lang or 'zh' -%}
{%- set c = char.components -%}
{%- set o = char.outputs.chibi_version -%}
###BASE###
{{ char.base_style[lang] }}
###CHIBI_BASE###
{{ i18n.templates.chibi_version.style }}
###FACE###
{{ c.face.shape[lang] }}，{{ c.face.eyes[lang] }}{{ i18n.templates.chibi_version.face_zoom }}，{{ i18n.templates.chibi_version.cheek }}
###EXPRESSION###
{{ c.expression.type[lang] }}，{{ c.expression.mouth[lang] }}
###HAIR###
{{ c.hair.style[lang] }}{{ i18n.templates.chibi_version.hair_simplified }}，{% for acc in c.hair.accessories %}{{ acc[lang] }}{% if not loop.last %}，{% endif %}{% endfor %}
###CLOTHING###
{{ c.clothing.robe[lang] }}{{ i18n.templates.chibi_version.clothing_simplified }}，{{ c.clothing.collar[lang] }}
###CHIBI_POSES###
[正面] {{ i18n.templates.chibi_version.poses.front }}
[側面] {{ i18n.templates.chibi_version.poses.side }}
[背面] {{ i18n.templates.chibi_version.poses.back }}
###OUTPUT###
{{ o.style[lang] }}，{{ i18n.templates.chibi_version.output_label }}
```

color_scheme.j2:
```jinja2
{%- set lang = lang or 'zh' -%}
{%- set c = char.components -%}
{%- set o = char.outputs.color_scheme -%}
###BASE###
{{ char.base_style[lang] }}
###HAIR###
{{ c.hair.style[lang] }}
{{ i18n.templates.color_scheme.hair_color }}
###EYES###
{{ c.face.eyes[lang] }}
{{ i18n.templates.color_scheme.eye_color }}
###CLOTHING###
{{ c.clothing.robe[lang] }}
{{ i18n.templates.color_scheme.clothing_main }}
{{ c.clothing.collar[lang] }}{{ i18n.templates.color_scheme.collar_shadow }}
{{ c.clothing.waist[lang] }}{{ i18n.templates.color_scheme.waist_contrast }}
###ACCESSORIES###
{% for acc in c.hair.accessories %}{{ acc[lang] }}{{ i18n.templates.color_scheme.accessory_detail }}
{% endfor %}
###OUTPUT###
{{ o.style[lang] }}，{{ i18n.templates.color_scheme.output_label }}
```

weapon_prop.j2:
```jinja2
{%- set lang = lang or 'zh' -%}
{%- set c = char.components -%}
{%- set o = char.outputs.weapon_prop -%}
###BASE###
{{ char.base_style[lang] }}
###CHARACTER_CARRYING###
{{ c.clothing.robe[lang] }}，{{ c.pose.action[lang] }}
###PROP_MAIN###
{{ i18n.templates.weapon_prop.main_title }}
{{ i18n.templates.weapon_prop.main_desc }}
###PROP_DETAILS###
{{ i18n.templates.weapon_prop.detail_a }}
{{ i18n.templates.weapon_prop.detail_b }}
###PROP_BREAKDOWN###
{{ i18n.templates.weapon_prop.part_1 }}
{{ i18n.templates.weapon_prop.part_2 }}
{{ i18n.templates.weapon_prop.part_3 }}
###OUTPUT###
{{ o.style[lang] }}，道具設計拆解圖
```

hair_breakdown.j2:
```jinja2
{%- set lang = lang or 'zh' -%}
{%- set c = char.components -%}
{%- set o = char.outputs.hair_breakdown -%}
###BASE###
{{ char.base_style[lang] }}
###HAIR_STYLE###
{{ c.hair.style[lang] }}
###ACCESSORIES###
{% for acc in c.hair.accessories %}- {{ acc[lang] }}
{% endfor %}
###DETAILS###
{{ i18n.templates.hair_breakdown.flower_detail }}
{{ i18n.templates.hair_breakdown.tassel_detail }}
###OUTPUT###
{{ o.style[lang] }}，{{ o.label[lang] }}
```

action_pose.j2:
```jinja2
{%- set lang = lang or 'zh' -%}
{%- set c = char.components -%}
{%- set o = char.outputs.action_pose -%}
###BASE###
{{ char.base_style[lang] }}
###FACE###
{{ c.face.shape[lang] }}，{{ c.face.eyes[lang] }}
###EXPRESSION###
{{ c.expression.type[lang] }}，{{ c.expression.mouth[lang] }}
###HAIR###
{{ c.hair.style[lang] }}，{% for acc in c.hair.accessories %}{{ acc[lang] }}{% if not loop.last %}，{% endif %}{% endfor %}
###CLOTHING###
{{ c.clothing.robe[lang] }}，{{ c.clothing.collar[lang] }}，{{ c.clothing.waist[lang] }}
###POSES###
[POS1] {{ c.pose.action[lang] }}，{{ c.pose.head_angle[lang] }}
[POS2] {{ i18n.templates.action_pose.pos2_desc }}
[POS3] {{ i18n.templates.action_pose.pos3_desc }}
[POS4] {{ i18n.templates.action_pose.pos4_desc }}
###OUTPUT###
{{ o.style[lang] }}，{{ i18n.templates.action_pose.output_label }}
```

- [ ] **Step 4: 執行測試確認一切正常**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS (output may differ slightly from before due to i18n changes)

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "feat: i18n integration for templates, remove hardcoded text"
```

---

#### Task 8: 模板輸出型別 fallback 機制

**Files:**
- Modify: `D:\lineart\engine.py`

- [ ] **Step 1: 在 generate_prompt() 中改進 fallback 機制**

Current code creates empty output type if not defined. Improve it to use template-safe defaults:

```python
# 3. Ensure safe output type entry exists with fallback
if "outputs" not in char_data:
    char_data["outputs"] = {}
if output_type not in char_data["outputs"]:
    char_data["outputs"][output_type] = {
        "label": {"zh": output_type, "en": output_type},
        "style": {"zh": "", "en": ""},
    }
else:
    # Ensure every variant list field exists
    output_def = char_data["outputs"][output_type]
    if "variants" not in output_def:
        output_def["variants"] = []
    if "label" not in output_def:
        output_def["label"] = {"zh": output_type, "en": output_type}
    if "style" not in output_def:
        output_def["style"] = {"zh": "", "en": ""}
```

- [ ] **Step 2: 修改 list_outputs() 分離定義與模板**

Add new functions:
```python
def get_defined_outputs(char_data: dict) -> list[str]:
    """Return output types that a character actually defines."""
    return sorted(char_data.get("outputs", {}).keys())

def get_compatible_outputs(char_data: dict) -> list[str]:
    """Return output types that can be safely used with this character."""
    defined = set(get_defined_outputs(char_data))
    all_templates = set(list_templates())
    return sorted(defined | all_templates)
```

Keep `list_outputs()` as alias for backward compat or update callers.

- [ ] **Step 3: 執行測試**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: 提交**

```bash
git add engine.py
git commit -m "feat: add output type fallback and get_defined_outputs() API"
```

---

### Phase 3 — 穩定性與品質

#### Task 9: CLI 錯誤處理改用命名例外

**Files:**
- Create: `D:\lineart\exceptions.py`
- Modify: `D:\lineart\engine.py`
- Modify: `D:\lineart\cli.py`
- Modify: `D:\lineart\adapters\__init__.py`

- [ ] **Step 1: 建立 exceptions.py**

```python
"""Custom exceptions for Lineart."""


class LineartError(Exception):
    """Base exception for all Lineart errors."""


class CharacterNotFoundError(LineartError, FileNotFoundError):
    """Raised when a character YAML file is not found."""


class TemplateNotFoundError(LineartError, ValueError):
    """Raised when a template file is not found."""


class ModelNotSupportedError(LineartError, ValueError):
    """Raised when an unsupported model is requested."""


class LanguageNotFoundError(LineartError, FileNotFoundError):
    """Raised when an i18n language file is not found."""
```

- [ ] **Step 2: 在 engine.py 中改用自訂例外**

Replace `raise FileNotFoundError(...)` with `raise CharacterNotFoundError(...)` in `load_character()`
Replace `raise ValueError(...)` with `raise TemplateNotFoundError(...)` in `generate_prompt()`
Replace `raise FileNotFoundError(...)` with `raise LanguageNotFoundError(...)` in `load_i18n()`

- [ ] **Step 3: 在 adapters/__init__.py 中改用自訂例外**

```python
from exceptions import ModelNotSupportedError

def get_adapter(model: str) -> BaseAdapter:
    ...
    raise ModelNotSupportedError(...)
```

- [ ] **Step 4: 簡化 cli.py 的錯誤處理**

將全域 `except Exception` 改為捕獲特定例外：

```python
except LineartError as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}", file=sys.stderr)
    sys.exit(1)
```

- [ ] **Step 5: 更新測試以捕獲新的例外類型**

```python
# Change pytest.raises to catch new exception types
with pytest.raises(CharacterNotFoundError):
    load_character("nonexistent")
```

- [ ] **Step 6: 執行測試**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 7: 提交**

```bash
git add exceptions.py engine.py adapters/__init__.py cli.py tests/
git commit -m "refactor: add custom exception hierarchy, improve CLI error handling"
```

---

#### Task 10: 引入 logging 取代 print

**Files:**
- Modify: `D:\lineart\engine.py`
- Modify: `D:\lineart\cli.py`
- Modify: `D:\lineart\app.py`

- [ ] **Step 1: 在 engine.py 中加入 logging**

```python
import logging
logger = logging.getLogger(__name__)
```

Add key log messages in pipeline functions.

- [ ] **Step 2: 在 cli.py 中加入 logging**

Replace `print("Error: ...")` with `logger.error()` calls, keep user-facing output via `print()`.

- [ ] **Step 3: 在 app.py 中加入 logging**

```python
import logging
logger = logging.getLogger(__name__)
```

- [ ] **Step 4: 執行測試**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 5: 提交**

```bash
git add engine.py cli.py app.py
git commit -m "refactor: replace print with logging framework"
```

---

#### Task 11: 相依性版本鎖定

**Files:**
- Modify: `D:\lineart\requirements.txt`

- [ ] **Step 1: 在 requirements.txt 中加入版本下限**

```
pyyaml>=6.0,<7.0
jinja2>=3.0,<4.0
flask>=3.0,<4.0
```

- [ ] **Step 2: 提交**

```bash
git add requirements.txt
git commit -m "chore: tighten dependency version ranges"
```

---

#### Task 12: 最終 Code Review + 全面測試

- [ ] **Step 1: 執行 ruff lint 檢查**

Run: `ruff check . --select=E,F,I,N,W,UP`
Fix any remaining issues

- [ ] **Step 2: 執行完整測試套件**

Run: `python -m pytest tests/ -v --cov=engine --cov=adapters --cov-report=term-missing`
Verify coverage > 80%

- [ ] **Step 3: 執行手動冒煙測試**

```bash
python -m lineart generate sword_maiden --type three_view --model sd
python -m lineart generate sword_maiden --type three_view --model mj
python -m lineart generate sword_maiden --type three_view --model nai
python -m lineart list characters
python -m lineart list outputs --character sword_maiden
```

- [ ] **Step 4: 最終提交**

```bash
git add -A
git commit -m "chore: final code review and cleanup"
```
