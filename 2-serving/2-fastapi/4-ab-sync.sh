#!/bin/sh

ab -n 100000 -c 10000 http://127.0.0.1:8080/sync
