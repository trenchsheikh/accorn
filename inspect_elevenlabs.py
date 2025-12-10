from elevenlabs.client import ElevenLabs
import os

try:
    client = ElevenLabs(api_key="test")
    print("Client attributes:", dir(client))
except Exception as e:
    print(e)
