#!/bin/bash

# General purpose script for running commands on gakkenberry
# Usage: ./gakken.sh <command>
# Special commands:
#   kill-mpv: Kill all mpv processes
#   kill-python: Kill all python processes
#   play <file>: Play file with mpv
#   python <script> [args]: Run Python script with venv activated
#   cmd <command>: Run arbitrary command

# Path to the virtual environment on gakkenberry
VENV_PATH="~/gakken-venv/bin/activate"

if [ $# -eq 0 ]; then
    echo "Usage: $0 '<command>'"
    echo "Special commands:"
    echo "  kill-mpv: Kill all mpv processes"
    echo "  kill-python: Kill all python processes"
    echo "  play <file>: Play file with mpv"
    echo "  python <script> [args]: Run Python script with venv activated"
    echo "  cmd <command>: Run arbitrary command"
    exit 1
fi

case "$1" in
    "kill-mpv")
        ssh -t gakkenberry "pkill mpv"
        ;;
    "kill-python")
        ssh -t gakkenberry "pkill -9 -f python"
        ;;
    "play")
        if [ -z "$2" ]; then
            echo "Usage: $0 play <filename>"
            exit 1
        fi
        ssh -t gakkenberry "mpv '$2'"
        ;;
    "python")
        if [ -z "$2" ]; then
            echo "Usage: $0 python <script> [args]"
            exit 1
        fi
        shift  # Remove "python" from arguments
        ssh -t gakkenberry "source $VENV_PATH && python $@"
        ;;
    "cmd")
        shift
        ssh -t gakkenberry "$@"
        ;;
    *)
        ssh -t gakkenberry "$@"
        ;;
esac