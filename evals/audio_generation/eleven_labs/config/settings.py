import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

config_path = Path(__file__).parent / "config.yaml"
ROOT = Path(__file__).resolve().parents[4]
dotenv_path = ROOT / ".env"
load_dotenv(dotenv_path)

with Path(config_path).open(encoding="utf-8") as f:
    _config = yaml.safe_load(f)

VOICE_MAP = _config["voices"]
DEFAULT_VOICES = _config["default_voices"]
BACKGROUND_VOLUME_OFFSET = _config["background_volume_offset"]
TRANSCRIPT_FILE = _config["transcript_file"]

ELEVEN_LABS_MODEL_ID = _config["eleven_labs"]["model_id"]
ELEVEN_LABS_API_KEY = os.getenv(_config["eleven_labs"]["api_key_env"])
