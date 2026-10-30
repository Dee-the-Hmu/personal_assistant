from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

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
    await websocket.accept()

    try:
        while True: #websocket is a continuous stream
            audio_chunk = await websocket.receive_bytes() #wait until the client sends a blob
            print("Received audio bytes: ", len(audio_chunk))

    except WebSocketDisconnect: #when the client disconnects while await websocket.receive_bytes(), WebSocketDisconnect Exception is raised
        print("Voice WebSocket disconnected")

   