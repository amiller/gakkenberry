#!/bin/bash

# General purpose script for running commands on gakkenberry
# Usage: ./gakken.sh <command>
# Special commands:
#   kill-mpv: Kill all mpv processes
#   play <file>: Play file with timeout and auto-cleanup
#   cmd <command>: Run arbitrary command

if [ $# -eq 0 ]; then
    echo "Usage: $0 '<command>'"
    echo "Special commands:"
    echo "  kill-mpv: Kill all mpv processes"
    echo "  play <file>: Play file with 30s timeout"
    echo "  cmd <command>: Run arbitrary command"
    exit 1
fi

case "$1" in
    "kill-mpv")
        ssh gakkenberry "pkill mpv"
        ;;
    "play")
        if [ -z "$2" ]; then
            echo "Usage: $0 play <filename>"
            exit 1
        fi
        # Play with timeout and background cleanup
        ssh gakkenberry "timeout 30s mpv '$2' || true; pkill mpv 2>/dev/null || true" &
        SSH_PID=$!
        echo "Started playback (PID: $SSH_PID). Will auto-cleanup after 30s."
        echo "Run './gakken.sh kill-mpv' to stop early."
        ;;
    "cmd")
        shift
        ssh gakkenberry "$@"
        ;;
    *)
        ssh gakkenberry "$@"
        ;;
esac