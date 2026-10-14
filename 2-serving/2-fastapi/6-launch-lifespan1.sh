#!/bin/sh

uv run uvicorn lifespan1:app --host 0.0.0.0 --port 8080 --reload
