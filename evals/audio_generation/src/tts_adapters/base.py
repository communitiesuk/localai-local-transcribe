from abc import ABC, abstractmethod
from pathlib import Path

class TTSAdapter(ABC):
    
    @abstractmethod
    def generate_audio(self, transcript_file : str | Path)-> bytes:
        """Returns audio bytes from a tts provider"""
    pass