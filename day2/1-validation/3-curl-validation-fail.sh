#!/bin/sh

curl http://127.0.0.1:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"ffmodel","messages":[{"role":"user","content":"Below are FFmpeg transcode log content that describe the result of the video transcoding. Analyze the log content and provide the transcoding status, PSNR value, any detected error message, and suggested resolution steps in json.ffmpeg -i input.mp4 -c:v copy -b:v 1G -c:a copy output_large_bitrate.mp4\nffmpeg version 4.4.2-0ubuntu0.22.04.1 Copyright (c) 2000-2021 FFmpeg developers\n[mp4 @ 0x...] Value 1000000000 for parameter 'video_bit_rate' is out of range [-2147483648 - 2147483647]\nCould not write header for output file 'output_large_bitrate.mp4': Invalid argument\nConversion failed!"}],"max_tokens":1024,"temperature":0}'

