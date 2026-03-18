import os
import re
import yaml
from pathlib import Path

config_path = Path(__file__).parent / "config.yaml"

with open(config_path) as f:
    _config = yaml.safe_load(f)

VOICE_MAP = _config["voices"]
DEFAULT_VOICES=_config["default_voices"]
BACKGROUND_VOLUME_OFFSET = _config["background_volume_offset"]
TRANSCRIPT_FILE = _config["transcript_file"]

ELEVEN_LABS_MODEL_ID = _config["eleven_labs"]["model_id"]
ELEVEN_LABS_API_KEY = os.getenv(_config["eleven_labs"]["api_key_env"])
