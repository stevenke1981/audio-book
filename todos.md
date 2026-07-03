# 任務清單 (todos)

## Phase 1 — 規劃文件

- [x] plan.md — 實作計畫
- [x] spec.md — 技術規格
- [x] todos.md — 本文件
- [x] test.md — 驗收測試規格

## Phase 2 — 專案骨架

- [x] .gitignore
- [x] requirements.txt / requirements-dev.txt
- [x] config.py（預設設定）
- [x] config.example.yaml
- [x] README.md
- [x] 目錄：book_to_convert/, audiobooks/, src/, tests/

## Phase 3 — 核心模組

- [x] src/settings.py — 設定載入（config + env + CLI）
- [x] src/text_extractor.py — 多格式文字擷取
- [x] src/chunker.py — 智慧分塊
- [x] src/qwen_client.py — Gradio API 封裝
- [x] src/audio_processor.py — 合併與匯出
- [x] src/progress.py — 進度 JSON 持久化
- [x] src/converter.py — 主轉換流程
- [x] audiobook_converter.py — CLI 入口

## Phase 4 — 功能優化

- [x] CLI 完整參數（speaker/language/format/config/file）
- [x] Voice Design 模式
- [x] 進度續傳 --resume / --force-restart
- [x] 快取修正（不刪除 cache/audio_chunks）
- [x] 環境變數 QWEN_API_URL
- [x] --check-api 健康檢查
- [x] --dry-run 預覽模式
- [x] FFmpeg 啟動檢查

## Phase 5 — 測試與驗收

- [x] tests/test_chunker.py
- [x] tests/test_text_extractor.py
- [x] tests/test_settings.py
- [x] tests/test_progress.py
- [x] pytest 全部通過（19/19）
- [x] CLI --help 驗證

## Phase 6 — 交付

- [x] final.md 驗收報告
- [x] git init + commit
- [x] push 至 github.com/stevenke1981/audio-book