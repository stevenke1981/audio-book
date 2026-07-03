# =============================================================================
# QWEN API CONFIGURATION
# =============================================================================

QWEN_API_URL = "http://127.0.0.1:7860"
API_TIMEOUT = 300
MAX_RETRIES = 3

# =============================================================================
# VOICE GENERATION MODE
# =============================================================================

VOICE_MODE = "custom_voice"

# =============================================================================
# CUSTOM VOICE SETTINGS
# =============================================================================

CUSTOM_VOICE_SPEAKER = "Ryan"
CUSTOM_VOICE_LANGUAGE = "English"
CUSTOM_VOICE_INSTRUCT = (
    "Speak naturally and clearly, as if reading a dramatic book to an adult audience."
)
CUSTOM_VOICE_MODEL_SIZE = "1.7B"
CUSTOM_VOICE_SEED = -1
CUSTOM_VOICE_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"

# =============================================================================
# VOICE CLONE SETTINGS
# =============================================================================

VOICE_CLONE_REF_AUDIO = ""
VOICE_CLONE_REF_TEXT = ""
VOICE_CLONE_LANGUAGE = "English"
VOICE_CLONE_USE_XVECTOR_ONLY = False
VOICE_CLONE_MODEL_SIZE = "1.7B"
VOICE_CLONE_MAX_CHUNK_CHARS = 200
VOICE_CLONE_CHUNK_GAP = 0
VOICE_CLONE_SEED = -1

# =============================================================================
# VOICE DESIGN SETTINGS
# =============================================================================

VOICE_DESIGN_LANGUAGE = "English"
VOICE_DESIGN_DESCRIPTION = (
    "Speak in a clear, professional narrator voice suitable for reading audiobooks."
)
VOICE_DESIGN_SEED = -1

# =============================================================================
# PROCESSING SETTINGS
# =============================================================================

BOOKS_FOLDER = "book_to_convert"
AUDIOBOOKS_FOLDER = "audiobooks"
CHUNK_SIZE_WORDS = 1500
MAX_WORKERS = 1
MIN_DELAY_BETWEEN_CHUNKS = 1

# =============================================================================
# AUDIO OUTPUT SETTINGS
# =============================================================================

AUDIO_FORMAT = "mp3"
AUDIO_BITRATE = "128k"

# =============================================================================
# ADVANCED SETTINGS
# =============================================================================

SUPPORTED_FORMATS = [".txt", ".pdf", ".epub", ".docx", ".doc"]

CLEAN_PAGE_NUMBERS = True
NORMALIZE_WHITESPACE = True
SENTENCE_BOUNDARY_DETECTION = True

ENABLE_CACHING = True
CACHE_CLEANUP_DAYS = 30

LOG_LEVEL = "INFO"
LOG_TO_FILE = True
LOG_TO_CONSOLE = True