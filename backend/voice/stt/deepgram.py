import os 
import websockets
import json

from dotenv import load_dotenv
#python-dotenv → loads environment variables from a .env file

from .base import STTProvider

# read variables from the local .env file and adds them 
load_dotenv()

class DeepgramSTT(STTProvider):

    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        self.websocket = None #no connection exists yet

    async def connect(self):
        url = (
            "wss://api.deepgram.com/v2/listen"
            "?model=flux-general-en"
            "&encoding=linear16"
            "&sample_rate=16000"
        )

        #add api_key as the additional_header (HTTP headers )
        self.websocket = await websockets.connect(
            url, 
            additional_headers={
                "Authorization" : f"Token {self.api_key}"
            }
        )

    async def send_audio(self, audio: bytes):
        await self.websocket.send(audio)

    async def receive_transcript(self) -> str | None:
        # recv waits until Deepgram sends us the next WebSocket Message
        message = await self.websocket.recv() 

        # Deepgram sends its events as JSON text, json.load() converts the JSON -> Python dict 
        data = json.loads(message) 

        #Deepgram Flux sends multiple event types 
        if data.get("type") != "TurnInfo":
            return None

        # For now, only return a transcript when the turn is complete.
        if data.get("event") != "EndOfTurn":  # "EndOfTurn" = Flux believes the user has finished speaking, "Update" = the user's turn is still developing.
            return None

        # .get() = safely read the transcript, "" if the field doesn't exist
        transcript = data.get("transcript", "")

        # ignore an EndOfTurn event if it somehow contains no transcript
        if not transcript: 
            return None

        # print("Deepgram event: ", data)
        return transcript

        
       

    async def close(self):
        if self.websocket is not None: # if created successfully
            await self.websocket.close()

            self.websocket = None 
        


"""
example 
Deepgram event:  {'type': 'TurnInfo', 
'request_id': '01a18e4e-cfcd-7a83-92db-8e630c4a3e9a', 
'event': 'Update', 
'turn_index': 1, 
'audio_window_start': 4.0, 
'audio_window_end': 8.56, 
'transcript': '', 
'words': [], 
'end_of_turn_confidence': 0.0017, 
'sequence_id': 36}
"""