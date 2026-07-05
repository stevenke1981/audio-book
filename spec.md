# Qwen3 Audiobook Converter — 技術規格

## 1. 系統概述

將 PDF、EPUB、DOCX、DOC、TXT 轉為有聲書，透過本機 Qwen3 TTS Gradio API（預設 `http://127.0.0.1:7860`）合成語音。

## 2. 功能需求

### 2.1 文字擷取（FR-EXTRACT）

| ID | 格式 | 實作 | 備註 |
|----|------|------|------|
| FR-EXTRACT-01 | `.txt` | 多編碼嘗試 utf-8/utf-16/latin-1/cp1252 | 與原版一致 |
| FR-EXTRACT-02 | `.pdf` | PyPDF2 逐頁擷取 | 記錄頁數進度 |
| FR-EXTRACT-03 | `.epub` | ebooklib → zipfile → manual 三層 fallback | |
| FR-EXTRACT-04 | `.docx` | python-docx | 可選依賴 |
| FR-EXTRACT-05 | `.doc` | docx2txt | 可選依賴 |
| FR-EXTRACT-06 | HTML 清理 | BeautifulSoup 或 regex fallback | |

文字清理規則：
- 正規化空白
- 可選移除獨立頁碼（1–3 位數字）
- 句子邊界保留

> **改善建議（P1）**：`text_extractor.py:72` 的 `\b\d{1,3}\b` 會誤刪章節號（「Chapter 42」）、年份（「2025」）與數據。建議收斂正則（僅比對行首/行尾孤立數字）或將 `clean_page_numbers` 預設改為 `False`，並補測試涵蓋誤刪案例。

### 2.2 分塊（FR-CHUNK）

| 參數 | 預設 | 說明 |
|------|------|------|
| `CHUNK_SIZE_WORDS` | 1500 | 每塊最大字數 |
| 邊界 | 句號/驚嘆/問號 | 優先在句子邊界切分 |
| 長句 | 逗號/分號/冒號 | 超長句二次切分 |

### 2.3 語音合成（FR-TTS）

#### 模式 A：Custom Voice（預設）

```
API: /run_custom_voice 或 /generate_custom_voice
參數: text, language, speaker, instruct, model_id_cv|model_size, seed
預設 speaker: Ryan
預設 model: 1.7B
```

#### 模式 B：Voice Clone

```
API: /generate_voice_clone
參數: ref_audio, ref_text, target_text, language, use_xvector_only, model_size, ...
前置: /transcribe_audio 自動轉錄參考音檔
```

#### 模式 C：Voice Design（優化新增）

```
API: /generate_voice_design 或 /run_voice_design
參數: text, language, description, seed
僅 1.7B 模型
```

### 2.4 音訊處理（FR-AUDIO）

| 項目 | 規格 |
|------|------|
| 中間格式 | WAV（chunks/） |
| 輸出格式 | mp3（預設）、wav、flac、ogg |
| 位元率 | 128k（mp3 預設），可調 |
| 合併 | pydub AudioSegment 順序拼接 |
| FFmpeg | 系統依賴，啟動時檢查 |

> **改善建議（P0）— 部分失敗行為**：目前 `converter.py:275` 即使部分 chunk 失敗仍會合併並回傳成功，`audio_processor.combine_chunks` 只要有一塊成功即回傳 True，缺塊只記錄警告。這會靜默產出不完整有聲書。應改為：缺塊處插入短靜音佔位，或當成功率低於門檻（如 95%）時中止並回報明確錯誤。

### 2.5 快取（FR-CACHE）

- 路徑：`cache/audio_chunks/{md5}.wav`
- 雜湊輸入（`converter.get_cache_path`）：`text + voice_mode + voice_key + extra`
  - custom_voice：`voice_key=speaker`、`extra=instruct`
  - voice_clone：`voice_key=ref_audio 檔名`、`extra=""`
  - voice_design：`voice_key="design"`、`extra=description`
- **優化**：轉換結束僅清理 `chunks/chunk_*.wav`，**保留** cache

> **改善建議（P0）**：目前快取鍵未納入 `model_size`、`seed`、`language`，換模型或 seed 後可能誤用舊快取。應與 `settings_hash` 一併補齊語音參數。

### 2.6 進度續傳（FR-RESUME，優化）

狀態檔：`cache/progress/{book_stem}.json`

```json
{
  "book": "my_book.pdf",
  "total_chunks": 42,
  "completed_chunks": [1, 2, 3],
  "failed_chunks": [],
  "voice_mode": "custom_voice",
  "settings_hash": "abc123",
  "updated_at": "2026-07-04T12:00:00"
}
```

- `--resume`：跳過已完成 chunk，從斷點繼續
- 設定變更（speaker/mode）時 hash 不符則警告並可 `--force-restart`

`settings_hash`（`settings.py:78`）目前納入欄位：`voice_mode`、`custom_voice_speaker`、`custom_voice_language`、`custom_voice_instruct`、`voice_clone_ref_audio`、`voice_design_description`、`audio_format`、`chunk_size_words`。

> **改善建議（P0）**：hash 應補入所有影響輸出的語音參數，避免 `--resume` 誤判：
> - custom：`custom_voice_model_size`、`custom_voice_model_id`、`custom_voice_seed`
> - clone：`voice_clone_language`、`voice_clone_model_size`、`voice_clone_use_xvector_only`、`voice_clone_seed`
> - design：`voice_design_language`、`voice_design_seed`
> - 音訊：`audio_bitrate`

