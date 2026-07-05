# 驗收測試規格

## 1. 單元測試（pytest，無需 Qwen API）

### 1.1 分塊器 `test_chunker.py`

| 案例 ID | 輸入 | 預期 |
|---------|------|------|
| CHK-01 | 空字串 | 回傳 `[]` |
| CHK-02 | 短文本 < chunk_size | 單一 chunk |
| CHK-03 | 多句文本 | 在句號邊界切分 |
| CHK-04 | 超長單句 | 在逗號/分號處二次切分 |
| CHK-05 | chunk_size=10 | 每塊 ≤10 字 |

### 1.2 文字擷取 `test_text_extractor.py`

| 案例 ID | 輸入 | 預期 |
|---------|------|------|
| EXT-01 | UTF-8 txt 檔 | 正確讀取內容 |
| EXT-02 | HTML 片段 | 標籤移除、文字保留 |
| EXT-03 | `_clean_text` 頁碼 | 獨立數字被移除 |
| EXT-04 | 空白正規化 | 多餘空白合併 |

### 1.3 設定 `test_settings.py`

| 案例 ID | 操作 | 預期 |
|---------|------|------|
| SET-01 | 預設載入 | speaker=Ryan, format=mp3 |
| SET-02 | 環境變數 QWEN_API_URL | 覆寫 api url |
| SET-03 | CLI 覆寫 --speaker | speaker 更新 |
| SET-04 | settings_hash | 相同設定產生相同 hash |

### 1.4 進度 `test_progress.py`

| 案例 ID | 操作 | 預期 |
|---------|------|------|
| PRG-01 | 新建進度 | total_chunks 正確 |
| PRG-02 | mark_complete | completed_chunks 含該編號 |
| PRG-03 | 載入已存 JSON | 狀態還原 |
| PRG-04 | settings_hash 不符 | is_resumable=False |

### 1.5 改善優化新增測試（cbm 審查後）

#### 1.5.1 音訊合併 `test_audio_processor.py`（新增，P0）

| 案例 ID | 操作 | 預期 |
|---------|------|------|
| AUD-01 | combine_chunks 全部成功 | 輸出檔產生，回傳 True |
| AUD-02 | combine_chunks 部分缺塊 | 缺塊插入靜音佔位 **或** 依門檻中止並回報明確 |
| AUD-03 | combine_chunks 全失敗 | 回傳 False，不產生輸出 |
| AUD-04 | restore_chunk_from_cache | 由 cache 複製至 chunks/ |
| AUD-05 | cleanup_temp_chunks | 僅刪 chunk_*.wav，保留 cache |

#### 1.5.2 Qwen 客戶端 `test_qwen_client.py`（新增，P0，mock）

| 案例 ID | 操作 | 預期 |
|---------|------|------|
| QC-01 | _resolve_api_name 命中 | 回傳匹配端點 |
| QC-02 | _resolve_api_name 無匹配 | 丟出 ValueError（改善後） |
| QC-03 | voice_clone 端點解析 | 支援 /generate_voice_clone 與 /run_voice_clone fallback |
| QC-04 | generate 三模式 | 依 voice_mode 呼叫對應端點 |

#### 1.5.3 轉換流程 `test_converter.py`（新增，P0，mock）

| 案例 ID | 操作 | 預期 |
|---------|------|------|
| CNV-01 | dry-run | 不呼叫 API，印出 chunk 預覽 |
| CNV-02 | process_chunk_with_retry 首試成功 | 回傳 True，不重試 |
| CNV-03 | retry 全失敗 | 回傳 False，記錄失敗 |
| CNV-04 | get_cache_path 一致性 | 相同輸入產生相同路徑；換 model/seed 後路徑改變（改善後） |

#### 1.5.4 settings_hash 完整性 `test_settings.py`（強化，P0）

| 案例 ID | 操作 | 預期 |
|---------|------|------|
| SET-05 | 變更 custom_voice_model_size | hash 改變（改善後） |
| SET-06 | 變更 seed | hash 改變（改善後） |
| SET-07 | 變更 audio_bitrate | hash 改變（改善後） |

#### 1.5.5 頁碼清理誤刪 `test_text_extractor.py`（強化，P1）

| 案例 ID | 輸入 | 預期 |
|---------|------|------|
| EXT-05 | 「Chapter 42」 | 章節號保留（改善後） |
| EXT-06 | 「in 2025」 | 年份保留（改善後） |
| EXT-07 | 小型 PDF fixture | 正確擷取文字 |
| EXT-08 | 小型 EPUB fixture | 正確擷取文字 |

#### 1.5.6 CLI `test_cli.py`（新增，P1）

| 案例 ID | 操作 | 預期 |
|---------|------|------|
| CLI-01 | --voice-clone 無 --voice-sample | exit 1，錯誤訊息 |
| CLI-02 | --format 非法值 | argparse 拒絕 |
| CLI-03 | --help | exit 0，列出所有參數 |

## 2. 整合測試（可選，需本機環境）

### 2.1 API 健康檢查

```bash
python audiobook_converter.py --check-api
```

| 條件 | 預期 |
|------|------|
| Gradio 運行中 | exit 0，顯示可用端點 |
| Gradio 未運行 | exit 1，錯誤訊息含 API URL |

### 2.2 Dry-run

```bash
python audiobook_converter.py --dry-run --file book_to_convert/sample.txt
```

| 預期 |
|------|
| 顯示擷取字數、chunk 數量、前 2 個 chunk 預覽 |
| 不呼叫 Qwen API |
| exit 0 |

### 2.3 原版相容 CLI

```bash
python audiobook_converter.py --help
python audiobook_converter.py --voice-clone --voice-sample missing.wav
```

| 預期 |
|------|
| help 顯示所有參數 |
| missing.wav → exit 1 含錯誤訊息 |

## 3. 手動驗收（需 Qwen + FFmpeg）

| 案例 ID | 步驟 | 預期 |
|---------|------|------|
| MAN-01 | 放入 sample.txt，執行轉換 | audiobooks/sample.mp3 產生 |
| MAN-02 | 中斷後 --resume | 從斷點繼續，不重做已完成 chunk |
| MAN-03 | --voice-clone --voice-sample ref.wav | 克隆模式正常 |
| MAN-04 | --format flac | 輸出 .flac |

## 4. 驗收通過條件

### 4.1 目前基線（已達成）

- [x] `pytest tests/ -v` 全部 PASS（19/19）
- [x] `python audiobook_converter.py --help` 正常
- [x] `python audiobook_converter.py --dry-run` 正常（有 sample 檔時）
- [x] 模組結構與 spec.md 一致（spec §3 已對齊 cbm IMPORTS）
- [x] git push 至 stevenke1981/audio-book 成功

### 4.2 改善優化輪目標（Phase 7）

- [ ] 部分失敗行為測試通過（AUD-02）
- [ ] settings_hash 涵蓋所有語音參數（SET-05~07）
- [ ] qwen_client / audio_processor / converter / CLI 具備 mock 測試
- [ ] voice_clone 端點動態解析（QC-03）
- [ ] 頁碼清理誤刪測試通過（EXT-05/06）
- [ ] PDF / EPUB 擷取測試通過（EXT-07/08）

## 5. 執行指令

```bash
# 安裝依賴
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 執行測試
pytest tests/ -v

# Dry-run
python audiobook_converter.py --dry-run

# API 檢查（需 Gradio）
python audiobook_converter.py --check-api
```