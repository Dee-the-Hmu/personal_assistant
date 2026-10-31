import os 
import websockets
import json

from dotenv import load_dotenv
#python-dotenv → loads environment variables from a .env file

from .base import TTSProvider

# read variables from the local .env file and adds them 
load_dotenv()

class DeepgramTTS(TTSProvider):

    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        self.websocket = None

    async def connect(self):
        """
        Establish the realtime connection to the TTS provider.
        """

        url = (
            "wss://api.deepgram.com/v2/speak"
            "?model=flux-alexis-en"
            "&encoding=linear16"
            "&sample_rate=24000"
        )

        self.websocket = await websockets.connect(
            url,
            additional_headers={
                "Authorization": f"Token {self.api_key}"
            }
        )

   
    async def send_text(self, text: str):
        # Deepgram Flux TTS expects text inside a JSON "Speak" message.
        #
        # Python dictionary:
        # {
        #     "type": "Speak",
        #     "text": "Hello..."
        # }
        #
        # json.dumps() converts the Python dictionary → JSON string
        # because WebSocket text messages are strings.
        message = {
            "type" : "Speak",
            "text" : text,
        }

        await self.websocket.send(
            json.dumps(message)
        )


    
    async def receive_audio(self) -> bytes | None:
        """
        Wait for the next generated audio chunk.

        bytes = generated audio is available
        None  = provider event contains no audio
        """
        message = await self.websocket.recv()

        # If Deepgram sent bytes, this is actual generated PCM audio.
        # isinstance(object, type) checks an object's runtime type.
        if isinstance(message, bytes):
            return message

        # Otherwise this is a JSON control/metadata event.
        data = json.loads(message)

        # Temporarily print these events so we understand the
        # Flux TTS event lifecycle while integrating it.
        print("TTS event:", data)

        # No audio came from this particular event.
        return None



    async def flush(self):
        # Flush tells Deepgram:
        #
        # "This speaking turn is complete. Generate any audio
        # still waiting in your internal text buffer."
        #
        # We should NOT call this for every tiny Gemini chunk.
        message = {
            "type" : "Flush"
        }

        await self.websocket.send(
            json.dumps(message)
        )


    async def close(self):
        if self.websocket is not None:
            await self.websocket.close()

        self.websocket = None 