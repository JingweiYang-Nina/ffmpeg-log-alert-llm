from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Application starting up...")
    # You could initialize resources here (e.g., database connections, models)
    yield
    # Shutdown
    print("Application shutting down...")
    # Clean up resources here

app = FastAPI(
    title="Log Analyzer VLLM Service",
    description="Log Analyzer VLLM Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan  # <-- attach the lifespan
)

@app.get("/async")
async def func_async():
    return {"message": "Hello, World!"}

@app.get("/sync")
def func_sync():
    return {"message": "Hello, World!"}
