from fastapi import FastAPI

#creates our web application
app = FastAPI(); 

#registers an endpoint
@app.get("/hello")
async def hello():
    return {"message" : "Hello from backend"}
