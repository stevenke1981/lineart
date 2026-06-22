# Lineart 複刻執行計畫

> 版本：1.0 | 預估工時：17-20 hr

## 執行順序

| Phase | 內容 | 工時 |
|-------|------|------|
| 1 | 專案基礎建設 | 30 min |
| 2 | 核心引擎 (exceptions, schemas, engine, __main__) | 3 hr |
| 3 | Adapter 層 (5 檔) | 1.5 hr |
| 4 | CLI 介面 (cli.py + history 子命令) | 1.5 hr |
| 5 | Web GUI + SQLite History | 4.5 hr |
| 6 | 角色 YAML + 模板 + i18n | 2 hr |
| 7 | 測試 (79 個) | 2 hr |
| 8 | 整合驗證 + 文件 | 1 hr |

## 關鍵決策

- **ADR-1**: HTMX + Alpine.js 並用（表單提交 + UI 狀態）
- **ADR-2**: SQLite 內建模組，無 ORM
- **ADR-3**: 儲存粒度 = 單一輸出一筆記錄
- **ADR-4**: 歷史頁面 = 獨立 `/history` 路由
- **ADR-5**: engine.py 純粹無副作用，儲存由呼叫方負責
