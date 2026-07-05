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
├── plan.md / spec.md / todos.md / test.md / final.md  # 文件位於倉庫根目錄
├── README.md
└── config.example.yaml
```

> 註：文件（plan/spec/todos/test/final）與 `config.py`、`config.example.yaml` 皆位於**倉庫根目錄**，並非 `docs/` 子目錄。

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

## Phase 5：改善優化（cbm 分析後新增）

以 `cbm+audio-book` 索引（24 檔、147 符號、328 邊）與原始碼審查為依據，規劃下一輪可靠性與品質強化。

### 5.1 可靠性修正（P0）

| 項目 | 問題證據 | 目標 |
|------|----------|------|
| 部分失敗處理 | `converter.py:275` 即使 `successful < total_chunks` 仍合併並回傳成功；`audio_processor.py:62-79` 只要有一塊成功即回傳 True，缺塊僅記 log | 缺塊時插入靜音佔位或依門檻中止，並在報告明確標示缺塊 |
| settings_hash 不完整 | `settings.py:78-90` 僅納入 8 欄位，缺 `custom_voice_model_size/model_id/seed`、`voice_clone_*`、`voice_design_language/seed`、`audio_bitrate` | 納入所有影響輸出的語音參數，避免換模型/seed 後 `--resume` 誤用舊快取 |
| 核心模組零測試 | `qwen_client.py`、`audio_processor.py`、`converter.py`、`audiobook_converter.py` 皆無單元測試 | 以 mock 補齊 API 封裝、音訊合併、轉換流程與 CLI 測試 |

### 5.2 相容性與正確性（P1）

| 項目 | 問題證據 | 目標 |
|------|----------|------|
| Voice Clone 端點硬編碼 | `qwen_client.py:107` 寫死 `/generate_voice_clone`，與其他模式動態解析不一致 | 改用 `_resolve_api_name("/generate_voice_clone", "/run_voice_clone")` |
| 端點解析靜默 fallback | `qwen_client.py:130-135` 無匹配時回傳第一個候選，導致難懂的 Gradio 錯誤 | 無匹配時丟出明確 `ValueError` |
| 頁碼清理誤刪 | `text_extractor.py:72` `\b\d{1,3}\b` 會誤刪章節號、年份、數據 | 收斂正則或預設關閉，並補測試涵蓋誤刪案例 |
| PDF/EPUB/DOCX 無測試 | `test_text_extractor.py` 僅涵蓋 TXT/HTML | 補小型 fixture 測試 |

### 5.3 文件與設定一致性（P2）

| 項目 | 目標 |
|------|------|
| spec 模組圖 | 修正 `spec.md §3` 依賴關係與實際 import 一致 |
| final 完成宣稱 | `final.md` 標示 4 項本機驗證項目為「未於本次交付驗證」 |
| config 範例 | `config.example.yaml` 擴充涵蓋所有語音模式與設定群組 |
| PyPDF2 遷移 | 規劃遷移至 `pypdf`（PyPDF2 已 deprecated） |

### 5.4 里程碑（改善輪）

| 里程碑 | 完成條件 |
|--------|----------|
| M5 可靠性 | 部分失敗處理、settings_hash 補全、核心模組測試通過 |
| M6 相容性 | 端點解析統一、頁碼清理修正、格式測試補齊 |
| M7 文件對齊 | spec/final/config 與程式碼一致，PyPDF2 遷移計畫確立 |

## 參考來源

- 原版：`WhiskeyCoder/Qwen3-Audiobook-Converter` @ main
- 授權：MIT
- 分析工具：`cbm+audio-book` 索引（get_architecture / query_graph）