### 2.7 CLI 介面（FR-CLI）

```bash
python audiobook_converter.py [OPTIONS]

# 原版相容
python audiobook_converter.py
python audiobook_converter.py --voice-clone --voice-sample ref.wav

# 優化新增
python audiobook_converter.py --speaker Serena --language English
python audiobook_converter.py --format flac --bitrate 192k
python audiobook_converter.py --config config.yaml
python audiobook_converter.py --file book.pdf
python audiobook_converter.py --resume
python audiobook_converter.py --check-api
python audiobook_converter.py --voice-design
python audiobook_converter.py --dry-run
```

| 參數 | 型別 | 預設 | 說明 |
|------|------|------|------|
| `--voice-clone` | flag | false | 語音克隆模式 |
| `--voice-design` | flag | false | 語音設計模式 |
| `--voice-sample` | path | - | 克隆參考音檔 |
| `--speaker` | str | Ryan | Custom voice 說話人 |
| `--language` | str | English | 語言 |
| `--instruct` | str | (config) | 風格指示 |
| `--api-url` | str | 127.0.0.1:7860 | API 端點 |
| `--input-dir` | path | book_to_convert | 輸入目錄 |
| `--output-dir` | path | audiobooks | 輸出目錄 |
| `--format` | str | mp3 | 輸出格式 |
| `--bitrate` | str | 128k | 音訊位元率 |
| `--chunk-size` | int | 1500 | 分塊字數 |
| `--config` | path | - | YAML 設定檔 |
| `--file` | path | - | 單檔轉換 |
| `--resume` | flag | false | 續傳 |
| `--force-restart` | flag | false | 忽略進度重新開始 |
| `--check-api` | flag | false | 僅檢查 API |
| `--dry-run` | flag | false | 僅擷取文字與分塊預覽 |
| `--no-cache` | flag | false | 停用快取 |

### 2.8 環境變數

| 變數 | 對應設定 |
|------|----------|
| `QWEN_API_URL` | API 端點 |
| `AUDIOBOOK_INPUT_DIR` | 輸入目錄 |
| `AUDIOBOOK_OUTPUT_DIR` | 輸出目錄 |

## 3. 模組設計

```
audiobook_converter.py           # CLI：import load_settings、QwenAudiobookConverter
    ├── src/settings.py          # load_settings / Settings（被以下所有模組 import）
    └── src/converter.py         # QwenAudiobookConverter，import settings + 下列全部
            ├── text_extractor.py    # import settings 無關；被 converter 使用
            ├── chunker.py           # 純函式 split_into_chunks
            ├── qwen_client.py       # import settings
            ├── audio_processor.py   # import settings
            └── progress.py          # 獨立，無 settings 相依
```

> 依賴關係（以 cbm IMPORTS 邊為準）：`audiobook_converter.py` → `converter`、`settings`；`converter` → `settings`、`text_extractor`、`chunker`、`qwen_client`、`audio_processor`、`progress`；`qwen_client`／`audio_processor` → `settings`。

### 3.1 `Settings`

```python
@dataclass
class Settings:
    qwen_api_url: str
    voice_mode: str  # custom_voice | voice_clone | voice_design
    custom_voice_speaker: str
    custom_voice_language: str
    custom_voice_instruct: str
    # ... 其餘欄位
    def settings_hash(self) -> str: ...
```

### 3.2 `QwenClient`

- `connect()` / `check_health()`
- `transcribe(audio_path) -> str`
- `generate_custom_voice(text) -> path`
- `generate_voice_clone(text) -> path`
- `generate_voice_design(text) -> path`
- `_resolve_api_name(*candidates)`

> **改善建議（P1）**：
> - `_generate_voice_clone`（`qwen_client.py:107`）目前硬編碼 `/generate_voice_clone`，與 custom/design 的動態解析不一致，應改用 `_resolve_api_name("/generate_voice_clone", "/run_voice_clone")`。
> - `_resolve_api_name`（`qwen_client.py:130`）在無匹配端點時靜默回傳第一個候選，導致難以除錯的 Gradio 錯誤。應改為丟出明確 `ValueError`，或於呼叫前以 `check_health` 驗證端點存在。

### 3.3 `ProgressTracker`

- `load(book_stem) -> ProgressState | None`
- `mark_complete(chunk_num)`
- `is_complete(chunk_num) -> bool`
- `save()`

## 4. 非功能需求

| ID | 需求 |
|----|------|
| NFR-01 | Python 3.8+ |
| NFR-02 | Windows UTF-8 主控台修正 |
| NFR-03 | 日誌：`logs/audiobook_YYYYMMDD.log` |
| NFR-04 | 失敗時仍清理暫存 chunks |
| NFR-05 | MAX_RETRIES=3，指數退避 |
| NFR-06 | MAX_WORKERS=1（避免 rate limit） |
| NFR-07（新增） | 部分 chunk 失敗須明確標示（靜音佔位或門檻中止），不得靜默產出不完整輸出 |
| NFR-08（新增） | 核心模組（qwen_client / audio_processor / converter / CLI）須具備 mock 單元測試 |
| NFR-09（新增） | 規劃自 PyPDF2 遷移至 `pypdf`（PyPDF2 已 deprecated） |

## 5. 相容性

- 原版 CLI 無參數呼叫行為不變
- 目錄名稱 `book_to_convert`、`audiobooks` 保持預設
- MIT 授權保留

## 6. 驗收標準

見 `test.md`。