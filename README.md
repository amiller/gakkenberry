# Gakken projector controller on raspberry pi

## Initial setup (Raspberry Pi)

The Raspberry Pi was set up with:
- RPi OS Lite
- Python virtual environment with system site packages: `~/gakken-venv`
- System packages: `mpv`, `python3-matplotlib`
- Python packages: `pygame`, `numpy`

The HDMI resolution is 1280x720. We run without X11, using direct framebuffer access.

## Setup (Control computer)

Add this to your ~/.ssh/config so the coding agent can reuse a session:

```
Host gakkenberry
    HostName gakkenberry.local
    User pi
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist yes
```

Download test files:
```bash
curl -o earth.gif https://upload.wikimedia.org/wikipedia/commons/7/7f/Rotating_earth_animated_transparent.gif
```

Copy files to gakkenberry:
```bash
scp earth.gif gakkenberry:~/
scp mpl-sdl-example.py gakkenberry:~/
scp sdl_direct.py gakkenberry:~/
```

### Remote control script

You can run commands directly via SSH:
```bash
ssh gakkenberry "mpv earth.gif"      # Direct SSH command execution
ssh gakkenberry "pkill mpv"          # Kill processes remotely
```

`gakken.sh` is a utility wrapper that makes coding agents more comfortable with remote execution:

```bash
./gakken.sh "mpv earth.gif"           # Run arbitrary commands
./gakken.sh kill-mpv                  # Kill all mpv processes
./gakken.sh kill-python               # Kill all python processes
./gakken.sh play earth.gif            # Play file with mpv
./gakken.sh cmd "ls -la"              # Explicit command mode
```

## Getting started

### Play videos/images with mpv

```bash
./gakken.sh play earth.gif
```

### Matplotlib visualization

For scientific visualization with matplotlib, use the "Agg" backend:

```python
import matplotlib
matplotlib.use("Agg")
```

Run matplotlib SDL example:
```bash
./gakken.sh "source ~/gakken-venv/bin/activate && python mpl-sdl-example.py"
```

### Direct pygame drawing (fastest)

Run direct pygame drawing example:
```bash
./gakken.sh "source ~/gakken-venv/bin/activate && python sdl_direct.py"
```

This is much faster than matplotlib since it does direct drawing without buffer conversions.