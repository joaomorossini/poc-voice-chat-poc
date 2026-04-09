"""
Pipecat Voice Sidecar
=====================
Real-time voice server using Pipecat + WebRTC.
Runs alongside LibreChat as a sidecar service.

Transport: SmallWebRTC (P2P, no vendor dependency)
STT/TTS: Configurable — OpenAI Realtime (native) or modular pipeline
MCP: Connects to the same MCP servers as LibreChat agents

Replace the pipeline configuration with your preferred providers.
"""

import os
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

# --- Configuration ---
PROMPT_PATH = os.getenv("PROMPT_PATH", "app/prompts/voice.md")
MCP_SERVER_URL = os.getenv("FARM_DATA_MCP_URL", "")
TRANSPORT = os.getenv("VOICE_TRANSPORT", "smallwebrtc")
STT_TTS_MODE = os.getenv("STT_TTS_MODE", "openai-realtime")
VIDEO_ENABLED = os.getenv("VIDEO_ENABLED", "false").lower() == "true"
PORT = int(os.getenv("PORT", "7860"))

app = FastAPI(title="Pipecat Voice Sidecar")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_system_prompt() -> str:
    """Load voice system prompt from file."""
    path = Path(PROMPT_PATH)
    if path.exists():
        return path.read_text()
    logger.warning(f"Prompt file not found: {PROMPT_PATH}, using default")
    return "You are a helpful voice assistant. Keep responses concise and conversational."


# --- Pipeline factory ---
# This is where you configure the Pipecat pipeline.
# The actual implementation depends on your chosen transport and STT/TTS providers.

async def _create_pipeline():
    """
    Create and return a Pipecat pipeline.

    This is a skeleton — uncomment and configure based on your providers.
    See the Pipecat docs for full pipeline configuration:
    https://docs.pipecat.ai/
    """
    system_prompt = _load_system_prompt()

    # --- SmallWebRTC + OpenAI Realtime (lowest latency) ---
    if STT_TTS_MODE == "openai-realtime":
        # from pipecat.transports.services.small_webrtc import SmallWebRTCTransport
        # from pipecat.services.openai_realtime import OpenAIRealtimeService
        # from pipecat.vad.silero import SileroVAD
        #
        # transport = SmallWebRTCTransport(
        #     video_in_enabled=VIDEO_ENABLED,
        #     start_video_paused=not VIDEO_ENABLED,
        # )
        # llm = OpenAIRealtimeService(
        #     api_key=os.getenv("OPENAI_API_KEY"),
        #     system_instruction=system_prompt,
        #     voice="alloy",
        # )
        # vad = SileroVAD()
        #
        # # MCP client for tool access
        # if MCP_SERVER_URL:
        #     from pipecat.services.mcp import MCPClient
        #     mcp_client = MCPClient(url=MCP_SERVER_URL)
        #     llm.register_tools(await mcp_client.get_tools())
        #
        # return Pipeline([transport.input(), vad, llm, transport.output()])
        pass

    # --- Modular pipeline (mix providers) ---
    elif STT_TTS_MODE == "modular":
        # from pipecat.services.deepgram import DeepgramSTT
        # from pipecat.services.elevenlabs import ElevenLabsTTS
        # from pipecat.services.anthropic import AnthropicLLM
        #
        # stt = DeepgramSTT(api_key=os.getenv("DEEPGRAM_API_KEY"))
        # llm = AnthropicLLM(
        #     api_key=os.getenv("ANTHROPIC_API_KEY"),
        #     model="claude-sonnet-4-6",
        #     system_prompt=system_prompt,
        # )
        # tts = ElevenLabsTTS(
        #     api_key=os.getenv("ELEVENLABS_API_KEY"),
        #     voice_id="your-voice-id",
        # )
        #
        # return Pipeline([transport.input(), stt, llm, tts, transport.output()])
        pass

    logger.info(f"Pipeline created: transport={TRANSPORT}, stt_tts={STT_TTS_MODE}")
    return None


# --- HTTP endpoints ---

@app.get("/health")
async def health():
    return {"status": "ok", "transport": TRANSPORT, "stt_tts": STT_TTS_MODE}


@app.post("/connect")
async def connect(request: Request):
    """
    WebRTC connection endpoint.
    The frontend posts an SDP offer; this returns an SDP answer.
    """
    # pipeline = await _create_pipeline()
    # In a real implementation:
    # body = await request.json()
    # answer = await pipeline.handle_offer(body["sdp"])
    # return {"sdp": answer}
    return {"status": "voice_not_configured", "message": "Uncomment pipeline code in server.py"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
