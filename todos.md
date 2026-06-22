# Lineart 複刻任務清單

## Phase 1: 專案基礎建設
- [x] 1.1 建立完整目錄結構
- [x] 1.2 編寫 pyproject.toml (+pydantic)
- [x] 1.3 編寫 requirements.txt (+pydantic)
- [x] 1.4 初始化虛擬環境 + 安裝依賴
- [x] 1.5 編寫 run.bat (已存在)
- [x] 1.6 編寫 .gitignore (+ lineart_history.db)

## Phase 2: 核心引擎
- [ ] 2.1 exceptions.py — 自訂例外類別
- [ ] 2.2 schemas.py — Pydantic 資料模型
- [ ] 2.3 engine.py — 路徑、i18n、角色載入
- [ ] 2.4 engine.py — 自訂角色建構器
- [ ] 2.5 engine.py — 模板引擎與生成 Pipeline
- [ ] 2.6 __main__.py — python -m 入口

## Phase 3: Adapter 層
- [ ] 3.1 adapters/base.py
- [ ] 3.2 adapters/stable_diffusion.py
- [ ] 3.3 adapters/midjourney.py
- [ ] 3.4 adapters/novelai.py
- [ ] 3.5 adapters/__init__.py

## Phase 4: CLI 介面
- [ ] 4.1 cli.py — generate + list 子命令
- [ ] 4.2 cli.py — history 子命令

## Phase 5: Web GUI + SQLite History
- [ ] 5a.1 app.py — Flask 路由 (含歷史路由)
- [ ] 5a.2 templates/index.html — 基礎 HTML
- [ ] 5a.3 static/style.css — 樣式表
- [ ] 5b.1 history.py — SQLite 資料庫層
- [ ] 5c.1 templates/index.html — 重寫為 HTMX + Alpine.js
- [ ] 5c.2 templates/_result_card.html + _error.html
- [ ] 5c.3 templates/history.html — 歷史頁面
- [ ] 5c.4 templates/_history_rows.html — HTMX 片段

## Phase 6: 角色與模板資料
- [ ] 6a i18n/zh.yaml + en.yaml
- [ ] 6b 12 個角色 YAML
- [ ] 6c 8 個 Jinja2 模板

## Phase 7: 測試
- [ ] 7.1 tests/conftest.py
- [ ] 7.2 tests/test_engine.py (27 tests)
- [ ] 7.3 tests/test_adapters.py (33 tests)
- [ ] 7.4 tests/test_history.py (19 tests)

## Phase 8: 整合驗證
- [ ] 8.1 ruff check + pytest 全部通過
- [ ] 8.2 E2E 手動驗證
- [ ] 8.3 完成報告
