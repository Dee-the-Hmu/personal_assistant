from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from voice.stt.deepgram import DeepgramSTT
import asyncio

from agents.assistant import stream_assistant

import uuid

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

    # uuid4() generates a practically unique identifier.
    # str() converts the UUID object into a normal string.
    #
    # One WebSocket voice session = one conversation thread for now.
    thread_id = str(uuid.uuid4())

    stt = DeepgramSTT()
    # Establish FastAPI → Deepgram WebSocket connection
    await stt.connect()  #connects with STT provider ()

    transcript_queue = asyncio.Queue() #an async-safe FIFO queue 

    #do 2 pipelines at the Same Time (Concurrency)
    # 1) Browser -> audio -> STT provider
    # 2) STT provider -> transcript -> transcript_queue
    # 3) transcript_queue -> LangGraph/Gemini -> Browser 

    #1st pipeline
    async def send_audio_to_stt():
        try:
            while True:
                # Receive PCM16 audio:
                # Browser → FastAPI
                # audio_chunk = await websocket.receive_bytes()

                # Forward the same audio:
                # FastAPI → Deepgram
                # await stt.send_audio(audio_chunk)

                # receive() gives us the full WebSocket event.
                message = await websocket.receive()

                if message["type"] == "websocket.disconnect":
                    print("Browser Disconnected")
                    break

                # Browser audio is sent as binary WebSocket data
                audio_chunk = message.get("bytes")

                if audio_chunk is not None:
                    await stt.send_audio(audio_chunk)

        except WebSocketDisconnect:
            print("Browser Disconnected")

    #2nd pipeline
    async def receive_transcripts():
        while True: 
            #okay to wait for STT to send transcript since this is a separate task 
            transcript = await stt.receive_transcript()

            # None means Deepgram sent an event that wasn't a completed user transcript.
            if transcript is None:
                continue

            # Send the completed transcript to transcript_queue
            if transcript is not None: 

                await transcript_queue.put(transcript)

    #3rd pipeline (agent reads from the transcript_queue)
    async def process_transcripts():
        while True: 
            # get() waits until the queue contains something
            transcript = await transcript_queue.get()   # While it's waiting, it does NOT block the other tasks.

            try: 
                print("User:", transcript)

                async for text_chunk in stream_assistant(
                    transcript,
                    thread_id,
                ):
                    print("Assistant chunk: ", text_chunk)

                    #send each chunk to React immediately
                    await websocket.send_json({
                        "type": "assistant_chunk",
                        "text": text_chunk,
                    })

                #tell the frontend that this assistant response is complete
                await websocket.send_json({
                    "type": "assistant_done"
                })
            finally: 
                transcript_queue.task_done()

                '''
                # This can take several seconds.
                # okay because Deepgram is being read
                response = await stream_assistant(
                    transcript, 
                    thread_id,
                )
                print("Assistant: ", response)
                print()

                #send structured JSON instead of plain text 
                await websocket.send_json({
                    "type": "assistant_response",
                    "transcript": transcript,
                    "text": response,
                })
                '''
            

                

    # Run audio sending and transcript/agent processing concurrently.
    #asyncio.create_task() schedules Each coroutine to run Concurrently
    audio_task = asyncio.create_task(send_audio_to_stt())
    transcript_task = asyncio.create_task(receive_transcripts())
    agent_task = asyncio.create_task(process_transcripts())


    # cooperative async concurrency
    try:
        # gather() waits for  all the tasks (All concurrent tasks run)
        await asyncio.gather(
            audio_task,
            transcript_task,
            agent_task
        )
    finally:
        # cancel() requests that these tasks stop if they are still running
        audio_task.cancel()
        transcript_task.cancel()
        agent_task.cancel()

        await stt.close()
   