from common.services.transcription_services.adapter import TranscriptionAdapter
from common.services.transcription_services.azure import AzureSpeechAdapter

ADAPTER_REGISTRY: dict[str, type[TranscriptionAdapter]] = {
    "azure": AzureSpeechAdapter,
}
