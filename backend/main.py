from fastapi import FastAPI
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
