#!/bin/sh

ffmpeg -i stylegan.mp4 -c:v libx264 -preset medium -crf 23 -c:a aac -movflags +faststart -y stylegan_output.mp4
