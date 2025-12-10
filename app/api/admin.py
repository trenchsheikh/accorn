from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Agent
from app.services.voice import VoiceService
from app.services.rag import RAGService
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import json

router = APIRouter()

class IntentRequest(BaseModel):
    text: str
    agent_id: str

class Voice(BaseModel):
    id: str
    name: str

class IntentResponse(BaseModel):
    reply: str
    audio_base64: Optional[str] = None
    proposed_changes: Optional[Dict[str, Any]] = None
    voice_options: Optional[List[Voice]] = None

class SpeakRequest(BaseModel):
    text: str
    voice_id: str

VOICES = [
    { "id": "21m00Tcm4TlvDq8ikWAM", "name": "Bella (American, Soft)" },
    { "id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi (American, Strong)" },
    { "id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella (British, Professional)" },
    { "id": "ErXwobaYiN019PkySvjV", "name": "Antoni (American, Deep)" },
    { "id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli (American, Young)" },
    { "id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh (American, Deep)" },
    { "id": "VR6AewLTigWg4xSOukaG", "name": "Arnold (American, Crisp)" },
    { "id": "pNInz6obpgDQGcFmaJgB", "name": "Adam (American, Deep)" },
    { "id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam (American, Raspy)" },
]

@router.post("/speak")
async def speak(request: SpeakRequest):
    voice_service = VoiceService()
    audio = voice_service.generate_audio(request.text, voice_id=request.voice_id)
    return {"audio_base64": audio}

@router.post("/intent", response_model=IntentResponse)
async def handle_intent(request: IntentRequest, db: Session = Depends(get_db)):
    try:
        real_id = uuid.UUID(request.agent_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    agent = db.query(Agent).filter(Agent.id == real_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    # Initialize services
    rag = RAGService(db) # We'll use RAG service's Gemini connection
    voice_service = VoiceService()
    
    current_config = agent.config or {}
    
    # Construct prompt for the "Admin Agent"
    prompt = f"""You are an expert AI Agent Configurator. Your job is to help the user configure their AI receptionist.
    
    Current Configuration:
    - Voice ID: {current_config.get('voice_id', 'Default')}
    - Personality: {current_config.get('personality', 'Default')}
    
    Available Voices:
    {json.dumps(VOICES, indent=2)}
    
    User Request: "{request.text}"
    
    Analyze the user's request.
    1. Determine if they want to change the voice or personality.
    2. If they want to change the voice, pick the best matching ID from the list.
    3. If they want to see a list of voices, set "show_voice_options" to true and keep the reply very short (e.g. "Here are the available voices.").
    4. If they want to change personality, formulate a new system instruction.
    5. Construct a helpful, natural response to the user confirming what you found or asking for clarification.
    
    Output strictly valid JSON with this structure:
    {{
        "reply": "Text to speak back to the user",
        "proposed_changes": {{
            "voice_id": "...", // Optional, only if changed
            "personality": "..." // Optional, only if changed
        }},
        "show_voice_options": boolean // Set to true if user asks to see/hear voices
    }}
    
    If the request is unrelated to configuration, just reply helpfully and leave proposed_changes empty.
    """
    
    # Use Gemini to generate the response
    # We'll reuse the RAG service's model for convenience since it's already set up
    if not rag.model:
        return IntentResponse(
            reply="I'm sorry, I can't process that right now as my brain is offline.",
            proposed_changes=None
        )
        
    try:
        response = rag.model.generate_content(prompt)
        text_response = response.text
        # Clean up potential markdown code blocks
        if text_response.startswith("```json"):
            text_response = text_response[7:-3]
        elif text_response.startswith("```"):
            text_response = text_response[3:-3]
            
        data = json.loads(text_response.strip())
        
        reply_text = data.get("reply", "I didn't understand that.")
        proposed_changes = data.get("proposed_changes", {})
        show_voice_options = data.get("show_voice_options", False)
        
        voice_options = VOICES if show_voice_options else None
        
        # Generate audio for the reply
        # We use a specific "Admin" voice for this, e.g., "Adam" or just the default
        audio_base64 = voice_service.generate_audio(reply_text)
        
        return IntentResponse(
            reply=reply_text,
            audio_base64=audio_base64,
            proposed_changes=proposed_changes,
            voice_options=voice_options
        )
        
    except Exception as e:
        print(f"Error processing intent: {e}")
        return IntentResponse(
            reply="I encountered an error trying to understand your request.",
            proposed_changes=None
        )
