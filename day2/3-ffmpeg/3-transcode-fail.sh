#!/bin/sh

ffmpeg -i stylegan.mp4 -c:v fake_video_encoder -c:a aac stylegan_error.mp4
