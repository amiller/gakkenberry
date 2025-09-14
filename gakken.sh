#!/bin/bash

# General purpose script for running commands on gakkenberry
# Usage: ./gakken.sh <command>
# Special commands:
#   kill-mpv: Kill all mpv processes
#   kill-python: Kill all python processes
#   play <file>: Play file with mpv
#   cmd <command>: Run arbitrary command

if [ $# -eq 0 ]; then
    echo "Usage: $0 '<command>'"
    echo "Special commands:"
    echo "  kill-mpv: Kill all mpv processes"
    echo "  kill-python: Kill all python processes"
    echo "  play <file>: Play file with mpv"
    echo "  cmd <command>: Run arbitrary command"
    exit 1
fi

case "$1" in
    "kill-mpv")
        ssh gakkenberry "pkill mpv"
        ;;
    "kill-python")
        ssh gakkenberry "pkill -9 -f python"
        ;;
    "play")
        if [ -z "$2" ]; then
            echo "Usage: $0 play <filename>"
            exit 1
        fi
        ssh gakkenberry "mpv '$2'"
        ;;
    "cmd")
        shift
        ssh gakkenberry "$@"
        ;;
    *)
        ssh gakkenberry "$@"
        ;;
esac