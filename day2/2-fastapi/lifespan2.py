from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize a variable and attach to app.state
    app.state.counter = {"value": 0}
    print("Application starting up... counter initialized to 0")
    yield
    # Shutdown: print final counter value (optional cleanup)
    print(f"Application shutting down... final counter value: {app.state.counter['value']}")

app = FastAPI(
    title="Log Analyzer VLLM Service",
    description="Log Analyzer VLLM Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

@app.get("/async")
async def func_async():
    # Read and increment the counter
    app.state.counter["value"] += 1
    return {"message": "Hello, World!", "counter": app.state.counter["value"]}

@app.get("/sync")
def func_sync():
    # Read and increment the counter (same shared state)
    app.state.counter["value"] += 1
    return {"message": "Hello, World!", "counter": app.state.counter["value"]}
