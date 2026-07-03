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

- [ ] `pytest tests/ -v` 全部 PASS
- [ ] `python audiobook_converter.py --help` 正常
- [ ] `python audiobook_converter.py --dry-run` 正常（有 sample 檔時）
- [ ] 模組結構與 spec.md 一致
- [ ] git push 至 stevenke1981/audio-book 成功

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