#!/usr/bin/env python3

import subprocess
import requests
import json

# Configuration
SERVICE_URL = "http://127.0.0.1:8080/analyze"  # Adjust if your service runs on different port/host
TIMEOUT = 240  # seconds for ffmpeg command (successful transcoding may take time)

def run_ffmpeg_and_get_stderr(cmd: str):
    """Run ffmpeg command as a string, return its stderr."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=TIMEOUT
    )
    # ffmpeg logs everything to stderr, so stderr is what we want
    return result.stderr

def send_to_analyze(log_text: str):
    """POST raw log text to /analyze endpoint and return parsed JSON."""
    response = requests.post(
        SERVICE_URL,
        data=log_text.encode("utf-8"),
        headers={"Content-Type": "text/plain"},
        timeout=60
    )
    response.raise_for_status()
    return response.json()

def main():
    # Two ffmpeg commands (use the ones from your previous code)
    cmd_success = (
        "ffmpeg -i ../3-ffmpeg/stylegan.mp4 -c:v libx264 -preset medium -crf 23 "
        "-c:a aac -movflags +faststart -y stylegan_output.mp4"
    )
    cmd_failure = (
        "ffmpeg -i ../3-ffmpeg/stylegan.mp4 -c:v fake_video_encoder -c:a aac stylegan_error.mp4"
    )

    print("=" * 70)
    print("Testing successful ffmpeg command")
    print("=" * 70)
    try:
        stderr_success = run_ffmpeg_and_get_stderr(cmd_success)
        print(f"Captured stderr length: {len(stderr_success)} characters")
        # Optionally print first few lines (very verbose)
        # print(stderr_success[:500])
        print("Sending to analyzer...")
        result = send_to_analyze(stderr_success)
        print("Analysis result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except subprocess.TimeoutExpired:
        print(f"FFmpeg command timed out after {TIMEOUT} seconds")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    print("\n" + "=" * 70)
    print("Testing failing ffmpeg command (invalid encoder)")
    print("=" * 70)
    try:
        stderr_failure = run_ffmpeg_and_get_stderr(cmd_failure)
        print(f"Captured stderr length: {len(stderr_failure)} characters")
        print("Sending to analyzer...")
        result = send_to_analyze(stderr_failure)
        print("Analysis result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except subprocess.TimeoutExpired:
        print("Command timed out (unlikely for failing command)")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
