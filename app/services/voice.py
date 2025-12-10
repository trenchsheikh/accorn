from elevenlabs.client import ElevenLabs
from app.core.config import settings
import base64

class VoiceService:
    def __init__(self):
        if settings.ELEVENLABS_API_KEY:
            self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False

    def generate_audio(self, text: str, voice_id: str = None) -> str:
        """
        Generate audio from text using ElevenLabs.
        Returns base64 encoded audio.
        """
        if not self.enabled or not self.client:
            return ""
            
        try:
            # The generate method returns a generator in v1+, we need to consume it
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id or "21m00Tcm4TlvDq8ikWAM", # Default to Bella
                model_id="eleven_multilingual_v2"
            )
            
            # Combine all chunks into bytes
            audio_bytes = b"".join(audio_generator)
            
            return base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error generating audio: {e}")
            return ""
