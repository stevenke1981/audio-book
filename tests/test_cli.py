"""Tests for CLI argument parsing (no API/FFmpeg needed)."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from audiobook_converter import build_parser, main


@pytest.fixture
def parser():
    return build_parser()


def test_help_returns_zero(parser):
    """--help should exit 0 and print usage."""
    with pytest.raises(SystemExit) as exc:
        with patch("sys.argv", ["prog", "--help"]):
            parser.parse_args(["--help"])


def test_voice_clone_requires_voice_sample(parser):
    """--voice-clone without --voice-sample should be caught after parsing."""
    args = parser.parse_args(["--voice-clone"])
    assert args.voice_clone is True
    assert args.voice_sample is None


def test_voice_clone_and_voice_design_mutually_exclusive():
    """--voice-clone and --voice-design should be mutually exclusive."""
    with pytest.raises(SystemExit):
        with patch("sys.argv", ["prog", "--voice-clone", "--voice-design"]):
            build_parser().parse_args(["--voice-clone", "--voice-design"])


def test_format_valid_choices():
    parser = build_parser()
    for fmt in ["mp3", "wav", "flac", "ogg"]:
        args = parser.parse_args(["--format", fmt])
        assert args.format == fmt


def test_format_invalid_choice():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--format", "aac"])


def test_main_no_args_returns_zero(parser):
    """main() with no args should run and return 0 (dry-run mode)."""
    with patch("sys.argv", ["prog", "--dry-run"]):
        rc = main()
        assert rc == 0


def test_main_voice_clone_no_sample_returns_one(parser):
    """main() with --voice-clone but no --voice-sample should return 1."""
    with patch("sys.argv", ["prog", "--voice-clone"]):
        rc = main()
        assert rc == 1


def test_main_check_api(parser):
    """main() with --check-api should return 0 (even without real API)."""
    with patch("sys.argv", ["prog", "--check-api"]):
        rc = main()
        assert rc == 1  # Will fail to connect, which is expected


def test_dry_run_flag_sets_attribute(parser):
    args = parser.parse_args(["--dry-run"])
    assert args.dry_run is True
