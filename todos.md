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

## Phase 7 — 改善優化（cbm 審查後新增）

### P0 可靠性

- [ ] 部分失敗處理：`converter.py:275` + `audio_processor.combine_chunks` 缺塊時插入靜音佔位或依門檻中止，回報明確
- [ ] `settings.settings_hash` 補入所有語音參數（model_size/model_id/seed/language/bitrate 等）
- [ ] `converter.get_cache_path` 快取鍵同步納入 model/seed/language
- [ ] 新增 `tests/test_qwen_client.py`（mock gradio_client：三種模式 + 端點解析）
- [ ] 新增 `tests/test_audio_processor.py`（合併全成功/部分缺塊/全失敗、cache restore、cleanup）
- [ ] 新增 `tests/test_converter.py`（dry-run、retry 成功/失敗、cache path 一致性）
- [ ] 新增 `tests/test_cli.py`（argparse 參數、錯誤路徑、exit code）

### P1 相容性與正確性

- [ ] `_generate_voice_clone` 改用 `_resolve_api_name("/generate_voice_clone", "/run_voice_clone")`
- [ ] `_resolve_api_name` 無匹配時丟出明確 `ValueError`
- [ ] `clean_text` 頁碼正則收斂或預設關閉，補誤刪測試（Chapter 42 / 年份）
- [ ] 補 PDF / EPUB / DOCX 擷取測試（小型 fixture）

### P2 文件與設定

- [ ] `spec.md §3` 模組圖已對齊實際 import（本輪完成）
- [ ] `final.md` 標示 4 項本機驗證項目為未驗證（本輪完成）
- [ ] `config.example.yaml` 擴充涵蓋所有語音模式與設定群組
- [ ] 規劃 PyPDF2 → `pypdf` 遷移
- [ ] `_print_banner` 空 `voice_clone_ref_audio` 顯示 N/A