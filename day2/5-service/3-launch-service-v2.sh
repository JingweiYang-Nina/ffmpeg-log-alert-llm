#!/bin/sh

OMP_NUM_THREADS=4 uv run uvicorn service-v2:app --host 0.0.0.0 --port 8080 --reload
