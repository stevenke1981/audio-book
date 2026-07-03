#!/usr/bin/env python3
"""
Qwen3 Audiobook Converter
Converts PDFs, EPUBs, DOCX, DOC, TXT files into audiobooks using Qwen Voice API.

Based on WhiskeyCoder/Qwen3-Audiobook-Converter with modular architecture and enhancements.
License: MIT
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

from src.converter import QwenAudiobookConverter
from src.settings import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert books to audiobooks using Qwen3 TTS Voice Model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python audiobook_converter.py
  python audiobook_converter.py --speaker Serena --language English
  python audiobook_converter.py --voice-clone --voice-sample ref.wav
  python audiobook_converter.py --voice-design
  python audiobook_converter.py --file book.pdf --resume
  python audiobook_converter.py --dry-run
  python audiobook_converter.py --check-api
  python audiobook_converter.py --config config.example.yaml
        """,
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--voice-clone", action="store_true", help="Voice cloning mode")
    mode.add_argument("--voice-design", action="store_true", help="Voice design mode")

    parser.add_argument("--voice-sample", type=str, help="Reference audio for voice clone (WAV)")
    parser.add_argument("--speaker", type=str, help="Custom voice speaker (default: Ryan)")
    parser.add_argument("--language", type=str, help="Voice language")
    parser.add_argument("--instruct", type=str, help="Style instruction for custom voice")
    parser.add_argument("--description", type=str, help="Voice design description")
    parser.add_argument("--api-url", type=str, help="Qwen Gradio API URL")
    parser.add_argument("--input-dir", type=str, help="Input books folder")
    parser.add_argument("--output-dir", type=str, help="Output audiobooks folder")
    parser.add_argument("--format", type=str, choices=["mp3", "wav", "flac", "ogg"], help="Output format")
    parser.add_argument("--bitrate", type=str, help="MP3 bitrate (e.g. 128k)")
    parser.add_argument("--chunk-size", type=int, help="Words per chunk")
    parser.add_argument("--config", type=str, help="YAML config file path")
    parser.add_argument("--file", type=str, help="Convert a single file")
    parser.add_argument("--resume", action="store_true", help="Resume interrupted conversion")
    parser.add_argument("--force-restart", action="store_true", help="Ignore saved progress")
    parser.add_argument("--check-api", action="store_true", help="Check Qwen API connectivity")
    parser.add_argument("--dry-run", action="store_true", help="Extract and chunk only, no TTS")
    parser.add_argument("--no-cache", action="store_true", help="Disable audio chunk cache")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.voice_clone:
        voice_mode = "voice_clone"
    elif args.voice_design:
        voice_mode = "voice_design"
    else:
        voice_mode = None

    if args.voice_clone and not args.voice_sample:
        print("[ERROR] --voice-clone requires --voice-sample")
        return 1

    cli_overrides = {
        "voice_mode": voice_mode,
        "voice_clone_ref_audio": args.voice_sample or None,
        "custom_voice_speaker": args.speaker,
        "custom_voice_language": args.language,
        "custom_voice_instruct": args.instruct,
        "voice_design_description": args.description,
        "qwen_api_url": args.api_url,
        "books_folder": args.input_dir,
        "audiobooks_folder": args.output_dir,
        "audio_format": args.format,
        "audio_bitrate": args.bitrate,
        "chunk_size_words": args.chunk_size,
        "resume": args.resume or None,
        "force_restart": args.force_restart or None,
        "dry_run": args.dry_run or None,
        "no_cache": args.no_cache or None,
    }

    settings = load_settings(config_path=args.config, cli_overrides=cli_overrides)

    try:
        converter = QwenAudiobookConverter(settings)

        if args.check_api:
            info = converter.check_api()
            print(f"[OK] Connected to {info['url']}")
            print(f"[OK] Endpoints available: {info['endpoint_count']}")
            for ep in info["endpoints"][:10]:
                print(f"  - {ep}")
            if info["endpoint_count"] > 10:
                print(f"  ... and {info['endpoint_count'] - 10} more")
            return 0

        converter.validate()

        if not settings.dry_run:
            converter.init_qwen()

        single = Path(args.file) if args.file else None
        results = converter.run(single_file=single)
        if results and not all(results.values()):
            return 1
        return 0

    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"[ERROR] {exc}")
        return 1
    except KeyboardInterrupt:
        print("\n[WARNING] Shutdown requested by user")
        return 130
    except Exception as exc:
        print(f"[FATAL] {exc}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())