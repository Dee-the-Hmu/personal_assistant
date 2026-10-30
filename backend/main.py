from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from voice.stt.deepgram import DeepgramSTT
import asyncio
import time

#creates our web application
app = FastAPI(); 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#registers an endpoint
@app.get("/hello")
async def hello():
    return {"message" : "Hello from backend"}

# a WebSocket endpoint
"""
parameter WebSocket = the client's connection 

await websocket.accept() = accepts the connection 
await websocket.receive_test() = waits for the frontend data
await websocket.send_text() = sends data to frontend 

while True = keeps listening while the connection stays open 
"""
@app.websocket("/ws")
async def websocket_endpoint(websocket : WebSocket):
    await websocket.accept() # accepts the connection  from the browser/frontend 

    stt = DeepgramSTT()
    # Establish FastAPI → Deepgram WebSocket connection
    await stt.connect()  #connects with STT provider ()

    #do 2 pipelines at the Same Time (Concurrency)
    # 1) Browser -> audio -> STT provider
    # 2) STT provider -> transcript -> Browser 

    #1st pipeline
    async def send_audio_to_stt():
        try:
            while True:
                audio_chunk = await websocket.receive_bytes()

                await stt.send_audio(audio_chunk)
        except WebSocketDisconnect:
            print("Browser Disconnected")

    #2nd pipeline
    async def receive_transcripts():
        while True: 
            #okay to wait for STT to send transcript since this is a separate task 
            transcript = await stt.receive_transcript()

            if transcript is not None: 

                backend_received_time = time.perf_counter()
                print(
                    f"[BACKEND] Transcript received at: "
                    f"{backend_received_time:.3f}"
                )   
                await websocket.send_json({
                    "type": "transcript",
                    "text": transcript,
                    "backend_received_time": backend_received_time,
                })
             
                
                
                # await websocket.send_text(transcript) #sends text back thru the same browser websocket

    #asyncio.create_task() schedules Each coroutine to run Concurrently
    audio_task = asyncio.create_task(send_audio_to_stt())
    transcript_task = asyncio.create_task(receive_transcripts())

    #both task are registered with the Event Loop
    # cooperative async concurrency
    try:
        # gather() waits for both tasks 
        await asyncio.gather(
            audio_task,
            transcript_task
        )
    finally:
        # cancel() requests that these tasks stop if they are still running
        audio_task.cancel()
        transcript_task.cancel()

        await stt.close()
   