#!/bin/sh

uv run uvicorn lifespan2:app --host 0.0.0.0 --port 8080 --reload
