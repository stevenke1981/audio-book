# Qwen3 Audiobook Converter

將 PDF、EPUB、DOCX、DOC、TXT 轉為有聲書，使用本機 [Qwen3 TTS](https://github.com/QwenLM/Qwen3-TTS) Gradio API。

本專案完整復刻 [WhiskeyCoder/Qwen3-Audiobook-Converter](https://github.com/WhiskeyCoder/Qwen3-Audiobook-Converter)，並加入模組化架構、進度續傳、Voice Design、多輸出格式等優化。

## 功能

- **Custom Voice**：Ryan、Serena、Aiden 等預設說話人
- **Voice Clone**：參考音檔自動轉錄並克隆
- **Voice Design**：以文字描述生成語音風格
- **多格式輸入**：TXT / PDF / EPUB / DOCX / DOC
- **智慧分塊**：句子邊界切分 + MD5 快取
- **進度續傳**：`--resume` 中斷後繼續
- **多輸出格式**：mp3 / wav / flac / ogg

## 快速開始

### 前置需求

1. Python 3.8+
2. [FFmpeg](https://ffmpeg.org/download.html)
3. Qwen3 TTS Gradio 運行於 `http://127.0.0.1:7860`

### 安裝

```bash
pip install -r requirements.txt
```

### 使用

```bash
# 預設模式（Ryan 說話人）
python audiobook_converter.py

# 指定說話人與語言
python audiobook_converter.py --speaker Serena --language English

# 語音克隆
python audiobook_converter.py --voice-clone --voice-sample ref.wav

# 語音設計
python audiobook_converter.py --voice-design

# 單檔轉換 + 續傳
python audiobook_converter.py --file book.pdf --resume

# 預覽（不呼叫 API）
python audiobook_converter.py --dry-run

# 檢查 API 連線
python audiobook_converter.py --check-api
```

將書籍放入 `book_to_convert/`，輸出在 `audiobooks/`。

## 專案結構

```
├── audiobook_converter.py   # CLI 入口
├── config.py                # 預設設定
├── src/                     # 核心模組
├── tests/                   # 單元測試
├── book_to_convert/         # 輸入
└── audiobooks/              # 輸出
```

## 測試

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## 文件

- [plan.md](plan.md) — 實作計畫
- [spec.md](spec.md) — 技術規格
- [todos.md](todos.md) — 任務清單
- [test.md](test.md) — 驗收標準
- [final.md](final.md) — 交付報告

## 授權

MIT License — 基於 WhiskeyCoder/Qwen3-Audiobook-Converter