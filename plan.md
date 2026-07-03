# Qwen3 Audiobook Converter — 實作計畫

## 目標

完整復刻 [WhiskeyCoder/Qwen3-Audiobook-Converter](https://github.com/WhiskeyCoder/Qwen3-Audiobook-Converter)，並在保持相容性的前提下加入功能優化，推送至 [stevenke1981/audio-book](https://github.com/stevenke1981/audio-book)。

## 階段規劃

### Phase 1：規劃與規格（本階段）

| 產出 | 說明 |
|------|------|
| `plan.md` | 整體實作計畫與里程碑 |
| `spec.md` | 功能規格、API 契約、模組設計 |
| `todos.md` | 可追蹤任務清單 |
| `test.md` | 驗收標準與測試案例 |

### Phase 2：核心復刻

1. **文字擷取**：TXT / PDF / EPUB / DOCX / DOC，與原版邏輯一致
2. **智慧分塊**：依句子邊界切分，預設 1500 字
3. **Qwen TTS 整合**：Custom Voice、Voice Clone（含自動轉錄）
4. **音訊組裝**：pydub + FFmpeg 合併為 MP3
5. **快取與重試**：MD5 快取、指數退避重試
6. **目錄結構**：`book_to_convert/`、`audiobooks/`、`chunks/`、`cache/`、`logs/`

### Phase 3：功能優化

| 優化項 | 說明 | 優先級 |
|--------|------|--------|
| 模組化架構 | 拆分 extractor / chunker / client / processor | P0 |
| CLI 增強 | `--speaker`、`--language`、`--format`、`--config` | P0 |
| 進度續傳 | JSON 狀態檔，中斷後 `--resume` 繼續 | P0 |
| Voice Design | 支援 config.py 已定義的 voice_design 模式 | P1 |
| 多輸出格式 | mp3 / wav / flac / ogg | P1 |
| 快取修正 | 清理僅刪暫存 chunks，保留 audio cache | P1 |
| 環境變數 | `QWEN_API_URL` 覆寫預設端點 | P1 |
| 章節偵測 | EPUB spine 章節標題輸出 metadata | P2 |
| 健康檢查 | `--check-api` 驗證 Gradio 連線 | P2 |
| 單元測試 | chunker、extractor、config 無需 API 的測試 | P0 |

### Phase 4：驗收與交付

1. 執行 `pytest tests/ -v`
2. 執行 CLI `--help` 與 dry-run 流程
3. 撰寫 `final.md` 驗收報告
4. `git init` → commit → push 至遠端

## 專案結構

```
audio-book/
├── audiobook_converter.py    # CLI 入口（相容原版呼叫方式）
├── config.py                 # 預設設定（可被 CLI / YAML 覆寫）
├── config.example.yaml       # 範例設定檔
├── requirements.txt
├── requirements-dev.txt
├── src/
│   ├── converter.py          # 主轉換流程
│   ├── text_extractor.py     # 多格式文字擷取
│   ├── chunker.py            # 智慧分塊
│   ├── qwen_client.py        # Gradio API 封裝
│   ├── audio_processor.py    # 音訊合併與匯出
│   ├── progress.py           # 進度持久化
│   └── settings.py           # 設定載入
├── tests/
│   ├── test_chunker.py
│   ├── test_text_extractor.py
│   ├── test_settings.py
│   └── test_progress.py
├── book_to_convert/
├── audiobooks/
└── docs/ (plan/spec/todos/test/final)
```

## 里程碑時程

| 里程碑 | 完成條件 |
|--------|----------|
| M1 規格就緒 | plan/spec/todos/test 四份文件完成 |
| M2 核心可跑 | 模組化程式與原版 CLI 相容 |
| M3 優化完成 | resume、voice_design、多格式、測試通過 |
| M4 交付 | final.md、git push 成功 |

## 風險與緩解

| 風險 | 緩解 |
|------|------|
| 本機無 Qwen Gradio | 單元測試覆蓋非 API 邏輯；`--check-api` 獨立驗證 |
| FFmpeg 未安裝 | 啟動時偵測並提示 |
| Gradio API 版本差異 | `_resolve_api_name` 動態解析端點 |

## 參考來源

- 原版：`WhiskeyCoder/Qwen3-Audiobook-Converter` @ main
- 授權：MIT