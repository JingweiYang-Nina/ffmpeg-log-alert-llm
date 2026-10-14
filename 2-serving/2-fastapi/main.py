from fastapi import FastAPI

app = FastAPI(
        title="Log Analyzer VLLM Service", 
        description="Log Analyzer VLLM Service",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
        )

@app.get("/async")
async def func_async():
    return {"message": "Hello, World!"}

@app.get("/sync")
def func_sync():
    return {"message": "Hello, World!"}